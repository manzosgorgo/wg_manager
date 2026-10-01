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