#!/bin/sh
# DV-HUNG-07: render the staging IP allowlist from STAGING_ALLOWED_CIDRS.
#
# The allowlist used to be hard-coded in nginx-staging-ui.conf while the compose
# overlay required a STAGING_ALLOWED_CIDRS variable that nothing ever read. An
# operator could therefore set the approved reviewer network, see the stack come
# up, and still be serving the default private ranges. This script makes the
# variable authoritative: it is the only thing that decides who reaches the UI.
#
# Used as the proxy entrypoint, it hands over to the stock nginx entrypoint so
# the official image behaviour (template processing, signal handling) is kept.
#
#   STAGING_ALLOWED_CIDRS="203.0.113.0/24 198.51.100.7/32"

set -eu

: "${STAGING_ALLOWED_CIDRS:?STAGING_ALLOWED_CIDRS must list the approved reviewer networks}"

OUTPUT=/etc/nginx/allowlist.conf
: > "$OUTPUT"

# Unquoted on purpose: the variable is a space-separated CIDR list.
for cidr in $STAGING_ALLOWED_CIDRS; do
    printf 'allow %s;\n' "$cidr" >> "$OUTPUT"
done

# Fail closed. An empty allowlist behind `deny all` would lock every reviewer
# out, and a whitespace-only value must not be mistaken for a valid list.
if [ ! -s "$OUTPUT" ]; then
    echo "STAGING_ALLOWED_CIDRS produced an empty allowlist; refusing to start." >&2
    exit 1
fi

echo "Staging UI allowlist rendered to $OUTPUT:"
sed 's/^/  /' "$OUTPUT"

exec /docker-entrypoint.sh "$@"
