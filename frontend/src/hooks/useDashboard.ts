import { useEffect, useState } from "react";
import { getDashboard } from "../services/api";
import type { Dashboard } from "../types/dashboard";

export function useDashboard(lookbackGameweeks = 5) {
    const [attempt, setAttempt] = useState(0);
    const key = `${lookbackGameweeks}:${attempt}`;
    const [state, setState] = useState<{key: string; data?: Dashboard; error?: string}>({key: ""});
    useEffect(() => {
        const controller = new AbortController();
        getDashboard(lookbackGameweeks, controller.signal).then(data => {
            if (!controller.signal.aborted) setState({key, data});
        }).catch((error: unknown) => {
            if (!controller.signal.aborted) setState({key, error: error instanceof Error ? error.message : "Could not load database data."});
        });
        return () => controller.abort();
    }, [key, lookbackGameweeks]);
    return {
        data: state.data,
        error: state.key === key ? state.error : undefined,
        loading: state.key !== key || (!state.data && !state.error),
        retry: () => setAttempt(previous => previous + 1),
    };
}
