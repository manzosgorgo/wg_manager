#!/usr/bin/env bash
#===============================================================================
#
#          FILE: generate_CA.sh
#
#         USAGE: ./generate_CA.sh <name> <profile>
#
#   DESCRIPTION:
#       Generates a private key, CSR and X.509 certificate signed by the
#       local CA.
#
#       Required files:
#           ../ca.crt
#           ../ca.key
#           <name>.cnf
#           tools/pki/profiles/<profile>.cnf
#
#       Profiles:
#           server
#           client
#           server-client
#
#       Generated files:
#           <name>.key
#           <name>.csr
#           <name>.crt
#
#===============================================================================
set -Eeuo pipefail

umask 077

SCRIPT_NAME="$(basename "$0")"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

#-------------------------------------------------------------------------------
# Configuration
#-------------------------------------------------------------------------------

KEY_BITS=2048
CERT_DAYS=825
HASH_ALGORITHM="sha256"

CA_CERT="../ca.crt"
CA_KEY="../ca.key"

#-------------------------------------------------------------------------------
# Functions
#-------------------------------------------------------------------------------

usage() {
    cat <<EOF
Usage:
    $SCRIPT_NAME <name> <profile>

Description:
    Generate a private key, CSR and X.509 certificate signed by the local CA.

Arguments:
    name        Base name used for the generated files.

    profile     Certificate extension profile:
                    server
                    client
                    server-client

                Examples:
                    $SCRIPT_NAME controller server
                    $SCRIPT_NAME apache-client client
                    $SCRIPT_NAME client server-client

                Generates:
                    <name>.key
                    <name>.csr
                    <name>.crt

Required files:
    ../ca.crt
    ../ca.key
    <name>.cnf

Extension profiles:
    $SCRIPT_DIR/profiles/server.cnf
    $SCRIPT_DIR/profiles/client.cnf
    $SCRIPT_DIR/profiles/server-client.cnf

Options:
    -h, --help  Show this help message and exit.

Examples:
    $SCRIPT_NAME auth server
    $SCRIPT_NAME apache-client client
    $SCRIPT_NAME client server-client
    $SCRIPT_NAME controller server

EOF
}

error() {
    echo "ERROR: $*" >&2
    exit 1
}

info() {
    echo "[+] $*"
}

warn() {
    echo "[!] $*" >&2
}

#-------------------------------------------------------------------------------
# Error trap
#-------------------------------------------------------------------------------

on_error() {
    local exit_code=$?
    local line_no=$1

    echo >&2
    echo "ERROR: command failed at line $line_no (exit code $exit_code)." >&2
    exit "$exit_code"
}

trap 'on_error $LINENO' ERR

#-------------------------------------------------------------------------------
# Argument parsing
#-------------------------------------------------------------------------------

if [[ $# -eq 0 ]]; then
    usage
    exit 1
fi

case "$1" in
    -h|--help)
        usage
        exit 0
        ;;
esac

if [[ $# -ne 2 ]]; then
    echo "ERROR: expected exactly two arguments." >&2
    echo >&2
    usage
    exit 1
fi

NAME="$1"
PROFILE="$2"

case "$PROFILE" in
    server)
        EXT_SECTION="v3_server"
        ;;
    client)
        EXT_SECTION="v3_client"
        ;;
    server-client)
        EXT_SECTION="v3_server_client"
        ;;
    *)
        error "unknown certificate profile: $PROFILE"
        ;;
esac

#-------------------------------------------------------------------------------
# Validate name
#-------------------------------------------------------------------------------

if [[ -z "$NAME" ]]; then
    error "certificate name cannot be empty."
fi

