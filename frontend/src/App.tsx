import { useState, useEffect } from "react";
import type { Player } from "./types/player";
import { Navigate, Route, Routes, NavLink } from "react-router";
import SquadPage from "./pages/SquadPage";
import RecommendationPage from "./pages/RecommendationPage";
import "./App.css"
import PlayerExplorerPage from "./pages/PlayerExplorerPage";
import FixturePlannerPage from "./pages/FixturePlannerPage";
import OverviewPage from "./pages/OverviewPage";


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
        <div className="app-layout">
            <header className="app-header">
                <div className="header-brand"><img src="/figma/forge-mark.svg" alt="" />FPL FORGE</div>
                <nav className="header-nav" aria-label="Main navigation">
                    <NavLink to="/overview" onClick={() => setError(null)}>Overview</NavLink>
                    <NavLink to="/player-explorer" onClick={() => setError(null)}><span className="desktop-label">Player explorer</span><span className="mobile-label">Players</span></NavLink>
                    <NavLink to="/fixture-planner" onClick={() => setError(null)}><span className="desktop-label">Fixture planner</span><span className="mobile-label">Fixtures</span></NavLink>
                    <NavLink to="/squad" onClick={() => setError(null)}><span className="desktop-label">My squad</span><span className="mobile-label">Squad</span></NavLink>
                    <NavLink to="/transfer-lab" onClick={() => setError(null)}><span className="desktop-label">Transfer lab</span><span className="mobile-label">Transfers</span></NavLink>
                </nav>
                <div className="header-account"><span className="eyebrow">GW {currentGameweek.padStart(2, "0")} / DEMO</span><span className="account-avatar">N</span></div>
            </header>

            <main className="app-main">
                <Routes>
                    <Route
                        path="/"
                        element={<Navigate to="/squad" replace />}
                    />

                    <Route
                        path="/overview"
                        element={<OverviewPage />}
                    />

                    <Route
                        path="/fixture-planner"
                        element={<FixturePlannerPage />}
                    />

                    <Route
                        path="/player-explorer"
                        element={<PlayerExplorerPage />}
                    />

                    <Route
                        path="/squad"
                        element={
                            <>
                                {error && (
                                    <p
                                        className="forge-state forge-state--error"
                                        role="alert"
                                    >
                                        {error}
                                    </p>
                                )}

                                <SquadPage
                                    selectedPlayers={selectedPlayers}
                                    onAddPlayer={handleAddPlayer}
                                    onRemovePlayer={handleRemovePlayer}
                                    bankMillions={bankMillions}
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
                <footer className="page-footer"><span>FPL FORGE / FIELDWORK</span><span>ILLUSTRATIVE CONTENT · DESIGN CONCEPT</span></footer>
            </main>
        </div>
    );
}