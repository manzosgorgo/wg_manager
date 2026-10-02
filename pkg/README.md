# Debian packaging

Debian packaging metadata lives in the repository-level `debian/` directory.

The source package builds two binary packages:

- `wg-manager-auth-client`: authentication service, per-session client,
  frontend and Apache integration.
- `wg-manager-controller`: privileged WireGuard controller for the host that
  owns the WireGuard interface.

The old raw `dpkg-deb` staging roots were removed once the project switched
to debhelper. The `debian/*.install` files are the authoritative file
manifests for the two binary packages.
