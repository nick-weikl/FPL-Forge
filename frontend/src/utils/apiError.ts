export function apiErrorMessage(body: unknown, status: number): string {
    const fallback = `Request failed (${status}). Please check your entries and try again.`;
    if (!body || typeof body !== "object" || !("detail" in body)) return fallback;
    const detail = body.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
        const messages = detail.flatMap((issue: unknown) => {
            if (!issue || typeof issue !== "object" || !("msg" in issue) || typeof issue.msg !== "string") return [];
            const path = "loc" in issue && Array.isArray(issue.loc)
                ? issue.loc.filter(part => part !== "body" && part !== "[key]").map(String).join(" → ") : "";
            return [`${path ? `${path}: ` : ""}${issue.msg}`];
        });
        if (messages.length) return messages.join("; ");
    }
    if (detail && typeof detail === "object" && "error" in detail && typeof detail.error === "string") return detail.error;
    return fallback;
}
