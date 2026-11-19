#!/usr/bin/env bash
# Vendor pstack skills into real directories.
#
# This repository keeps the Cursor pstack skills as symlinks pointing at
# ~/.cursor/plugins/cache/cursor-public/pstack/<content-hash>/skills/<name>.
# The hash changes whenever the plugin updates, and the cache exists only on the
# machine running Cursor, so those symlinks dangle everywhere else — including
# the VM where bobbin reads skills/<name> for every vhome.
#
# This script replaces each tracked symlink with a real copy of the current
# cache content, so a plain `git clone` works on any machine. Run it on the
# machine that has the cache, then commit and push; the VM only needs
# `git pull`. Machines that want the newest Cursor versions before vendoring can
# run `scripts/sync.py --apply --prefer-live` (Mac-side overlay).
#
# Usage:
#   scripts/vendor-pstack.sh                     # dry run: report what it would copy
#   scripts/vendor-pstack.sh --apply             # replace the tracked symlinks with copies
#   scripts/vendor-pstack.sh --apply --all       # also vendor untracked symlinks on disk
#   scripts/vendor-pstack.sh --apply --name bro  # vendor one skill (repeatable)
#
# Environment:
#   PSTACK_CACHE_ROOT  override the cache root (default ~/.cursor/plugins/cache/cursor-public/pstack)
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
skills_dir="$repo_root/skills"
cache_root="${PSTACK_CACHE_ROOT:-$HOME/.cursor/plugins/cache/cursor-public/pstack}"

apply=0
all_entries=0
only_names=()

while [ $# -gt 0 ]; do
  case "$1" in
    --apply) apply=1 ;;
    --all) all_entries=1 ;;
    --name)
      shift
      [ $# -gt 0 ] || { echo "ERROR: --name requires a value" >&2; exit 2; }
      only_names+=("$1")
      ;;
    -h|--help) sed -n '2,24p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "ERROR: unknown argument: $1" >&2; exit 2 ;;
  esac
  shift
done

if [ ! -d "$skills_dir" ]; then
  echo "ERROR: $skills_dir not found" >&2
  exit 1
fi
if [ ! -d "$cache_root" ]; then
  echo "ERROR: pstack cache not found: $cache_root" >&2
  echo "       Run this on the machine that has the Cursor plugin cache." >&2
  exit 1
fi

# The cache is content-addressed, so several versions can be present. Use the
# newest one: that is what Cursor currently loads.
cache_dir=""
cache_mtime=0
for dir in "$cache_root"/*/; do
  [ -d "$dir/skills" ] || continue
  mtime=$(stat -c %Y "$dir" 2>/dev/null || stat -f %m "$dir")
  if [ "$mtime" -ge "$cache_mtime" ]; then
    cache_mtime=$mtime
    cache_dir="${dir%/}"
  fi
done
if [ -z "$cache_dir" ]; then
  echo "ERROR: no <hash>/skills directory under $cache_root" >&2
  exit 1
fi
echo "cache: $cache_dir"

# Which entries to consider. By default only the symlinks git tracks: an
# untracked symlink is local clutter, and vendoring it would add a skill to the
# repository as a side effect of a sync. --all widens the scan to every symlink
# on disk. Built with a while-read loop rather than mapfile so this runs on
# macOS's bash 3.2 as well.
candidates=()
if [ "$all_entries" -eq 1 ]; then
  source_cmd=(find "$skills_dir" -mindepth 1 -maxdepth 1 -type l)
else
  source_cmd=(git -C "$repo_root" ls-files -s skills)
fi
while IFS= read -r line; do
  if [ "$all_entries" -eq 1 ]; then
    candidates+=("$line")
  else
    # ls-files -s: "<mode> <sha> <stage>\t<path>"; keep symlinks (120000).
    case "$line" in
      120000\ *) candidates+=("$repo_root/${line#*	}") ;;
    esac
  fi
done < <("${source_cmd[@]}" | sort)

vendored=0
skipped_real=0
missing=0
wanted() {
  [ ${#only_names[@]} -eq 0 ] && return 0
  local n
  for n in "${only_names[@]}"; do [ "$n" = "$1" ] && return 0; done
  return 1
}

for entry in "${candidates[@]}"; do
  name=$(basename "$entry")
  if [ -d "$entry" ] && [ ! -L "$entry" ]; then
    skipped_real=$((skipped_real + 1))
    continue
  fi
  wanted "$name" || continue
  if [ ! -f "$cache_dir/skills/$name/SKILL.md" ]; then
    echo "  MISSING in cache, left as is: $name -> $(readlink "$entry" 2>/dev/null || echo '(not a symlink)')"
    missing=$((missing + 1))
    continue
  fi
  if [ "$apply" -eq 0 ]; then
    echo "  WOULD vendor: $name"
  else
    rm "$entry"
    cp -R "$cache_dir/skills/$name" "$entry"
    find "$entry" -name '._*' -delete 2>/dev/null || true
    echo "  vendored: $name"
  fi
  vendored=$((vendored + 1))
done

# Informational: cache skills this repo does not track. Not vendored — adding a
# skill to the repository is a deliberate choice, not a side effect of syncing.
new_in_cache=()
for dir in "$cache_dir"/skills/*/; do
  [ -f "$dir/SKILL.md" ] || continue
  name=$(basename "$dir")
  # -L as well as -e: a dangling symlink still occupies the slot.
  if [ ! -e "$skills_dir/$name" ] && [ ! -L "$skills_dir/$name" ]; then
    new_in_cache+=("$name")
  fi
done

echo
echo "vendored: $vendored, already real directories: $skipped_real, missing in cache: $missing"
if [ ${#new_in_cache[@]} -gt 0 ]; then
  echo "in cache but not in this repo (add manually if wanted): ${new_in_cache[*]}"
fi
if [ "$apply" -eq 0 ]; then
  echo
  echo "dry run: re-run with --apply to write the copies."
else
  echo
  echo "next: git add -A skills && git commit -m 'chore: vendor pstack skills as real directories' && git push"
fi
