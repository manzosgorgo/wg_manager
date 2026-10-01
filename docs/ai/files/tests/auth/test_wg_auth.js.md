# `tests/auth/test_wg_auth.js`

## Metadata

- Path: `tests/auth/test_wg_auth.js`
- Language: `javascript`
- Lines: 9
- SHA256: `208cebe8510ef9a5a5e8e4889db255a533fda44a09c6457e854e8c3754e14e1f`

## Source

```javascript
const session = new WGAuthSession("https://127.0.0.1:9445");

const result = await session.authenticate("test-user");

console.assert(result.ok === true);
console.assert(session.sessionId);
console.assert(session.kSession);

await session.logout();
```
