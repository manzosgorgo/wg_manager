# `debian/rules`

## Metadata

- Path: `debian/rules`
- Language: `unknown`
- Lines: 7
- SHA256: `93299adec4ab2d7bdd1100e8652fd86f7c3df70b38c2b2030ba4d5c2c392c72f`

## Source

```
#!/usr/bin/make -f

%:
	dh $@

override_dh_installsystemd:
	dh_installsystemd --no-start --no-enable
```
