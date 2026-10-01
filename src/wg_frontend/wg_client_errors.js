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
 */

export class WGError extends Error {
  constructor(message) {
    super(message);
    this.name = "WGError";
  }
}

export class WGClientError extends WGError {
  constructor(message) {
    super(message);
    this.name = "WGClientError";
  }
}

export class WGProtocolError extends WGClientError {
  constructor(message) {
    super(message);
    this.name = "WGProtocolError";
  }
}

export class WGMalformedMessageError extends WGProtocolError {
  constructor(message) {
    super(message);
    this.name = "WGMalformedMessageError";
  }
}

export class WGInvalidFieldError extends WGProtocolError {
  constructor(message) {
    super(message);
    this.name = "WGInvalidFieldError";
  }
}

export class WGInvalidEncodingError extends WGProtocolError {
  constructor(message) {
    super(message);
    this.name = "WGInvalidEncodingError";
  }
}

export class WGCounterError extends WGProtocolError {
  constructor(message) {
    super(message);
    this.name = "WGCounterError";
  }
}

export class WGCounterExhaustedError extends WGCounterError {
  constructor(message) {
    super(message);
    this.name = "WGCounterExhaustedError";
  }
}

export class WGAuthenticationError extends WGClientError {
  constructor(message) {
    super(message);
    this.name = "WGAuthenticationError";
  }
}

export class WGInvalidMACError extends WGAuthenticationError {
  constructor(message) {
    super(message);
    this.name = "WGInvalidMACError";
  }
}

export class WGSessionMismatchError extends WGAuthenticationError {
  constructor(message) {
    super(message);
    this.name = "WGSessionMismatchError";
  }
}

export class WGSessionError extends WGClientError {
  constructor(message) {
    super(message);
    this.name = "WGSessionError";
  }
}

export class WGSessionExpiredError extends WGSessionError {
  constructor(message) {
    super(message);
    this.name = "WGSessionExpiredError";
  }
}

export class WGRequestRateExceededError extends WGSessionError {
  constructor(message) {
    super(message);
    this.name = "WGRequestRateExceededError";
  }
}

export class WGReplayError extends WGProtocolError {
  constructor(message) {
    super(message);
    this.name = "WGReplayError";
  }
}