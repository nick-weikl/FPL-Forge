import { readJSONStored } from "./storage.ts";
import type { ImportedTeam, TeamImportPreview } from "../types/teamImport";

export function parseTeamId(text: string): number | null {
  const trimmed = text.trim();
  if (!/^[1-9]\d*$/.test(trimmed)) return null;
  const id = Number(trimmed);
  return Number.isSafeInteger(id) && id <= 2147483647 ? id : null;
}

export function importedTeamMetadata(preview: TeamImportPreview): ImportedTeam {
  return {
    entry_id: preview.entry_id,
    team_name: preview.team_name,
    season: preview.season,
    gameweek: preview.gameweek,
    deadline_time: preview.deadline_time,
    bank_tenths: preview.bank_tenths,
    edited: false,
  };
}

export function readImportedTeam(): ImportedTeam | null {
  if (typeof window === "undefined") return null;
  try {
    const value: unknown = JSON.parse(readJSONStored("fpl-forge-import", "null"));
    if (!value || typeof value !== "object") return null;
    const team = value as Partial<ImportedTeam>;
    if (
      !Number.isInteger(team.entry_id) ||
      typeof team.team_name !== "string" ||
      typeof team.season !== "string" ||
      !Number.isInteger(team.gameweek) ||
      typeof team.deadline_time !== "string" ||
      !Number.isInteger(team.bank_tenths) ||
      typeof team.edited !== "boolean"
    )
      return null;
    return team as ImportedTeam;
  } catch {
    return null;
  }
}
