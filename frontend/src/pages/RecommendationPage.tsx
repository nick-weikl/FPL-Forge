import {getTransferStrategy} from "../services/api.ts"
import { useState, useEffect } from "react"
import type { StrategyRequest, StrategyResponse } from "../types/recommendation.ts"
import type { Player } from "../types/player.ts";
import PlayerPicker from "../components/PlayerPicker.tsx";


export default function RecommendationPage() {
    const [recommendation, setRecommendation] = useState<StrategyResponse | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [currentGameweek, setCurrentGameweek] = useState<string>("2");
    const [freeTransfers, setFreeTransfers] = useState<string>("1");
    const [bankMillions, setBankMillions] = useState<string>("1.0")
    const strategyLabels: Record<string, string> = {
        single_transfer: "Single transfer",
        double_transfer: "Double transfer",
        no_transfer: "Keep current squad",
    };
    const [selectedPlayers, setSelectedPlayers] = useState<Player[]>(() => {
        try {
            const savedSquad = localStorage.getItem("fpl-forge-squad");

            if (savedSquad === null) {
                return [];
            }

            const parsedSquad: unknown = JSON.parse(savedSquad);

            return Array.isArray(parsedSquad) ? parsedSquad : [];
        } catch {
            return [];
        }
    });

    useEffect(() => {
        try {
            localStorage.setItem(
                "fpl-forge-squad",
                JSON.stringify(selectedPlayers)
            );
        } catch (error) {
            console.error("Could not save squad", error);
        }
    }, [selectedPlayers]);

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


    function handleAddPlayer(player: Player) {
        setRecommendation(null)
        setError(null)

        const playersFromTeam = selectedPlayers.filter(
            (selectedPlayer) => selectedPlayer.team_id === player.team_id
        ).length;

        if (playersFromTeam >= 3) {
            setError(`You already have 3 players from ${player.team_name}.`);
            return;
        }

        const positionLimits: Record<string, number> = {
            Goalkeeper: 2,
            Defender: 5,
            Midfielder: 5,
            Attacker: 3,
        };

        const playersInPosition = selectedPlayers.filter(
            (selectedPlayer) => selectedPlayer.position === player.position
        ).length;

        if (playersInPosition >= positionLimits[player.position]) {
            setError(`You have reached the limit for ${player.position} players.`);
            return;
        }

        setSelectedPlayers((previousPlayers) => {
            const alreadySelected = previousPlayers.some(
                (selectedPlayer) => selectedPlayer.id === player.id
            );

            if (alreadySelected || previousPlayers.length >= 15) {
                return previousPlayers
            }

            return [...previousPlayers, player]
        })
    }


    function handleRemovePlayer(playerId: number) {
        setRecommendation(null)
        setError(null)
        setSelectedPlayers((previousPlayers) => {
            const remainingPlayers = previousPlayers.filter(
                (selectedPlayer) => selectedPlayer.id !== playerId
            );

            return remainingPlayers;
        });
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

            console.log(result)
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
            <label htmlFor="1">Current Gameweek</label>
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
            <label htmlFor="2">Free Transfers</label>
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
            <label htmlFor="3">Enter the current value of your bank £m</label>
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
            {recommendation && (
                <div>
                <p>Strategy: {strategyLabels[recommendation.recommended_strategy] ?? recommendation.recommended_strategy}</p>
                <p>Net Score Gain: {recommendation.best_net_score_gain}</p>
                <p>Reason for strategy: {recommendation.reason.summary}</p>
                <p>Details on Reason: {recommendation.reason.decision_detail}</p>
                <h2>Recommended moves</h2>
                {recommendation.reason.recommended_moves.length > 0 ? (
                    <ul>
                        {recommendation.reason.recommended_moves.map((move) => (
                            <li key={`${move.player_out}-${move.player_in}`}>
                                {move.player_out} → {move.player_in}
                            </li>
                        ))}
                    </ul>
                ) : (
                    <p>No player changes recommended.</p>
                )}
                </div>
            )}
            {error && (
                <div>
                    <p role="alert">{error}</p>
                </div>
            )}
            <button 
            onClick={handleGetRecommendation}
            disabled={isLoading}>
                {isLoading ? "Loading..." : "Recommend Transfer"}
            </button>
            <section>
                <h2>Squad: {selectedPlayers.length} / 15</h2>
                <div>
                    <p>Goalkeepers: {goalkeeperCount} / 2</p>
                    <p>Defenders: {defenderCount} / 5</p>
                    <p>Midfielders: {midfielderCount} / 5</p>
                    <p>Attackers: {attackerCount} / 3</p>
                </div>

                {selectedPlayers.length === 0 ? (
                    <p>Add players using the picker below.</p>
                ) : (
                    <ul>
                        {selectedPlayers.map((player) => (
                            <li key={player.id}>
                                {player.name} — {player.team_name ?? "Unknown team"} — {player.position}
                                {" — £"}{(player.price_tenths / 10).toFixed(1)}m
                                <button
                                    type="button"
                                    onClick={() => handleRemovePlayer(player.id)}
                                    disabled={isLoading}
                                >
                                    Remove
                                </button>
                            </li>
                        ))}
                    </ul>
                )}
            </section>
            <PlayerPicker
                selectedPlayers={selectedPlayers}
                onAddPlayer={handleAddPlayer}
                onRemovePlayer={handleRemovePlayer}
                disabled={isLoading}
            />
        </>
    )
}