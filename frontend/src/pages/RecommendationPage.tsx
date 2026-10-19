import {getTransferStrategy} from "../services/api.ts"
import { useState } from "react"
import type { StrategyRequest, StrategyResponse } from "../types/recommendation.ts"
import type { Player } from "../types/player.ts";
import "./RecommendationPage.css"
import type { Dispatch, SetStateAction } from "react";


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

    let remainingBankTenths: number | null = null;

    if (
        recommendation?.recommended_strategy === "single_transfer" &&
        recommendation.single_transfer
    ) {
        const transfer = recommendation.single_transfer.transfer;

        remainingBankTenths = transfer.remaining_bank_tenths;
    } else if (
        recommendation?.recommended_strategy === "double_transfer" &&
        recommendation.double_transfer
    ) {
        const pair = recommendation.double_transfer.transfer_pair;

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
        <div className="recommendation-page page-stack">
            <div className="recommendation-heading">
                <header className="page-heading">
                    <p className="eyebrow">TRANSFER LAB / GAMEWEEK {currentGameweek.padStart(2, "0")}</p>
                    <h1>One decision.<br />Three ways forward.</h1>
                    <p>Compare the moves and their cost before you commit.</p>
                </header>
                <section className="starting-point panel">
                    <p className="eyebrow">YOUR STARTING POINT</p>
                    <div className="metrics">
                        <div><p className="eyebrow">SQUAD</p><p className="metric-value">{selectedPlayers.length} / 15</p></div>
                        <div><p className="eyebrow">BANK</p><p className="metric-value">£{bankMillions || "—"}m</p></div>
                        <div><p className="eyebrow">TRANSFERS</p><p className="metric-value">{freeTransfers || "—"} free</p></div>
                    </div>
                </section>
            </div>
            <div className="recommendation-settings">
                <div className="recommendation-fields">
                    <label className="field" htmlFor="gameweek"><span className="eyebrow">CURRENT GAMEWEEK</span><input type="number" value={currentGameweek} onChange={(event) => { setCurrentGameweek(event.target.value); setRecommendation(null); setError(null); }} disabled={isLoading} id="gameweek" /></label>
                    <label className="field" htmlFor="free-transfers"><span className="eyebrow">FREE TRANSFERS</span><input type="number" value={freeTransfers} onChange={(event) => { setFreeTransfers(event.target.value); setRecommendation(null); setError(null); }} disabled={isLoading} id="free-transfers" /></label>
                    <label className="field" htmlFor="bank"><span className="eyebrow">BANK / £m</span><input type="number" step="0.1" value={bankMillions} onChange={(event) => { setBankMillions(event.target.value); setRecommendation(null); setError(null); }} disabled={isLoading} id="bank" /></label>
                </div>
                <button className="forge-button recommendation-submit" onClick={handleGetRecommendation} disabled={isLoading || selectedPlayers.length !== 15}>{isLoading ? "Analysing…" : "Run analysis"}</button>
            </div>
            {isLoading && <div className="forge-state forge-state--loading" role="status"><strong className="forge-state-title">Comparing transfer options…</strong><p>Your recommendation will appear here when it is ready.</p></div>}
            {!recommendation && !isLoading && !error && <div className="forge-state forge-state--empty"><strong className="forge-state-title">Your recommendation will appear here.</strong><p>{selectedPlayers.length !== 15 ? "Complete your 15-player squad on My Squad to get started." : "Check your settings, then select Run analysis."}</p></div>}
            {error && <p className="forge-state forge-state--error" role="alert">{error}</p>}
            {recommendation && <>
                <section className="strategy-board" aria-label="Transfer strategy comparison">
                    {([
                        { key: "no_transfer", label: "00 / NO TRANSFER", raw: 0, net: 0, cost: 0, moves: [], available: true },
                        { key: "single_transfer", label: "01 / SINGLE TRANSFER", raw: recommendation.single_transfer?.raw_score_gain, net: recommendation.single_transfer?.net_score_gain, cost: recommendation.single_transfer?.transfer_cost, moves: recommendation.single_transfer ? [recommendation.single_transfer.transfer] : [], available: !!recommendation.single_transfer },
                        { key: "double_transfer", label: "02 / DOUBLE TRANSFER", raw: recommendation.double_transfer?.raw_score_gain, net: recommendation.double_transfer?.net_score_gain, cost: recommendation.double_transfer?.transfer_cost, moves: recommendation.double_transfer?.transfer_pair.transfers ?? [], available: !!recommendation.double_transfer },
                    ]).map(strategy => <article key={strategy.key} className={`strategy-card panel${recommendation.recommended_strategy === strategy.key ? " strategy-card--best" : ""}${strategy.key === "no_transfer" ? " strategy-card--hold" : ""}`}>
                        <p className="eyebrow strategy-label">{strategy.label}{recommendation.recommended_strategy === strategy.key && " · BEST"}</p>
                        <p className="strategy-gain">{strategy.net == null ? "—" : `${strategy.net > 0 ? "+" : ""}${strategy.net.toFixed(2)}`}</p>
                        <p className="eyebrow strategy-gain-label">NET FORGE SCORE GAIN</p>
                        <hr className="rule" />
                        <div className="strategy-moves">
                            {strategy.key === "no_transfer" ? <><h2>Keep your current squad.</h2><p className="muted">Carry the same 15 into the next gameweek.</p></> : strategy.available ? <>{strategy.moves.map((move, index) => <p className={index === 0 ? "strategy-move-title" : "muted"} key={`${move.player_out.player_id}-${move.player_in.player_id}`}><span>{move.player_out.name}</span><span className="move-arrow" aria-label="to"> → </span><span>{move.player_in.name}</span></p>)}{strategy.key === "single_transfer" && <p className="muted">One change.{recommendation.recommended_strategy === "single_transfer" ? " The strongest net gain." : " Compare the net gain."}</p>}</> : <><h2>No available move.</h2><p className="muted">No transfer option was found for this strategy.</p></>}
                        </div>
                        <hr className="rule" />
                        <div className="metrics strategy-costs">
                            <div><p className="eyebrow">RAW GAIN</p><p className="metric-value">{strategy.raw == null ? "—" : `${strategy.raw > 0 ? "+" : ""}${strategy.raw.toFixed(2)}`}</p></div>
                            <div><p className="eyebrow">TRANSFER HIT</p><p className="metric-value">{strategy.cost == null ? "—" : `${strategy.cost > 0 ? "−" : ""}${strategy.cost} pts`}</p></div>
                        </div>
                    </article>)}
                </section>
                <section className="decision-explanation">
                    <div><p className="eyebrow accent">WHY {recommendation.recommended_strategy === "single_transfer" ? "SINGLE WINS" : recommendation.recommended_strategy === "double_transfer" ? "DOUBLE WINS" : "HOLD WINS"}</p><h2>{recommendation.reason.summary}</h2></div>
                    <div><p>{recommendation.reason.decision_detail}</p><p className="small-note">{remainingBankTenths !== null ? `Bank after recommended strategy: £${(remainingBankTenths / 10).toFixed(1)}m / ` : ""}{strategyLabels[recommendation.recommended_strategy]} / Demo prices and budget values</p></div>
                </section>
            </>}
        </div>
    );
}
