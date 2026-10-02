class WGError(Exception):
    """Base class for all wg-manager exceptions."""

    pass


class WGControllerError(WGError):
    """Error returned by the WireGuard controller."""

    def __init__(self, status, message, response=None):
        super().__init__(message)
        self.status = status
        # The API handler reads exc.message: it was never set before.
        self.message = message
        self.response = response


class WGClientError(WGError):
    """Base class for errors raised by the WireGuard client."""

    pass


class WGPeerError(WGClientError):
    """A peer operation could not be completed (carries an HTTP status)."""

    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


class WGAuthenticationError(WGClientError):
    """Authentication failed."""

    pass


class WGSessionError(WGClientError):
    """Session is invalid or expired."""

    pass


class WGProtocolError(WGClientError):
    """Invalid or malformed protocol message."""

    pass


class WGConnectionClosed(WGProtocolError):
    """IPC connection to the WireGuard client was closed with an EOF."""

    pass


class WGPeerPersistenceError(WGProtocolError):
    """Semantic error returned by the auth persistence IPC."""

    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


class WGAPIError(WGClientError):
    """Error raised while processing an API request."""

    pass


class WGReplayError(WGProtocolError):
    """A valid protocol message was rejected because it was replayed."""

    pass
class WGMalformedMessageError(WGProtocolError):
    """The message structure is malformed or incomplete."""
    pass


class WGInvalidFieldError(WGProtocolError):
    """A message field has an invalid type or value."""
    pass


class WGInvalidEncodingError(WGProtocolError):
    """A message field uses an invalid encoding."""
    pass


class WGCounterError(WGProtocolError):
    """A session counter is invalid or cannot be used."""
    pass


class WGCounterExhaustedError(WGCounterError):
    """The session counter has reached its maximum value."""
    pass


class WGSessionExpiredError(WGSessionError):
    """The secure session lifetime has expired."""
    pass


class WGRequestRateExceededError(WGSessionError):
    """The configured maximum request frequency has been exceeded."""
    pass


class WGInvalidMACError(WGAuthenticationError):
    """The supplied MAC does not authenticate the message."""
    pass


class WGSessionMismatchError(WGAuthenticationError):
    """The message belongs to a different session."""
    pass