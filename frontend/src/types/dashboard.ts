import type { Player } from "./player";

export interface Team {
  id: number;
  name: string;
  short_name: string;
}

export interface Fixture {
  id: number;
  gameweek: number | null;
  fixture_date: string;
  status: string | null;
  home_team_id: number;
  away_team_id: number;
  home_score: number | null;
  away_score: number | null;
  home_difficulty: number | null;
  away_difficulty: number | null;
}

export interface ExplorerPlayer extends Player {
  price_updated_at: string | null;
  availability_status: string | null;
  has_stats: boolean;
  minutes: number | null;
  goals: number | null;
  assists: number | null;
  points: number | null;
  points_per_match: number | null;
  recent_minutes: { gameweek: number; minutes: number | null }[];
}

export interface Dashboard {
  season: string;
  latest_completed_gameweek: number | null;
  next_gameweek: number | null;
  window: { start: number | null; end: number | null; gameweeks: number };
  teams: Team[];
  fixtures: Fixture[];
  players: ExplorerPlayer[];
  difficulty_description: string;
  data_quality: { warnings: string[]; official_fpl_through_gameweek: number | null };
}
