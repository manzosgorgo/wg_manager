const session = new WGAuthSession("https://127.0.0.1:9445");

const result = await session.authenticate("test-user");

console.assert(result.ok === true);
console.assert(session.sessionId);
console.assert(session.kSession);

await session.logout();
