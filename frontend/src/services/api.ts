import type { Player } from "../types/player";
import type { StrategyRequest, StrategyResponse } from "../types/recommendation";

const base_url = "http://127.0.0.1:8000/api"

export async function getTransferStrategy(request: StrategyRequest) : Promise<StrategyResponse> {
    try {
        const response = await fetch(base_url + "/recommendations/strategy", {
            method: "POST", 
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(request)
        })

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`)
        }

        const data = await response.json();
        return data;
    }
    catch (error) {
        console.error("Failed", error);
        throw error;
    }
}


export async function getPlayers() : Promise<Player[]> {
    try {
        const response = await fetch(base_url + "/players" , {
            method: "GET"
        })

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`)
        }

        const data = await response.json();
        return data;
    }
    catch (error) {
        console.error("Failed", error);
        throw error;
    }
}