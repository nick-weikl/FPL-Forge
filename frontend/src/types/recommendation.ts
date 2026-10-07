export interface StrategyRequest {
  current_gameweek: number;
  bank_tenths: number;
  free_transfers: number;
  owned_player_ids: number[];
  candidates_per_player: number;
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

export interface StrategyResponse {
    recommended_strategy:
        | "single_transfer"
        | "double_transfer"
        | "no_transfer";

    best_net_score_gain: number;
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
        raw_score_gain: number;
        transfer_cost: number;
        net_score_gain: number;
    } | null;
}