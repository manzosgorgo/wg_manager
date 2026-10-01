# `src/wg_auth/wg_auth_errors.py`

## Metadata

- Path: `src/wg_auth/wg_auth_errors.py`
- Language: `python`
- Lines: 17
- SHA256: `39e9e7e9cf057f1bceb51db3ebd1a6fc99d4fab44a6671f42635b88794a8a44a`

## Source

```python
class WGAuthError(Exception):

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class WGAuthSessionError(WGAuthError):
    pass


class WGAuthAuthenticationError(WGAuthError):
    pass


class WGAuthProtocolError(WGAuthError):
    pass
```
