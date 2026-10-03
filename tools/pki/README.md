# PKI helper

`generate_CA.sh` is a standalone administrative helper for generating a
private key, CSR and X.509 certificate signed by an existing local CA.

It is intentionally not installed by the Debian packages and is not invoked
from package maintainer scripts. The CA private key remains outside the
wg_manager runtime hosts.

## Inputs

Run the helper from a certificate working directory containing:

```
../ca.crt
../ca.key
./<name>.cnf
```

The per-certificate `<name>.cnf` contains the CSR subject and, when needed,
SAN/request-specific settings. TLS usage constraints are selected separately
through one of the shared extension profiles under `tools/pki/profiles/`.

Available profiles:

- `server` -> `extendedKeyUsage = serverAuth`
- `client` -> `extendedKeyUsage = clientAuth`
- `server-client` -> `extendedKeyUsage = serverAuth, clientAuth`

## Usage

```bash
./generate_CA.sh <name> <profile>
```

Examples for wg_manager:

```bash
./generate_CA.sh auth server
./generate_CA.sh apache-client client
./generate_CA.sh client server-client
./generate_CA.sh controller server
```

The generated files are:

```
<name>.key
<name>.csr
<name>.crt
```

The helper refuses to overwrite existing key/CSR/certificate files and verifies
the generated certificate against `../ca.crt`.

## Apache mTLS client PEM

Apache's `SSLProxyMachineCertificateFile` needs the client certificate and
its private key in the same PEM file. After generating `apache-client` with
the `client` profile:

```bash
cat apache-client.crt apache-client.key > apache-client.pem
```

For the packaged layout, install it as:

```bash
sudo install -o root -g www-data -m 0640 \
    apache-client.pem \
    /etc/wg-manager/cert/apache/apache-client.pem
```
