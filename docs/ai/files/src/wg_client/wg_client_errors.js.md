# `src/wg_client/wg_client_errors.js`

## Metadata

- Path: `src/wg_client/wg_client_errors.js`
- Language: `javascript`
- Lines: 107
- SHA256: `571abcf5ac75fdd9662a8a98e2ddeae8207cbed1d740914c224d63c99b76aa4a`

## Source

```javascript
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

export class WGProtocolError extends WGError {
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

export class WGAuthenticationError extends WGError {
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

export class WGReplayError extends WGError {
  constructor(message) {
    super(message);
    this.name = "WGReplayError";
  }
}
export class WGSessionExpiredError extends WGError {
  constructor(message) {
    super(message);
    this.name = "WGSessionExpiredError";
  }
}

export class WGRequestRateExceededError extends WGError {
  constructor(message) {
    super(message);
    this.name = "WGRequestRateExceededError";
  }
}
```
