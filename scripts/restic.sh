#!/bin/usr

# Shamelessly stolen from https://github.com/itzg/docker-mc-backup/blob/master/scripts/opt/backup-loop.sh
# Lightly modified by me, mostly copied. I appreciate your work, Geoff <3.

: "${SRC_DIR:=/data}"
: "${DEST_DIR:=/backups}"
: "${RESTIC_HOSTNAME:=$(hostname)}"
: "${PRUNE_BACKUPS_DAYS:=7}"
: "${PRUNE_RESTIC_RETENTION:=--keep-within ${PRUNE_BACKUP_DAYS:-7}d}"


is_elem_in_array() {
  # $1 = element
  # All remaining arguments are array to search for the element in
  if [ "$#" -lt 2 ]; then
    log INTERNALERROR "Wrong number of arguments passed to is_elem_in_array function"
    return 2
  fi
  local element="${1}"
  shift
  local e
  for e; do
    if [ "${element}" == "${e}" ]; then
      return 0
    fi
  done
  return 1
}

log() {
  if [ "$#" -lt 1 ]; then
    log INTERNALERROR "Wrong number of arguments passed to log function"
    return 2
  fi
  local level="${1}"
  shift
  local valid_levels=(
    "INFO"
    "WARN"
    "ERROR"
    "INTERNALERROR"
  )
  if ! is_elem_in_array "${level}" "${valid_levels[@]}"; then
    log INTERNALERROR "Log level ${level} is not a valid level."
    return 2
  fi
  (
    # If any arguments are passed besides log level
    if [ "$#" -ge 1 ]; then
      # then use them as log message(s)
      <<<"${*}" cat -
    else
      # otherwise read log messages from standard input
      cat -
    fi
    if [ "${level}" == "INTERNALERROR" ]; then
      echo "Please report this: https://github.com/itzg/docker-mc-backup/issues"
    fi
  ) | awk -v level="${level}" '{ printf("%s %s %s\n", strftime("%FT%T%z"), level, $0); fflush(); }'
} >&2

_delete_old_backups() {
  # shellcheck disable=SC2086
  command restic forget --tag "${restic_tags_filter}" ${PRUNE_RESTIC_RETENTION} "${@}"
}

_check() {
    if ! output="$(command restic check 2>&1)"; then
      log ERROR "Repository contains error! Aborting"
      <<<"${output}" log ERROR
      return 1
    fi
}

init() {
  if [ -z "${RESTIC_PASSWORD:-}" ] \
      && [ -z "${RESTIC_PASSWORD_FILE:-}" ] \
      && [ -z "${RESTIC_PASSWORD_COMMAND:-}" ]; then
    log ERROR "At least one of" RESTIC_PASSWORD{,_FILE,_COMMAND} "needs to be set!"
    return 1
  fi
  if [ -z "${RESTIC_REPOSITORY:-}" ]; then
    log ERROR "RESTIC_REPOSITORY is not set!"
    return 1
  fi
  if output="$(command restic snapshots 2>&1 >/dev/null)"; then
    log INFO "Repository already initialized"
    _check
  elif <<<"${output}" grep -q '^Is there a repository at the following location?$'; then
    log INFO "Initializing new restic repository..."
    command restic init | log INFO
  elif <<<"${output}" grep -q 'wrong password'; then
    <<<"${output}" log ERROR
    log ERROR "Wrong password provided to an existing repository?"
    return 1
  else
    <<<"${output}" log ERROR
    log INTERNALERROR "Unhandled restic repository state."
    return 2
  fi

  # Used to construct tagging arguments and filters for snapshots
  read -ra restic_tags <<< ${RESTIC_ADDITIONAL_TAGS}
  restic_tags+=("${BACKUP_NAME}")
  readonly restic_tags

  # Arguments to use to tag the snapshots with
  restic_tags_arguments=()
  local tag
  for tag in "${restic_tags[@]}"; do
      restic_tags_arguments+=( --tag "$tag")
  done
  readonly restic_tags_arguments
  # Used for filtering backups to only match ours
  restic_tags_filter="$(IFS=,; echo "${restic_tags[*]}")"
  readonly restic_tags_filter
}

backup() {
  init
  log INFO "Backing up content in ${SRC_DIR} as host ${RESTIC_HOSTNAME}"
  command restic backup --host "${RESTIC_HOSTNAME}" "${restic_tags_arguments[@]}" "${excludes[@]}" "${SRC_DIR}" | log INFO
}

restore() {
  log INFO "Restoring backup id '${BACKUP_TARGET_ID}' to '${BACKUP_DEST_PATH}'"
  command restic restore "${BACKUP_TARGET_ID}" --target "${BACKUP_DEST_PATH}" | log INFO
}

prune() {
  # We cannot use `grep -q` here - see https://github.com/restic/restic/issues/1466
  if _delete_old_backups --dry-run | grep '^remove [[:digit:]]* snapshots:$' >/dev/null; then
    log INFO "Pruning snapshots using ${PRUNE_RESTIC_RETENTION}"
    _delete_old_backups --prune | log INFO
    _check | log INFO
  fi
}

$1