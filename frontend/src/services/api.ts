import { apiErrorMessage } from "../utils/apiError";
import type { Dashboard } from "../types/dashboard";
import type { Player } from "../types/player";
import type { StrategyRequest, StrategyResponse } from "../types/recommendation";

const base_url = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api"

export async function getTransferStrategy(request: StrategyRequest, signal?: AbortSignal) : Promise<StrategyResponse> {
    try {
        const response = await fetch(base_url + "/recommendations/strategy", {
            method: "POST", 
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(request),
            signal
        })

        if (!response.ok) {
            const body = await response.json().catch(() => null);
            throw new Error(apiErrorMessage(body, response.status))
        }

        const data = await response.json();
        return data;
    }
    catch (error) {
        if (!signal?.aborted) console.error("Failed", error);
        throw error;
    }
}


export async function getPlayers() : Promise<Player[]> {
    try {
        const response = await fetch(base_url + "/players" , {
            method: "GET"
        })

        if (!response.ok) {
            const body = await response.json().catch(() => null);
            throw new Error(apiErrorMessage(body, response.status))
        }

        const data = await response.json();
        return data;
    }
    catch (error) {
        console.error("Failed", error);
        throw error;
    }
}

export async function getDashboard(lookbackGameweeks = 5, signal?: AbortSignal): Promise<Dashboard> {
    const response = await fetch(`${base_url}/dashboard?lookback_gameweeks=${lookbackGameweeks}`, {signal});
    if (!response.ok) throw new Error(`Could not load season data (${response.status}). Check that the backend is running and try again.`);
    return response.json();
}
