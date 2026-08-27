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

strip_user_harbor_n_concurrent() {
  # Drop user -n / --n-concurrent from the nameref array. Harbor concurrency
  # always follows -k: 5 tasks × -k 20 with -n 100 starts 100 simultaneous
  # `docker compose build`s and Harbor aborts them with Environment start
  # timed out after 300s. The same -k 20 with n=k scored every trial.
  local -n _n_args="$1"
  local i
  local -a kept=() ignored=()
  for ((i = 0; i < ${#_n_args[@]}; i++)); do
    case "${_n_args[$i]}" in
      -n|--n-concurrent)
        ignored+=("${_n_args[$((i + 1))]:-}")
        i=$((i + 1))
        ;;
      --n-concurrent=*)
        ignored+=("${_n_args[$i]#--n-concurrent=}")
        ;;
      *)
        kept+=("${_n_args[$i]}")
        ;;
    esac
  done
  _n_args=("${kept[@]}")
  if [[ ${#ignored[@]} -gt 0 ]]; then
    echo "Ignoring Harbor -n/--n-concurrent ${ignored[*]}: concurrent trials always follow -k (n>k starves docker compose build; Harbor then hits Environment start timed out after 300s)." >&2
  fi
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
