# Manage cross-process Docker network slot reservations.

harbor_uses_docker_env() {
  # Harbor's default --env is docker. Skip IPAM only when the user passed a
  # different backend (daytona, e2b, apple-container, …). There is no host-local
  # environment in Harbor 0.20 — local Linux trials still need Docker.
  local i val
  for ((i = 0; i < ${#HARBOR_ARGS[@]}; i++)); do
    case "${HARBOR_ARGS[$i]}" in
      -e|--env)
        val="${HARBOR_ARGS[$((i + 1))]:-docker}"
        [[ "$val" == "docker" ]]
        return
        ;;
      --env=*)
        [[ "${HARBOR_ARGS[$i]#--env=}" == "docker" ]]
        return
        ;;
      -e=*)
        [[ "${HARBOR_ARGS[$i]#-e=}" == "docker" ]]
        return
        ;;
    esac
  done
  return 0
}

harbor_uses_per_trial_networks() {
  # True when each Harbor trial still allocates a user-defined Docker network.
  # The task-template compose overlay uses network_mode: bridge (docker0), so
  # local docker jobs no longer consume IPAM slots. Cloud --env is not docker.
  harbor_uses_docker_env || return 1
  local compose="${SCRIPT_DIR}/task-template/environment/docker-compose.yaml"
  if [[ -f "$compose" ]] && grep -Eq '^[[:space:]]*network_mode:[[:space:]]*bridge[[:space:]]*$' "$compose"; then
    return 1
  fi
  return 0
}

release_docker_slots() {
  # Drop this shell's named Harbor IPAM reservation.
  if [[ -n "${_docker_slot_holder}" ]]; then
    python3 "$DOCKER_NETWORKS" release --holder "$_docker_slot_holder" || true
    _docker_slot_holder=""
  fi
}

on_eval_shell_exit() {
  # EXIT trap: drop the named holder, then any leaked holders for this shell.
  release_docker_slots
  python3 "$DOCKER_NETWORKS" release --pid "${BASHPID:-$$}" || true
  reclaim_docker_leftovers
}

reclaim_docker_leftovers() {
  # Free leftover Harbor containers (including failed compose down), IPAM,
  # and unused image tags. Keep BuildKit cache so the next job reuses layers.
  python3 "$DOCKER_NETWORKS" prune --keep-builder-cache >/dev/null || true
}

default_n_concurrent() {
  # Fallback Harbor -n when neither -n nor -k is available (CLI helper).
  python3 "$DOCKER_NETWORKS" default-n
}

acquire_docker_slots() {
  # Reserve *slots* trial networks for *holder* in the *current* shell.
  # Do not wrap this function in $() — that subshell would lose the holder
  # and leak the reservation until the wrapper process exits.
  # Pass ignore-ipam as $4 when trials use docker0 (no per-trial networks).
  local holder="$1"
  local slots="$2"
  local -n _granted_out="${3:-_docker_slots_granted}"
  local ignore_ipam="${4:-}"
  local -a acquire_args=(acquire --slots "$slots" --holder "$holder" --pid "${BASHPID:-$$}")
  if [[ "$ignore_ipam" == "ignore-ipam" ]]; then
    acquire_args+=(--ignore-ipam)
    echo "Reserving up to $slots coding-trial slot(s) for $holder (default bridge; IPAM not used)." >&2
  else
    echo "Reserving up to $slots Docker network slot(s) for $holder (blocks if IPAM is full)." >&2
  fi
  if [[ -n "${_docker_slot_holder}" && "${_docker_slot_holder}" != "$holder" ]]; then
    echo "Releasing leftover Docker slot holder $_docker_slot_holder before $holder" >&2
    python3 "$DOCKER_NETWORKS" release --holder "$_docker_slot_holder" || true
    _docker_slot_holder=""
  fi
  _docker_slot_holder="$holder"
  _granted_out="$(python3 "$DOCKER_NETWORKS" "${acquire_args[@]}")"
}

set_harbor_n_concurrent() {
  # Rewrite -n / --n-concurrent in the nameref array, or append -n.
  local -n _n_args="$1"
  local n="$2"
  local i found=0
  for ((i = 0; i < ${#_n_args[@]}; i++)); do
    if [[ "${_n_args[$i]}" == "-n" || "${_n_args[$i]}" == "--n-concurrent" ]]; then
      _n_args[$((i + 1))]="$n"
      found=1
    fi
  done
  if [[ "$found" -eq 0 ]]; then
    _n_args+=(-n "$n")
  fi
}

append_harbor_quiet() {
  # Add Harbor --quiet unless the caller already passed -q/--quiet/--silent.
  local -n _q_args="$1"
  local i
  for ((i = 0; i < ${#_q_args[@]}; i++)); do
    case "${_q_args[$i]}" in
      -q|--quiet|--silent) return 0 ;;
    esac
  done
  _q_args+=(--quiet)
}
