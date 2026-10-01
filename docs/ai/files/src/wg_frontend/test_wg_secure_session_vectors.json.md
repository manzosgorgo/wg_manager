# `src/wg_frontend/test_wg_secure_session_vectors.json`

## Metadata

- Path: `src/wg_frontend/test_wg_secure_session_vectors.json`
- Language: `json`
- Lines: 41
- SHA256: `fe21ad55cfcf26f5d999182a94439f4a3df883a55c5b6a387fe69248ff3068f9`

## Source

```json
{
  "protocol_version": "wg_manager secure session v1",
  "config": {
    "session_id_size": 16,
    "nonce_size": 32,
    "session_key_size": 64,
    "counter_min": 1,
    "counter_max": 4294967295
  },
  "inputs": {
    "k_session_hex": "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f",
    "session_id_hex": "a0a1a2a3a4a5a6a7a8a9aaabacadaeaf"
  },
  "derived": {
    "session_seed_hex": "0f590f0bd6d4e5c0a7d083e30bfe385a06cbfca2551180251b2fbeba84c6fc12"
  },
  "request_vector": {
    "counter": 1,
    "nonce_hex": "c0c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcdddedf",
    "method": "POST",
    "path": "/api/test",
    "body_hex": "7b22636f6d6d616e64223a2268656c6c6f227d",
    "body_utf8": "{\"command\":\"hello\"}",
    "message_hex": "a0a1a2a3a4a5a6a7a8a9aaabacadaeaf7c317cc0c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcdddedf7c504f53547c2f6170692f746573747c563feafe37b72e1d58b7bfe90ffc9d6560e9193d5d2ee9de1852d59794f46143",
    "expected_mac_hex": "57cfd36f6d2ac918d17be02b428ac8e9190be12a28b8c74de3285a97cc38d569",
    "session_id_b64": "oKGio6SlpqeoqaqrrK2urw==",
    "nonce_b64": "wMHCw8TFxsfIycrLzM3Oz9DR0tPU1dbX2Nna29zd3t8=",
    "mac_b64": "V8_Tb20qyRjRe-ArQorI6RkL4SoouMdN4yhal8w41Wk="
  },
  "response_vector": {
    "counter": 1,
    "nonce_hex": "c0c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcdddedf",
    "status": 200,
    "body_hex": "4f4b",
    "body_utf8": "OK",
    "message_hex": "a0a1a2a3a4a5a6a7a8a9aaabacadaeaf7c317cc0c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcdddedf7c3230307c565339bc4d33d72817b583024112eb7f5cdf3e5eef0252d6ec1b9c9a94e12bb3",
    "expected_mac_hex": "da5b7e7fc5c59d50b4a287ff6456cb929649e2db4dc522979498033078be52c9",
    "session_id_b64": "oKGio6SlpqeoqaqrrK2urw==",
    "mac_b64": "2lt-f8XFnVC0oof_ZFbLkpZJ4ttNxSKXlJgDMHi-Usk="
  }
}
```
