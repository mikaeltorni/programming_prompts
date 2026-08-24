# Manage cross-process Docker network slot reservations.

release_docker_slots() {
  # Drop this process's Harbor IPAM reservation. EXIT trap calls this so a
  # killed Harbor job does not leak slots to the next terminal.
  if [[ -n "${_docker_slot_holder}" ]]; then
    python3 "$DOCKER_NETWORKS" release --holder "$_docker_slot_holder" || true
    _docker_slot_holder=""
  fi
}

acquire_docker_slots() {
  # Reserve *slots* trial networks for *holder* (blocks until IPAM has room).
  local holder="$1"
  local slots="$2"
  local granted
  echo "Reserving up to $slots Docker network slot(s) for $holder (blocks if IPAM is full)." >&2
  granted="$(python3 "$DOCKER_NETWORKS" acquire --slots "$slots" --holder "$holder" --pid "$$")"
  _docker_slot_holder="$holder"
  printf '%s\n' "$granted"
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
