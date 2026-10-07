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
            <h1>FPL Forge</h1>
            <section>
                <h2>Selected squad</h2>
                <p>{selectedPlayers.length} / 15 players selected</p>

                <Link to="/squad" onClick={() => setError(null)}>
                    Edit squad
                </Link>

                {selectedPlayers.length !== 15 && (
                    <p>Select all 15 players before requesting a recommendation.</p>
                )}

                {selectedPlayers.length > 0 && (
                    <details>
                        <summary>View selected players</summary>

                        <ul>
                            {selectedPlayers.map((player) => (
                                <li key={player.id}>
                                    {player.name}
                                    {" — "}
                                    {player.team_name ?? "Unknown team"}
                                    {" — "}
                                    {player.position}
                                </li>
                            ))}
                        </ul>
                    </details>
                )}
            </section>
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

            {recommendation && (
            <section className="recommendation-result">
                <p>
                    Strategy: {strategyLabels[recommendation.recommended_strategy]}
                </p>

                <p>
                    Net score gain: {recommendation.best_net_score_gain.toFixed(2)}
                </p>

                <p>{recommendation.reason.summary}</p>
                <p>{recommendation.reason.decision_detail}</p>

                <h3>Strategy comparison</h3>

                    <table>
                        <thead>
                            <tr>
                                <th scope="col">Strategy</th>
                                <th scope="col">Raw score gain</th>
                                <th scope="col">Transfer cost</th>
                                <th scope="col">Net score gain</th>
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
                                <th scope="row">Single transfer</th>
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
                                <th scope="row">Double transfer</th>
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

                    <p>— means no transfer option was found for that strategy.</p>

                <h2>Recommended moves</h2>

                {recommendedTransfers.length > 0 ? (
                    <ul>
                        {recommendedTransfers.map((move) => (
                            <li
                                key={`${move.player_out.player_id}-${move.player_in.player_id}`}
                            >
                                <p>
                                    <strong>Sell:</strong> {move.player_out.name}
                                    {" — "}{move.player_out.team_name ?? "Unknown team"}
                                    {" — "}{move.player_out.position}
                                    {" — £"}
                                    {(move.player_out.price_tenths / 10).toFixed(1)}m
                                </p>

                                <p>
                                    <strong>Buy:</strong> {move.player_in.name}
                                    {" — "}{move.player_in.team_name ?? "Unknown team"}
                                    {" — "}{move.player_in.position}
                                    {" — £"}
                                    {(move.player_in.price_tenths / 10).toFixed(1)}m
                                </p>

                                <p>
                                    Player scores: {move.player_out.score.toFixed(2)}
                                    {" → "}{move.player_in.score.toFixed(2)}
                                </p>

                                <p>Score gain: {move.score_gain.toFixed(2)}</p>
                            </li>
                        ))}
                    </ul>
                ) : (
                    <p>
                        {recommendation.recommended_strategy === "no_transfer"
                            ? "Keep your current squad. No transfers recommended."
                            : "Transfer details are unavailable."}
                    </p>
                )}

                {remainingBankTenths !== null && (
                    <p>
                        Bank after transfers: £
                        {(remainingBankTenths / 10).toFixed(1)}m
                    </p>
                )}

                <p>Prices and budget calculations currently use demo values.</p>
            </section>
            )}            
            {error && (
                <div>
                    <p role="alert">{error}</p>
                </div>
            )}
            <button 
            onClick={handleGetRecommendation}
            disabled={isLoading || selectedPlayers.length !== 15}>
                {isLoading ? "Loading..." : "Recommend Transfer"}
            </button>
        </>
    )
}