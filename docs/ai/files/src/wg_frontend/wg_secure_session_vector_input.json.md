# `src/wg_frontend/wg_secure_session_vector_input.json`

## Metadata

- Path: `src/wg_frontend/wg_secure_session_vector_input.json`
- Language: `json`
- Lines: 21
- SHA256: `db430ebc83378c5915a4d212297c479b4b48be91a2fe69190dadc403fbc5205d`

## Source

```json
{
  "config": {
    "session_id_size": 16,
    "nonce_size": 32,
    "session_key_size": 32,
    "counter_min": 1,
    "counter_max": 4294967295
  },
  "k_session_hex": "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f202122232425262728292a2b2c2d2e2f303132333435363738393a3b3c3d3e3f",
  "session_id_hex": "a0a1a2a3a4a5a6a7a8a9aaabacadaeaf",
  "request": {
    "nonce_hex": "c0c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcdddedf",
    "method": "POST",
    "path": "/api/test",
    "body_utf8": "{\"command\":\"hello\"}"
  },
  "response": {
    "status": 200,
    "body_utf8": "OK"
  }
}
```
