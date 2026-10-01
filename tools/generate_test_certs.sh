#!/bin/bash
set -euo pipefail

CERT_DIR="$(cd "$(dirname "$0")/.." && pwd)/cert"

cd "$CERT_DIR"

echo "Generating test PKI in: $CERT_DIR"

rm -f \
    ca.key ca.crt ca.srl \
    server.key server.csr server.crt \
    client.key client.csr client.crt \
    auth.key auth.csr auth.crt

# ----------------------------------------------------------------------
# CA
# ----------------------------------------------------------------------

openssl genrsa -out ca.key 3072

openssl req \
    -x509 \
    -new \
    -sha256 \
    -key ca.key \
    -out ca.crt \
    -days 3650 \
    -subj "/CN=WG Manager Test CA" \
    -addext "basicConstraints=critical,CA:true" \
    -addext "keyUsage=critical,keyCertSign,cRLSign"

# ----------------------------------------------------------------------
# Server certificate
# ----------------------------------------------------------------------

openssl genrsa -out server.key 3072

openssl req \
    -new \
    -sha256 \
    -key server.key \
    -out server.csr \
    -subj "/CN=localhost"

cat > server.ext <<'EXT'
basicConstraints=critical,CA:false
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=DNS:localhost,IP:127.0.0.1
EXT

openssl x509 \
    -req \
    -sha256 \
    -in server.csr \
    -CA ca.crt \
    -CAkey ca.key \
    -CAcreateserial \
    -out server.crt \
    -days 825 \
    -extfile server.ext

# ----------------------------------------------------------------------
# Client certificate
# ----------------------------------------------------------------------

openssl genrsa -out client.key 3072

openssl req \
    -new \
    -sha256 \
    -key client.key \
    -out client.csr \
    -subj "/CN=wg-manager-test-client"

cat > client.ext <<'EXT'
basicConstraints=critical,CA:false
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=clientAuth
EXT

openssl x509 \
    -req \
    -sha256 \
    -in client.csr \
    -CA ca.crt \
    -CAkey ca.key \
    -CAcreateserial \
    -out client.crt \
    -days 825 \
    -extfile client.ext

# ----------------------------------------------------------------------
# Authentication server certificate
# ----------------------------------------------------------------------

openssl genrsa -out auth.key 3072

openssl req \
    -new \
    -sha256 \
    -key auth.key \
    -out auth.csr \
    -subj "/CN=localhost"

cat > auth.ext <<'EXT'
basicConstraints=critical,CA:false
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=DNS:localhost,IP:127.0.0.1
EXT

openssl x509 \
    -req \
    -sha256 \
    -in auth.csr \
    -CA ca.crt \
    -CAkey ca.key \
    -CAcreateserial \
    -out auth.crt \
    -days 825 \
    -extfile auth.ext

# ----------------------------------------------------------------------
# Permissions
# ----------------------------------------------------------------------

chmod 600 \
    ca.key \
    server.key \
    client.key \
    auth.key

chmod 644 \
    ca.crt \
    server.crt \
    client.crt \
    auth.crt

echo
echo "Test PKI generated successfully."
echo
echo "CA:"
openssl x509 -in ca.crt -noout -subject -issuer
openssl x509 -in ca.crt -noout -ext basicConstraints -ext keyUsage
echo
echo "Server:"
openssl x509 -in server.crt -noout -subject -issuer
openssl x509 -in server.crt -noout -ext basicConstraints -ext keyUsage -ext extendedKeyUsage
echo
echo "Client:"
openssl x509 -in client.crt -noout -subject -issuer
openssl x509 -in client.crt -noout -ext basicConstraints -ext keyUsage -ext extendedKeyUsage
echo
echo "Auth:"
openssl x509 -in auth.crt -noout -subject -issuer
openssl x509 -in auth.crt -noout -ext basicConstraints -ext keyUsage -ext extendedKeyUsage
echo
echo "Verification:"
openssl verify -CAfile ca.crt server.crt client.crt auth.crt
