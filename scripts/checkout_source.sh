#!/usr/bin/env bash
# Shared pinned checkout. Callers set PROJECT_ROOT and enable set -euo pipefail.
checkout() {
  local name="$1" url="$2" revision="$3"
  local dest="$PROJECT_ROOT/.vendor/$name" head
  if [[ ! -e "$dest" ]]; then
    git init -q "$dest"
    git -C "$dest" remote add origin "$url"
  fi
  [[ -d "$dest/.git" ]] || { echo "Not a Git checkout: $dest" >&2; return 1; }
  if head="$(git -C "$dest" rev-parse --verify HEAD 2>/dev/null)"; then
    [[ "$head" == "$revision" ]] || { echo "Wrong revision in $dest" >&2; return 1; }
    [[ -z "$(git -C "$dest" status --porcelain --untracked-files=no)" ]] || { echo "Modified source in $dest" >&2; return 1; }
  else
    # A failed fetch leaves an unborn repository. Retry only if it is empty.
    [[ -z "$(git -C "$dest" status --porcelain --untracked-files=all)" ]] || { echo "Modified incomplete source in $dest" >&2; return 1; }
    if ! git -C "$dest" remote get-url origin >/dev/null 2>&1; then
      git -C "$dest" remote add origin "$url"
    fi
    [[ "$(git -C "$dest" remote get-url origin)" == "$url" ]] || { echo "Unexpected source URL in $dest" >&2; return 1; }
    git -C "$dest" fetch --depth 1 origin "$revision" || return 1
    git -C "$dest" checkout --detach "$revision" || return 1
  fi
}
