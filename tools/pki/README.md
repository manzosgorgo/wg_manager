# PKI helper

`generate_CA.sh` is a standalone administrative helper for generating a
private key, CSR and X.509 certificate signed by an existing local CA.

It is intentionally not installed by the Debian packages and is not invoked
from package maintainer scripts. The CA private key remains outside the
wg_manager runtime hosts.

Expected layout when running the script from a certificate working directory:

```
../ca.crt
../ca.key
./<name>.cnf
./<name>-ext.cnf
./generate_CA.sh
```

Run:

```bash
./generate_CA.sh <name>
```

The current helper signs using the `v3_server` extension section from the
`<name>-ext.cnf` file.
