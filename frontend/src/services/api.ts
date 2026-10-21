import { apiErrorMessage } from "../utils/apiError";
import type { Dashboard } from "../types/dashboard";
import type { Player } from "../types/player";
import type { StrategyRequest, StrategyResponse } from "../types/recommendation";
const baseUrl = (import.meta.env.VITE_API_BASE_URL || "/api").replace(/\/$/, "");
async function jsonRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const timeout = AbortSignal.timeout(45000);
  const signal = options.signal ? AbortSignal.any([options.signal, timeout]) : timeout;
  try {
    const response = await fetch(`${baseUrl}${path}`, { ...options, signal });
    const body = await response.json().catch(() => null);
    if (!response.ok) throw new Error(apiErrorMessage(body, response.status));
    if (body === null)
      throw new Error("The server returned an unreadable response. Please try again.");
    return body as T;
  } catch (error) {
    if (timeout.aborted)
      throw new Error("This request took too long. Please try again shortly.", { cause: error });
    if (error instanceof TypeError)
      throw new Error("Could not reach FPL Forge. Check your connection and try again.", {
        cause: error,
      });
    throw error;
  }
}
export function getTransferStrategy(
  request: StrategyRequest,
  signal?: AbortSignal,
): Promise<StrategyResponse> {
  return jsonRequest("/recommendations/strategy", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
    signal,
  });
}
export function getPlayers(): Promise<Player[]> {
  return jsonRequest("/players");
}
export function getDashboard(lookbackGameweeks = 5, signal?: AbortSignal): Promise<Dashboard> {
  return jsonRequest(`/dashboard?lookback_gameweeks=${lookbackGameweeks}`, { signal });
}
export function previewTeamImport(
  entryId: number,
  signal?: AbortSignal,
): Promise<import("../types/teamImport").TeamImportPreview> {
  return jsonRequest(`/fpl/teams/${entryId}/preview`, { signal });
}
