# Package staging roots

This directory contains the filesystem roots used to build the two Debian
packages for wg_manager.

- `wg-manager-auth-client/`: authentication service, per-session client,
  frontend and Apache integration. This package is installed on the web/auth
  host.
- `wg-manager-controller/`: privileged WireGuard controller. This package is
  installed on the WireGuard host.

Each package root follows the raw `dpkg-deb` layout. Package metadata lives in
`DEBIAN/control`; runtime files will be added under `etc/`, `usr/` and
`var/` as the production layout is finalized.

These directories are staging trees, not source-install locations.
