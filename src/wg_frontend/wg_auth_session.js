export class WGAuthSession {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.sessionId = null;
        this.kSession = null;
    }

    async authenticate(fakeId) {
        const response = await fetch(
            `${this.baseUrl}/auth`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    fake_id: fakeId
                })
            }
        );

        const result = await response.json();

        if (!response.ok || !result.ok) {
            throw new Error(
                result.error ?? "authentication failed"
            );
        }

        this.sessionId = result.session_id;
        this.kSession = result.k_session;

        return result;
    }

    async logout() {
        await fetch(
            `${this.baseUrl}/auth`,
            {
                method: "DELETE"
            }
        );

        this.sessionId = null;
        this.kSession = null;
    }
}