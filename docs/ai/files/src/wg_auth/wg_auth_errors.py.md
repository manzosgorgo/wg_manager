# `src/wg_auth/wg_auth_errors.py`

## Metadata

- Path: `src/wg_auth/wg_auth_errors.py`
- Language: `python`
- Lines: 36
- SHA256: `e0b60e3051039e4f17c403fdabf884ee49c5629228aa179c6b6d3afeebbbdca1`

## Source

```python
"""
Exception hierarchy used by the authentication service.
"""

class WGAuthError(Exception):
    """
    Base exception carrying a stable human-readable auth error message.
    """

    def __init__(self, message):
        """
        Store *message* both on Exception and on the public message attribute.
        """
        super().__init__(message)
        self.message = message


class WGAuthSessionError(WGAuthError):
    """
    Raised when an operation violates the auth session state machine.
    """
    pass


class WGAuthAuthenticationError(WGAuthError):
    """
    Raised when OPAQUE authentication cannot be completed safely.
    """
    pass


class WGAuthProtocolError(WGAuthError):
    """
    Raised for malformed or unsupported auth/IPC protocol input.
    """
    pass
```
