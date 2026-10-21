import type { Player } from "./player";

export interface TeamImportPreview {
  entry_id: number;
  team_name: string;
  season: string;
  gameweek: number;
  deadline_time: string;
  bank_tenths: number;
  analysis_gameweek: number | null;
  players: Player[];
  warnings: string[];
}

export interface ImportedTeam {
  entry_id: number;
  team_name: string;
  season: string;
  gameweek: number;
  deadline_time: string;
  bank_tenths: number;
  edited: boolean;
}