# Avoid accidentally creating paths such as ../foo.key
if [[ "$NAME" == */* ]]; then
    error "certificate name must not contain '/'."
fi

#-------------------------------------------------------------------------------
# File names
#-------------------------------------------------------------------------------

KEY_FILE="./${NAME}.key"
CSR_FILE="./${NAME}.csr"
CERT_FILE="./${NAME}.crt"

CSR_CONFIG="./${NAME}.cnf"
EXT_CONFIG="$SCRIPT_DIR/profiles/${PROFILE}.cnf"

#-------------------------------------------------------------------------------
# Dependency checks
#-------------------------------------------------------------------------------

if ! command -v openssl >/dev/null 2>&1; then
    error "openssl is not installed or is not in PATH."
fi

#-------------------------------------------------------------------------------
# Input file checks
#-------------------------------------------------------------------------------

for file in "$CA_CERT" "$CA_KEY" "$CSR_CONFIG" "$EXT_CONFIG"; do
    if [[ ! -f "$file" ]]; then
        error "required file not found: $file"
    fi
done

if [[ ! -r "$CA_CERT" ]]; then
    error "CA certificate is not readable: $CA_CERT"
fi

if [[ ! -r "$CA_KEY" ]]; then
    error "CA private key is not readable: $CA_KEY"
fi

#-------------------------------------------------------------------------------
# Prevent accidental overwrite
#-------------------------------------------------------------------------------

for file in "$KEY_FILE" "$CSR_FILE" "$CERT_FILE"; do
    if [[ -e "$file" ]]; then
        error "file already exists: $file"
    fi
done

#-------------------------------------------------------------------------------
# Display configuration
#-------------------------------------------------------------------------------

echo
echo "Certificate generation"
echo "----------------------"
echo "Name        : $NAME"
echo "Profile     : $PROFILE"
echo "Section     : $EXT_SECTION"
echo "Key size    : $KEY_BITS bits"
echo "Validity    : $CERT_DAYS days"
echo "Hash        : $HASH_ALGORITHM"
echo "CA cert     : $CA_CERT"
echo "CA key      : $CA_KEY"
echo "CSR config  : $CSR_CONFIG"
echo "Extensions  : $EXT_CONFIG"
echo

#-------------------------------------------------------------------------------
# Generate private key
#-------------------------------------------------------------------------------

info "Generating private key..."

openssl genrsa \
    -out "$KEY_FILE" \
    "$KEY_BITS"

chmod 600 "$KEY_FILE"

#-------------------------------------------------------------------------------
# Generate CSR
#-------------------------------------------------------------------------------

info "Generating certificate signing request..."

openssl req \
    -new \
    -"$HASH_ALGORITHM" \
    -key "$KEY_FILE" \
    -out "$CSR_FILE" \
    -config "$CSR_CONFIG"

#-------------------------------------------------------------------------------
# Sign certificate
#-------------------------------------------------------------------------------

info "Signing certificate with local CA..."

openssl x509 \
    -req \
    -in "$CSR_FILE" \
    -CA "$CA_CERT" \
    -CAkey "$CA_KEY" \
    -CAcreateserial \
    -out "$CERT_FILE" \
    -days "$CERT_DAYS" \
    -"$HASH_ALGORITHM" \
    -extfile "$EXT_CONFIG" \
    -extensions "$EXT_SECTION"

chmod 644 "$CERT_FILE"

#-------------------------------------------------------------------------------
# Verify certificate
#-------------------------------------------------------------------------------

info "Verifying generated certificate..."

openssl verify \
    -CAfile "$CA_CERT" \
    "$CERT_FILE"

#-------------------------------------------------------------------------------
# Show certificate information
#-------------------------------------------------------------------------------

echo
echo "Certificate generated successfully."
echo
echo "Files:"
echo "  Private key : $KEY_FILE"
echo "  CSR         : $CSR_FILE"
echo "  Certificate : $CERT_FILE"
echo

openssl x509 \
    -in "$CERT_FILE" \
    -noout \
    -subject \
    -issuer \
    -dates

echo

#-------------------------------------------------------------------------------
# Cleanup
#-------------------------------------------------------------------------------

read -r -p "Remove CSR ($CSR_FILE)? [Y/n] " answer

case "${answer:-Y}" in
    [Yy]|[Yy][Ee][Ss])
        rm -f -- "$CSR_FILE"
        info "CSR removed."
        ;;
    *)
        info "CSR kept: $CSR_FILE"
        ;;
esac

echo
info "Done."
