# `debian/wg-manager-auth-client/DEBIAN/md5sums`

## Metadata

- Path: `debian/wg-manager-auth-client/DEBIAN/md5sums`
- Language: `unknown`
- Lines: 48
- SHA256: `7fdfb645b6b0fd12b72034c5a5971ae74827a85eddadd1dcd4a3154dafd33ced`

## Source

```
56ef5cef75598b88663a64355441858b  usr/lib/systemd/system/wg-auth.service
5b03818d08708fe0f1e692c4d2b5cf18  usr/lib/systemd/system/wg-client.socket
8e0b342ff12e0f61c89796fdc6ab24de  usr/lib/systemd/system/wg-client@.service
59b8c7867183bbe8670f8a163f13b65a  usr/lib/sysusers.d/wg-manager-auth-client.conf
ad63b221754bcaa378fc48e9940d5b4e  usr/lib/tmpfiles.d/wg-manager-auth-client.conf
d41d8cd98f00b204e9800998ecf8427e  usr/lib/wg-manager/src/wg_auth/__init__.py
96753e13c7be912747607f97e9a54edc  usr/lib/wg-manager/src/wg_auth/wg_auth.py
98e2124c3431f72dd24f46cf792c43bb  usr/lib/wg-manager/src/wg_auth/wg_auth_API.py
fa42f4a08c0cee187e8bc5e06eedff82  usr/lib/wg-manager/src/wg_auth/wg_auth_API_handler.py
4935b4c97de71f8d21f6e89b4c617bb0  usr/lib/wg-manager/src/wg_auth/wg_auth_IPC.py
a3e3b0dc38414f5e05a5e94f903c518d  usr/lib/wg-manager/src/wg_auth/wg_auth_account_service.py
6bed4337fa7f478b6d7956595e259804  usr/lib/wg-manager/src/wg_auth/wg_auth_errors.py
03d2ef24e5f10f058e10bf56e977b41b  usr/lib/wg-manager/src/wg_auth/wg_auth_lifecycle.py
c1af79a6d33432ab852d47c776d0ab82  usr/lib/wg-manager/src/wg_auth/wg_auth_ownership_service.py
f5a017f3a4c7528a0eff86cd1aeb160c  usr/lib/wg-manager/src/wg_auth/wg_auth_peer_registry.py
082acfa23b0540f1de2152c8f0d7bc33  usr/lib/wg-manager/src/wg_auth/wg_auth_session.py
dceb57a65786cb728aaf2be1247a5af1  usr/lib/wg-manager/src/wg_auth/wg_auth_user_store.py
d41d8cd98f00b204e9800998ecf8427e  usr/lib/wg-manager/src/wg_client/__init__.py
3500d41b46ba300eba5060a33098d447  usr/lib/wg-manager/src/wg_client/wg_client.py
7210bcf68fc3d371628c677b64e601a8  usr/lib/wg-manager/src/wg_client/wg_client_API.py
8ae01d4bf8d3aca1d0991fb27d24c559  usr/lib/wg-manager/src/wg_client/wg_client_API_handler.py
59a9aea46ad71b6cc2e965c631f258f3  usr/lib/wg-manager/src/wg_client/wg_client_IPC.py
30c396ba5ff4e274d4df2930371574bb  usr/lib/wg-manager/src/wg_client/wg_client_activator.py
f9067846420b299939a615bc4a2c7d76  usr/lib/wg-manager/src/wg_client/wg_client_config.py
17f7d22de844ee1df56aad4ba2117ae2  usr/lib/wg-manager/src/wg_client/wg_client_errors.py
dbedf2c3d66fd69212f21b3f700842f0  usr/lib/wg-manager/src/wg_client/wg_client_lifecycle.py
e2b3acbcce62efc8b02988d46d9e230e  usr/lib/wg-manager/src/wg_client/wg_controller_client.py
fa8ba52538a33851bfdb10afe192a729  usr/lib/wg-manager/src/wg_client/wg_peer_service.py
892e772fce25a580beedc62acaf32411  usr/lib/wg-manager/src/wg_client/wg_secure_session.py
8f81399f41ff922ad1ba0c8c84179d1d  usr/lib/wg-manager/tools/manage_users.py
9a795c3892dfe5551e02aee729ff83c1  usr/sbin/wg-manager-check-auth-client
d046bf5e934209d8e230e5d162e6fd85  usr/sbin/wg-manager-users
4e0ca2bc63e61797836c39b9a6e33ddc  usr/share/doc/wg-manager-auth-client/LICENSE.libopaque.gz
43c68f571ee504ba5d3ac78e944f08b0  usr/share/doc/wg-manager-auth-client/certificates.README
eb0112db02ae1ae2a9359c2ab0785038  usr/share/doc/wg-manager-auth-client/changelog.Debian.gz
336fea291cd45118c2ebcb8905c64e68  usr/share/doc/wg-manager-auth-client/configuration.md.gz
305882b08911752f5da989e8d77fd8bf  usr/share/doc/wg-manager-auth-client/deployment.md.gz
f44fba97bf80e88a04cf990aa377ed9b  usr/share/wg-manager/frontend/app.js
3c0e3781ace2e94fb76ca33be807c10a  usr/share/wg-manager/frontend/index.html
b3e72564cf82e5b7e9e352fd2dc2f421  usr/share/wg-manager/frontend/style.css
84a242a6a09d39b3f1b7307044a705f2  usr/share/wg-manager/frontend/vendor/qrcode.LICENSE
517b55d3688ce9ef1085a3d9632bcb97  usr/share/wg-manager/frontend/vendor/qrcode.min.js
a69fe6cb9251788465a72ff738c80966  usr/share/wg-manager/js/vendor/libopaque.js
73841ef4a01d1d1ae8a675226c489a39  usr/share/wg-manager/js/wg_auth_session.js
775a23f3f237fe4790544e644d7f37b0  usr/share/wg-manager/js/wg_client_api.js
42ca3f9c4ed9235c55682d781ed1e535  usr/share/wg-manager/js/wg_client_errors.js
b9bb3c85e852469ea55dc3e60d7a7c28  usr/share/wg-manager/js/wg_opaque_client.js
854e9f95abccb401bb273e1efde5a792  usr/share/wg-manager/js/wg_secure_session.js
```
