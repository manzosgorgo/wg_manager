# `apache/production/wg-manager.conf`

## Metadata

- Path: `apache/production/wg-manager.conf`
- Language: `unknown`
- Lines: 55
- SHA256: `735f726b8ed0e55e9dcb6cc3ec6bc2b81d5f46ede7af14ec4ace530eda24108e`

## Source

```
# wg_manager production frontend + reverse proxy
#
# Installed as:
#   /etc/apache2/conf-available/wg-manager.conf
#
# The browser talks only to Apache:
#   /vpn/      -> static frontend
#   /auth      -> wg-auth 127.0.0.1:9445
#   /status    -> wg-auth 127.0.0.1:9445
#   /postauth/ -> per-session wg-client 127.0.0.1:9444

Alias /vpn/ /usr/share/wg-manager/frontend/
Alias /js/ /usr/share/wg-manager/js/

# app.js currently loads the bundled QR library from an absolute /vendor URL.
Alias /vendor/ /usr/share/wg-manager/frontend/vendor/

<Directory /usr/share/wg-manager/frontend>
    Options FollowSymLinks
    AllowOverride None
    Require all granted
    DirectoryIndex index.html
</Directory>

<Directory /usr/share/wg-manager/js>
    Options FollowSymLinks
    AllowOverride None
    Require all granted
</Directory>

SSLProxyEngine On

# Both local backend services use certificates issued by the project CA.
SSLProxyVerify require
SSLProxyCACertificateFile /etc/wg-manager/cert/ca.crt

# Backends bind to 127.0.0.1. Certificate trust is checked against the
# project CA; hostname verification is intentionally disabled for the local
# loopback proxy hop.
SSLProxyCheckPeerName Off

ProxyPass        /auth/verify https://127.0.0.1:9445/auth/verify
ProxyPassReverse /auth/verify https://127.0.0.1:9445/auth/verify

ProxyPass        /auth https://127.0.0.1:9445/auth
ProxyPassReverse /auth https://127.0.0.1:9445/auth

ProxyPass        /status https://127.0.0.1:9445/status
ProxyPassReverse /status https://127.0.0.1:9445/status

# Apache authenticates to wg-client with this PEM bundle.
SSLProxyMachineCertificateFile /etc/wg-manager/cert/apache/apache-client.pem

ProxyPass        /postauth/ https://127.0.0.1:9444/postauth/
ProxyPassReverse /postauth/ https://127.0.0.1:9444/postauth/
```
