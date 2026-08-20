#!/usr/bin/env bash
# DV-HUNG-07: create reviewer credentials for the staging UI proxy.
#
#   bash deployment/staging/generate_htpasswd.sh reviewer
#
# Writes deployment/staging/htpasswd, which the proxy mounts read-only.
# The generated file is git-ignored: credentials must never be committed.

set -euo pipefail

USERNAME="${1:-}"
if [[ -z "$USERNAME" ]]; then
    echo "Usage: $0 <username>" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT="$SCRIPT_DIR/htpasswd"

# A generated password is used rather than a prompt so that no reviewer picks a
# reused or guessable one, and so the value appears exactly once, here.
PASSWORD="$(openssl rand -base64 18)"

# apache2-utils is not assumed to be installed on the deployment host.
docker run --rm httpd:2.4-alpine \
    htpasswd -nbB "$USERNAME" "$PASSWORD" > "$OUTPUT"

chmod 600 "$OUTPUT"

cat <<EOF

Staging reviewer credentials created.

  File:     $OUTPUT
  Username: $USERNAME
  Password: $PASSWORD

Store the password in the team secret manager and share it over a private
channel. It is not recoverable from the htpasswd file.

Remaining steps before sharing the staging URL:
  1. Set STAGING_ALLOWED_CIDRS to the approved reviewer networks, then confirm
     the allowlist the proxy printed at start-up.
  2. Terminate TLS in front of the proxy.
  3. Verify that port 8501 is NOT reachable from outside the host.
EOF
