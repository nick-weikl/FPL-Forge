export interface StrategyRequest {
  current_gameweek: number;
  starting_player_ids: number[];
  bench_player_ids: number[];
  captain_id: number;
  vice_captain_id: number;
  bank_tenths: number;
  free_transfers: number;
  owned_player_ids: number[];
  candidates_per_player: number;
  selling_prices_tenths?: Record<number, number>;
}

export interface TransferPlayer {
  player_id: number;
  name: string;
  team_id: number;
  team_name: string | null;
  position: string;
  score: number;
  price_tenths: number;
}

export interface TransferMove {
  player_out: TransferPlayer;
  player_in: TransferPlayer;
  score_gain: number;
}

export interface Projection {
  before_points: number;
  after_points: number;
  transfer_hit: number;
  net_gain: number;
  gameweeks: {
    gameweek: number;
    before_points: number;
    after_points: number;
    raw_gain: number;
    transfer_hit: number;
    net_gain: number;
  }[];
}

export interface StrategyResponse {
  selling_price_assumptions: number[];
  baseline: Projection;
  lineup_mode: "fixed_starting_xi";
  recommended_strategy: "single_transfer" | "double_transfer" | "no_transfer";

  best_net_score_gain: number;
  score_units: "expected_fpl_points";
  horizon_gameweeks: number;
  warnings: string[];
  data_quality: {
    official_fpl_through_gameweek: number | null;
    api_sports_through_gameweek: number | null;
  };
  free_transfers: number;

  reason: {
    summary: string;
    decision_detail: string;
    recommended_moves: {
      player_out: string;
      player_in: string;
    }[];
  };

  single_transfer?: {
    transfer: TransferMove & {
      recommendation_strength: string;
      available_budget_tenths: number;
      remaining_bank_tenths: number;
    };
    projection: Projection;
    raw_score_gain: number;
    transfer_cost: number;
    net_score_gain: number;
  } | null;

  double_transfer?: {
    transfer_pair: {
      transfers: TransferMove[];
      combined_score_gain: number;
      remaining_bank_tenths: number;
    };
    projection: Projection;
    raw_score_gain: number;
    transfer_cost: number;
    net_score_gain: number;
  } | null;
}
