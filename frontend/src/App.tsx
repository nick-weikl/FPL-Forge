import { useState, useEffect } from "react";
import type { Player } from "./types/player";
import { Link, Navigate, Route, Routes } from "react-router";
import SquadPage from "./pages/SquadPage";
import RecommendationPage from "./pages/RecommendationPage";


function readSavedInput(key: string, fallback: string): string {
    try {
        return localStorage.getItem(key) ?? fallback;
    } catch {
        return fallback;
    }
}

export default function App() {
    const [error, setError] = useState<string | null>(null);
    const [currentGameweek, setCurrentGameweek] = useState<string>(
        () => readSavedInput("fpl-forge-gameweek", "2")
    );

    const [freeTransfers, setFreeTransfers] = useState<string>(
        () => readSavedInput("fpl-forge-free-transfers", "1")
    );

    const [bankMillions, setBankMillions] = useState<string>(
        () => readSavedInput("fpl-forge-bank", "1.0")
    );

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
            localStorage.setItem("fpl-forge-gameweek", currentGameweek);
            localStorage.setItem("fpl-forge-free-transfers", freeTransfers);
            localStorage.setItem("fpl-forge-bank", bankMillions);
        } catch (error) {
            console.error("Could not save transfer settings", error);
        }
    }, [currentGameweek, freeTransfers, bankMillions]);


    function handleAddPlayer(player: Player) {
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
        setError(null)
        setSelectedPlayers((previousPlayers) => {
            const remainingPlayers = previousPlayers.filter(
                (selectedPlayer) => selectedPlayer.id !== playerId
            );

            return remainingPlayers;
        });
    }


    return (
        <>
            <nav aria-label="Main navigation">
                <Link to="/squad" onClick={() => setError(null)}>
                    My Squad
                </Link>
                {" | "}
                <Link to="/transfer-lab" onClick={() => setError(null)}>
                    Transfer Lab
                </Link>
            </nav>

            <Routes>
                <Route
                    path="/"
                    element={<Navigate to="/squad" replace />}
                />

                <Route
                    path="/squad"
                    element={
                        <>
                            {error && <p role="alert">{error}</p>}

                            <SquadPage
                                selectedPlayers={selectedPlayers}
                                onAddPlayer={handleAddPlayer}
                                onRemovePlayer={handleRemovePlayer}
                                disabled={false}
                            />
                        </>
                    }
                />

                <Route
                    path="/transfer-lab"
                    element={
                        <RecommendationPage
                          selectedPlayers={selectedPlayers}
                          error={error}
                          setError={setError}
                          currentGameweek={currentGameweek}
                          setCurrentGameweek={setCurrentGameweek}
                          freeTransfers={freeTransfers}
                          setFreeTransfers={setFreeTransfers}
                          bankMillions={bankMillions}
                          setBankMillions={setBankMillions}
                      />
                    }
                />
            </Routes>
        </>
    );
}