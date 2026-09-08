#!/bin/sh
# Container entrypoint: prepare a writable HOME for CLI config, bootstrap
# the self-signed TLS certificate (mirrors scripts/install_service.sh), then
# exec the server command.
set -eu

cd /app

# HOME sits on the data volume so runtime state survives container
# recreation. The OCI runtime sets HOME=/ for numeric users without a passwd
# entry, so treat that as unset too.
case "${HOME:-}" in
    ""|"/") export HOME=/app/data/home ;;
esac
mkdir -p "$HOME" data

tls_port="${REPORTS_TLS_PORT:-8443}"
tls_cert="${REPORTS_TLS_CERT:-data/tls/service.crt}"
tls_key="${REPORTS_TLS_KEY:-data/tls/service.key}"
if [ -n "$tls_port" ] && command -v openssl >/dev/null 2>&1 && [ ! -f "$tls_cert" ]; then
    mkdir -p data/tls
    san="DNS:localhost,IP:127.0.0.1"
    for item in $(printf '%s' "${REPORTS_TLS_SAN:-}" | tr ',' ' '); do
        case "$item" in
            IP:*|DNS:*) san="$san,$item" ;;
            '')
                ;;
            *)
                # Bare values get a type prefix: IPv4-looking ones as IP, rest as DNS.
                case "$item" in
                    *[!0-9.]*) san="$san,DNS:$item" ;;
                    *) san="$san,IP:$item" ;;
                esac
                ;;
        esac
    done
    if ! openssl req -x509 -newkey rsa:2048 -sha256 -days 3650 -nodes \
        -keyout "$tls_key" -out "$tls_cert" \
        -subj "/CN=weeklyreports" -addext "subjectAltName=$san" >/dev/null 2>&1; then
        openssl req -x509 -newkey rsa:2048 -sha256 -days 3650 -nodes \
            -keyout "$tls_key" -out "$tls_cert" -subj "/CN=weeklyreports" >/dev/null 2>&1
    fi
fi

exec "$@"
