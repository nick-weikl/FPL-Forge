export interface StrategyRequest {
  current_gameweek: number;
  bank_tenths: number;
  free_transfers: number;
  owned_player_ids: number[];
  candidates_per_player: number;
}

export interface StrategyResponse {
    recommended_strategy: string;
    best_net_score_gain: number;
    reason: {
        summary: string;
        decision_detail: string;
        recommended_moves: {
            player_out: string;
            player_in: string;
        }[];
    };
}