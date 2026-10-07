import {getTransferStrategy} from "../services/api.ts"
import { useState } from "react"
import type { StrategyRequest, StrategyResponse, TransferMove } from "../types/recommendation.ts"
import type { Player } from "../types/player.ts";
import "./RecommendationPage.css"
import type { Dispatch, SetStateAction } from "react";
// import SquadPage from "./SquadPage";
import { Link } from "react-router";


interface RecommendationPageProps {
    selectedPlayers: Player[];
    error: string | null;
    setError: Dispatch<SetStateAction<string | null>>;
    currentGameweek: string;
    setCurrentGameweek: Dispatch<SetStateAction<string>>;
    freeTransfers: string;
    setFreeTransfers: Dispatch<SetStateAction<string>>;
    bankMillions: string;
    setBankMillions: Dispatch<SetStateAction<string>>;
}


export default function RecommendationPage({
    selectedPlayers,
    error,
    setError,
    currentGameweek,
    setCurrentGameweek,
    freeTransfers,
    setFreeTransfers,
    bankMillions,
    setBankMillions,
}: RecommendationPageProps) {
    const [recommendation, setRecommendation] = useState<StrategyResponse | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const strategyLabels: Record<string, string> = {
        single_transfer: "Single transfer",
        double_transfer: "Double transfer",
        no_transfer: "Keep current squad",
    };

    const goalkeeperCount = selectedPlayers.filter(
    (player) => player.position === "Goalkeeper"
    ).length;
    const defenderCount = selectedPlayers.filter(
        (player) => player.position === "Defender"
    ).length;
    const midfielderCount = selectedPlayers.filter(
        (player) => player.position === "Midfielder"
    ).length;
    const attackerCount = selectedPlayers.filter(
        (player) => player.position === "Attacker"
    ).length;

    let recommendedTransfers: TransferMove[] = [];
    let remainingBankTenths: number | null = null;

    if (
        recommendation?.recommended_strategy === "single_transfer" &&
        recommendation.single_transfer
    ) {
        const transfer = recommendation.single_transfer.transfer;

        recommendedTransfers = [transfer];
        remainingBankTenths = transfer.remaining_bank_tenths;
    } else if (
        recommendation?.recommended_strategy === "double_transfer" &&
        recommendation.double_transfer
    ) {
        const pair = recommendation.double_transfer.transfer_pair;

        recommendedTransfers = pair.transfers;
        remainingBankTenths = pair.remaining_bank_tenths;
    }


    async function handleGetRecommendation() {
        setRecommendation(null)
        setError(null)

        if (currentGameweek.trim() === "") {
            setError("Please enter a gameweek")
            return
        }
        const gameweek = Number(currentGameweek)
        if (!Number.isInteger(gameweek) || gameweek < 1 || gameweek > 38) {
            setError("Enter a valid gameweek.")
            return
        }

        if (freeTransfers.trim() === "") {
            setError("Enter a number of transfers")
            return
        }
        const transferCount = Number(freeTransfers)
        if (!Number.isInteger(transferCount) || transferCount < 0) {
            setError("Enter a valid number of transfers")
            return
        }

        if (bankMillions.trim() === "") {
            setError("Enter a bank amount")
            return
        }
        const bank = Number(bankMillions)
        if (!Number.isFinite(bank) || bank < 0) {
            setError("Enter a valid bank amount")
            return
        }
        const bankTenths = Math.round(bank * 10)
        if (( bankTenths / 10 ) !== bank) {
            setError("Enter the bank amount in increments of £0.1m")
            return
        }


        if (selectedPlayers.length !== 15) {
            setError("Select exactly 15 players.")
            return;
        }


        if (goalkeeperCount !== 2 || defenderCount !== 5 || midfielderCount !== 5 || attackerCount !== 3) {
            setError("Select 2 Goalkeepers, 5 Defenders, 5 Midfielders, and 3 Attackers")
            return
        }

        const teamCounts: Record<number, number> = {};

        for (const player of selectedPlayers) {
            const teamId = player.team_id;
            const currentCount = teamCounts[teamId] ?? 0;
            teamCounts[teamId] = currentCount + 1;
            if (teamCounts[teamId] > 3) {
                setError("Only 3 players allowed per team.")
                return
            }
        }
           

        setIsLoading(true)


        try {
            const request: StrategyRequest = {
            current_gameweek: gameweek,
            bank_tenths: bankTenths,
            free_transfers: transferCount, 
            candidates_per_player: 10, 
            owned_player_ids: selectedPlayers.map((player) => player.id),   
            }

            const result = await getTransferStrategy(request)
            setRecommendation(result)

            // console.log(result)
            console.log(JSON.stringify(result, null, 2));
        }
        catch (error) {
            console.error("Failed", error)
            setError("Could not fetch a recommendation. Please try again")
        }
        finally {
            setIsLoading(false)
        }

 
    }

    return (
        <>
            <header className="page-heading">
                <div className="context-bar">
                    <p>WORKSPACE / TRANSFER LAB</p>
                    <p>Demo GW {currentGameweek} / Nick</p>
                </div>

                <h1>Make a move with a reason.</h1>

                <p>
                    Compare gains, costs and minutes risk before changing your squad.
                </p>
            </header>
            <div className="recommendation-settings">
                <div>
                    <label htmlFor="1">Current Gameweek: </label>
                    <input 
                    type="number" 
                    value={currentGameweek} 
                    onChange={(event) => {
                        setCurrentGameweek(event.target.value);
                        setRecommendation(null);
                        setError(null);
                    }}
                    disabled={isLoading}
                    id="1"/>
                </div>
                <div>
                    <label htmlFor="2">Free Transfers: </label>
                    <input 
                    type="number" 
                    value={freeTransfers} 
                    onChange={(event) => {
                        setFreeTransfers(event.target.value);
                        setRecommendation(null);
                        setError(null);
                    }}
                    disabled={isLoading}
                    id="2"/>
                </div>
                <div>
                    <label htmlFor="3">Bank (£m): </label>
                    <input 
                    type="number" 
                    step={"0.1"}
                    value={bankMillions} 
                    onChange={(event) => {
                        setBankMillions(event.target.value);
                        setRecommendation(null);
                        setError(null);
                    }}
                    disabled={isLoading}
                    id="3"/>
                </div>
            </div>

            <button
                className="forge-button recommendation-submit"
                onClick={handleGetRecommendation}
                disabled={isLoading || selectedPlayers.length !== 15}
            >
                {isLoading ? "Loading..." : "Recommend Transfer"}
            </button>

            {isLoading && (
                <div
                    className="forge-state forge-state--loading"
                    role="status"
                >
                    <strong className="forge-state-title">
                        Comparing transfer options…
                    </strong>
                    <p>Your recommendation will appear here when it is ready.</p>
                </div>
            )}

            {!recommendation && !isLoading && !error && (
                <div className="forge-state forge-state--empty">
                    <strong className="forge-state-title">
                        Your recommendation will appear here.
                    </strong>
                    <p>
                        {selectedPlayers.length !== 15
                            ? "Complete your 15-player squad on My Squad to get started."
                            : "Check your settings, then select Recommend Transfer."}
                    </p>
                </div>
            )}

            {recommendation && (
            <section className="recommendation-result">
                <section className="transfer-card">
                    <p className="transfer-label">SUGGESTED MOVES</p>

                    {recommendedTransfers.length > 0 ? (
                        <ul className="transfer-moves">
                            {recommendedTransfers.map((move, index) => (
                                <li
                                    className="transfer-move"
                                    key={`${move.player_out.player_id}-${move.player_in.player_id}`}
                                >
                                    <p className="transfer-label">
                                        MOVE / {String(index + 1).padStart(2, "0")}
                                    </p>

                                    <div className="transfer-pair">
                                        <div className="transfer-player transfer-player--sell">
                                            <p className="transfer-label">SELL</p>
                                            <h2>{move.player_out.name}</h2>

                                            <p className="transfer-description">
                                                {move.player_out.position}
                                                {" · "}
                                                {move.player_out.team_name ?? "Unknown team"}
                                                {" · Selling value £"}
                                                {(move.player_out.price_tenths / 10).toFixed(1)}m
                                            </p>
                                        </div>

                                        <div className="transfer-player transfer-player--buy">
                                            <p className="transfer-label">BUY</p>
                                            <h2>{move.player_in.name}</h2>

                                            <p className="transfer-description">
                                                {move.player_in.position}
                                                {" · "}
                                                {move.player_in.team_name ?? "Unknown team"}
                                                {" · Purchase cost £"}
                                                {(move.player_in.price_tenths / 10).toFixed(1)}m
                                            </p>
                                        </div>
                                    </div>

                                    <p className="transfer-description transfer-score-detail">
                                        Player scores: {move.player_out.score.toFixed(2)}
                                        {" → "}
                                        {move.player_in.score.toFixed(2)}
                                        {" · Score gain: "}
                                        {move.score_gain.toFixed(2)}
                                    </p>
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p className="forge-state forge-state--empty">
                            {recommendation.recommended_strategy === "no_transfer"
                                ? "Keep your current squad. No transfers recommended."
                                : "Transfer details are unavailable."}
                        </p>
                    )}

                    <div className="transfer-outcomes">
                        <div>
                            <p className="transfer-label">GROSS SCORE GAIN</p>
                            <p className="transfer-metric">
                                {recommendation.recommended_strategy === "no_transfer"
                                    ? "0.00"
                                    : (
                                        recommendation.recommended_strategy === "single_transfer"
                                            ? recommendation.single_transfer?.raw_score_gain
                                            : recommendation.double_transfer?.raw_score_gain
                                    )?.toFixed(2) ?? "—"}
                            </p>
                        </div>

                        <div>
                            <p className="transfer-label">TRANSFER COST</p>
                            <p className="transfer-metric">
                                {recommendation.recommended_strategy === "no_transfer"
                                    ? 0
                                    : (
                                        recommendation.recommended_strategy === "single_transfer"
                                            ? recommendation.single_transfer?.transfer_cost
                                            : recommendation.double_transfer?.transfer_cost
                                    ) ?? "—"}
                            </p>
                        </div>

                        <div>
                            <p className="transfer-label">NET SCORE GAIN</p>
                            <p className="transfer-metric">
                                {recommendation.best_net_score_gain.toFixed(2)}
                            </p>
                        </div>

                        <div>
                            <p className="transfer-label">BANK AFTER</p>
                            <p className="transfer-metric">
                                {remainingBankTenths !== null
                                    ? `£${(remainingBankTenths / 10).toFixed(1)}m`
                                    : "—"}
                            </p>
                        </div>
                    </div>
                </section>

                <div className="recommendation-panels">
                    <section className="recommendation-panel">
                        <h2>Why it ranks first</h2>

                        <p className="panel-description">
                            {recommendation.reason.summary}
                        </p>

                        <p className="panel-description">
                            {recommendation.reason.decision_detail}
                        </p>

                        <div className="panel-method">
                            <p>
                                Strategy: {strategyLabels[recommendation.recommended_strategy]}
                            </p>
                            <p>
                                Net score gain: {recommendation.best_net_score_gain.toFixed(2)}
                            </p>
                            <p>Method: transparent baseline v0.1</p>
                            <p>Fantasy metadata: user-confirmed demo values</p>
                        </div>

                        <p className="transfer-label">
                            AI EXPLANATIONS · LATER PHASE
                        </p>

                        <p className="panel-description">
                            Evidence stays visible before a conversational layer is added.
                        </p>
                    </section>

                    <section className="recommendation-panel">
                        <h2>Other options</h2>

                        <div className="strategy-table-wrapper">
                            <table className="strategy-table">
                                <thead>
                                    <tr>
                                        <th scope="col">Strategy</th>
                                        <th scope="col">Gross gain</th>
                                        <th scope="col">Cost</th>
                                        <th scope="col">Net gain</th>
                                    </tr>
                                </thead>

                                <tbody>
                                    <tr>
                                        <th scope="row">No transfer</th>
                                        <td>0.00</td>
                                        <td>0</td>
                                        <td>0.00</td>
                                    </tr>

                                    <tr>
                                        <th scope="row">Single</th>
                                        <td>
                                            {recommendation.single_transfer?.raw_score_gain.toFixed(2) ?? "—"}
                                        </td>
                                        <td>
                                            {recommendation.single_transfer?.transfer_cost ?? "—"}
                                        </td>
                                        <td>
                                            {recommendation.single_transfer?.net_score_gain.toFixed(2) ?? "—"}
                                        </td>
                                    </tr>

                                    <tr>
                                        <th scope="row">Double</th>
                                        <td>
                                            {recommendation.double_transfer?.raw_score_gain.toFixed(2) ?? "—"}
                                        </td>
                                        <td>
                                            {recommendation.double_transfer?.transfer_cost ?? "—"}
                                        </td>
                                        <td>
                                            {recommendation.double_transfer?.net_score_gain.toFixed(2) ?? "—"}
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>

                        <p className="panel-note">
                            — means no transfer option was found for that strategy.
                        </p>

                        <button
                            type="button"
                            className="forge-button draft-placeholder"
                            disabled
                        >
                            Save as draft
                        </button>

                        <p className="panel-note">
                            No changes are sent to FPL.
                        </p>
                    </section>
                </div>

                <p className="transfer-footnote">
                    Prices and budget calculations currently use demo values.
                </p>
            </section>
            )}            
            {error && (
                <p
                    className="forge-state forge-state--error"
                    role="alert"
                >
                    {error}
                </p>
            )}
        </>
    )
}