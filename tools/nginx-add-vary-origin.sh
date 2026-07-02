#!/bin/bash
# nginx-add-vary-origin.sh
#
# Ensure every nginx vhost that reflects the request Origin into
# Access-Control-Allow-Origin also sends "Vary: Origin". Without it a shared
# cache (browser, CDN, or nginx proxy_cache) can hand one origin's CORS header
# to a different origin.
#
# What it does:
#   - scans enabled vhosts (resolved /etc/nginx/sites-enabled/*) + /etc/nginx/conf.d/*.conf
#   - inserts `add_header Vary Origin always;` right after every reflected
#     Access-Control-Allow-Origin line, matching indentation
#   - skips static `Access-Control-Allow-Origin *` (a constant value needs no Vary)
#   - idempotent (won't add a second time), purely additive (only inserts lines)
#   - backs up changed files, runs `nginx -t`, reloads only on success,
#     and rolls back automatically if the test fails
#
# nginx note: add_header directives are inherited from an outer level ONLY IF
# the current level has no add_header of its own (an `if` block is its own
# level). So Vary is placed next to the ACAO at the same level. For `if`-based
# CORS, Vary is therefore only emitted when the origin matches; that's safe (a
# no-ACAO response served cross-origin just fails the CORS check). For fully
# airtight caching, use the `map`-based CORS pattern with a single
# location-level `add_header Access-Control-Allow-Origin $mapvar always;`.
#
# Run as root:  sudo bash nginx-add-vary-origin.sh
set -euo pipefail
export LC_ALL=C

ts="$(date +%Y%m%d-%H%M%S)"
bakdir="/etc/nginx/vary-origin-backup-$ts"
mkdir -p "$bakdir"

mapfile -t candidates < <(
  { for l in /etc/nginx/sites-enabled/*; do [ -e "$l" ] && readlink -f "$l"; done
    for c in /etc/nginx/conf.d/*.conf; do [ -e "$c" ] && echo "$c"; done
  } | sort -u
)

bakname() { echo "$bakdir/$(echo "$1" | sed 's#/#_#g')"; }

changed=()
for f in "${candidates[@]}"; do
  grep -qE '^[[:space:]]*add_header[[:space:]]+"?Access-Control-Allow-Origin' "$f" || continue

  bak="$(bakname "$f")"
  cp -a "$f" "$bak"

  perl -0777 -i -pe \
    's/^([ \t]*)(add_header[ \t]+"?Access-Control-Allow-Origin"?(?![^\n]*\*)[^\n]*\n)(?![ \t]*add_header[ \t]+Vary[ \t]+Origin\b)/$1$2${1}add_header Vary Origin always;\n/mg' \
    "$f"

  if cmp -s "$f" "$bak"; then
    rm -f "$bak"
  else
    changed+=("$f")
  fi
done

echo "Backups (only for changed files): $bakdir"
echo "Changed files: ${changed[*]:-<none>}"
echo "----- diff preview -----"
for f in "${changed[@]:-}"; do
  [ -n "$f" ] || continue
  echo "===== $f ====="
  diff -u "$(bakname "$f")" "$f" || true
done

if [ "${#changed[@]}" -eq 0 ]; then
  echo "Nothing to change (already fixed). Removing empty backup dir."
  rmdir "$bakdir" 2>/dev/null || true
  exit 0
fi

echo "----- nginx -t -----"
if nginx -t; then
  systemctl reload nginx
  echo "OK: nginx configuration valid and reloaded."
else
  echo "nginx -t FAILED -- rolling back changes."
  for f in "${changed[@]}"; do cp -a "$(bakname "$f")" "$f"; done
  echo "Rolled back. nginx NOT reloaded."
  exit 1
fi
