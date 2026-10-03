/**
 * Gerarchia di errori del protocollo wg_client / wg_secure_session.
 * Deve restare identica, come contratto (nomi delle classi), alla
 * gerarchia Python in wg_client_errors.py:
 *
 *   WGError
 *   ├── WGProtocolError
 *   │   ├── WGMalformedMessageError
 *   │   ├── WGInvalidFieldError
 *   │   ├── WGInvalidEncodingError
 *   │   └── WGCounterError
 *   │       └── WGCounterExhaustedError
 *   ├── WGAuthenticationError
 *   │   ├── WGInvalidMACError
 *   │   └── WGSessionMismatchError
 *   └── WGReplayError
 *\n * @module wg_client_errors\n */\n\n/** Base class for all browser-side wg_manager errors. */
export class WGError extends Error {
  constructor(message) {
    super(message);
    this.name = "WGError";
  }
}

/** Base class for errors raised by the browser wg-client implementation. */
export class WGClientError extends WGError {
  constructor(message) {
    super(message);
    this.name = "WGClientError";
  }
}

/** Malformed or unsupported secure-session/protocol input. */
export class WGProtocolError extends WGClientError {
  constructor(message) {
    super(message);
    this.name = "WGProtocolError";
  }
}

/** Required authentication structure is missing or malformed. */
export class WGMalformedMessageError extends WGProtocolError {
  constructor(message) {
    super(message);
    this.name = "WGMalformedMessageError";
  }
}

/** A protocol field has an invalid type, size or value. */
export class WGInvalidFieldError extends WGProtocolError {
  constructor(message) {
    super(message);
    this.name = "WGInvalidFieldError";
  }
}

/** A protocol field cannot be decoded from its required encoding. */
export class WGInvalidEncodingError extends WGProtocolError {
  constructor(message) {
    super(message);
    this.name = "WGInvalidEncodingError";
  }
}

/** A secure-session counter is invalid or unusable. */
export class WGCounterError extends WGProtocolError {
  constructor(message) {
    super(message);
    this.name = "WGCounterError";
  }
}

/** The outgoing secure-session counter reached its configured maximum. */
export class WGCounterExhaustedError extends WGCounterError {
  constructor(message) {
    super(message);
    this.name = "WGCounterExhaustedError";
  }
}

/** Base class for cryptographic authentication failures. */
export class WGAuthenticationError extends WGClientError {
  constructor(message) {
    super(message);
    this.name = "WGAuthenticationError";
  }
}

/** The supplied HMAC does not authenticate the message. */
export class WGInvalidMACError extends WGAuthenticationError {
  constructor(message) {
    super(message);
    this.name = "WGInvalidMACError";
  }
}

/** Authentication metadata belongs to another session. */
export class WGSessionMismatchError extends WGAuthenticationError {
  constructor(message) {
    super(message);
    this.name = "WGSessionMismatchError";
  }
}

/** Base class for secure-session lifecycle/policy failures. */
export class WGSessionError extends WGClientError {
  constructor(message) {
    super(message);
    this.name = "WGSessionError";
  }
}

/** The configured secure-session lifetime has expired. */
export class WGSessionExpiredError extends WGSessionError {
  constructor(message) {
    super(message);
    this.name = "WGSessionExpiredError";
  }
}

/** The configured maximum request frequency was exceeded. */
export class WGRequestRateExceededError extends WGSessionError {
  constructor(message) {
    super(message);
    this.name = "WGRequestRateExceededError";
  }
}

/** A message counter was already accepted or fell outside the replay window. */
export class WGReplayError extends WGProtocolError {
  constructor(message) {
    super(message);
    this.name = "WGReplayError";
  }
}