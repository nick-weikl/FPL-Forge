import { useState, useEffect, useMemo } from "react";
import type { Player } from "./types/player";
import { Navigate, Route, Routes, NavLink, useLocation } from "react-router";
import SquadPage from "./pages/SquadPage";
import RecommendationPage from "./pages/RecommendationPage";
import "./App.css"
import PlayerExplorerPage from "./pages/PlayerExplorerPage";
import FixturePlannerPage from "./pages/FixturePlannerPage";
import OverviewPage from "./pages/OverviewPage";
import { useDashboard } from "./hooks/useDashboard";
import DataState from "./components/DataState";
import { reconcilePlayers } from "./utils/squad";
import { importedTeamMetadata, readImportedTeam } from "./utils/teamImport";
import type { ImportedTeam, TeamImportPreview } from "./types/teamImport";


function readSavedInput(key: string, fallback: string): string {
    try {
        return localStorage.getItem(key) ?? fallback;
    } catch {
        return fallback;
    }
}

export default function App() {
    const location = useLocation();
    const [lookback, setLookback] = useState(5);
    const {data, loading, error: dataError, retry} = useDashboard(lookback);
    const [importedTeam, setImportedTeam] = useState<ImportedTeam | null>(readImportedTeam);
    const [error, setError] = useState<string | null>(null);
    const [gameweekOverride, setCurrentGameweek] = useState<string>(
        () => readSavedInput("fpl-forge-gameweek", "")
    );

    const [freeTransfers, setFreeTransfers] = useState<string>(
        () => readSavedInput("fpl-forge-free-transfers", "1")
    );

    const [bankMillions, setBankMillions] = useState<string>(
        () => readSavedInput("fpl-forge-bank", "1.0")
    );

    const [savedPlayers, setSelectedPlayers] = useState<Player[]>(() => {
        try {
            const savedSquad = localStorage.getItem("fpl-forge-squad");

            if (savedSquad === null) {
                return [];
            }

            const parsedSquad: unknown = JSON.parse(savedSquad);

            return Array.isArray(parsedSquad) ? parsedSquad.filter((player): player is Player =>
                player !== null && typeof player === "object" && typeof player.id === "number" && Number.isInteger(player.id)
            ) : [];
        } catch {
            return [];
        }
    });

    const currentGameweek = gameweekOverride || (data?.latest_completed_gameweek?.toString() ?? "");
    const selectedPlayers = useMemo(() => {
        return reconcilePlayers(savedPlayers, data?.players);
    }, [data, savedPlayers]);

    useEffect(() => {
        if (!data) return;
        try { localStorage.setItem("fpl-forge-squad", JSON.stringify(selectedPlayers)); }
        catch (error) { console.error("Could not save squad", error); }
    }, [data, selectedPlayers]);

    useEffect(() => {
        try {
            if (currentGameweek) localStorage.setItem("fpl-forge-gameweek", currentGameweek);
            localStorage.setItem("fpl-forge-free-transfers", freeTransfers);
            localStorage.setItem("fpl-forge-bank", bankMillions);
        } catch (error) {
            console.error("Could not save transfer settings", error);
        }
    }, [currentGameweek, freeTransfers, bankMillions]);


    useEffect(() => {
        try { localStorage.setItem("fpl-forge-import", JSON.stringify(importedTeam)); }
        catch (error) { console.error("Could not save import details", error); }
    }, [importedTeam]);

    function handleTeamImport(preview: TeamImportPreview) {
        setSelectedPlayers(preview.players);
        setBankMillions((preview.bank_tenths / 10).toFixed(1));
        if (preview.analysis_gameweek !== null) setCurrentGameweek(preview.analysis_gameweek.toString());
        setImportedTeam(importedTeamMetadata(preview));
        setError(null);
    }

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

        setImportedTeam(previous => previous ? {...previous, edited: true} : null);
        setSelectedPlayers((previousPlayers) => {
            const currentPlayers = reconcilePlayers(previousPlayers, data?.players);
            const alreadySelected = currentPlayers.some(
                (selectedPlayer) => selectedPlayer.id === player.id
            );

            if (alreadySelected || currentPlayers.length >= 15) {
                return currentPlayers
            }

            return [...currentPlayers, player]
        })
    }


    function handleRemovePlayer(playerId: number) {
        setError(null)
        setImportedTeam(previous => previous ? {...previous, edited: true} : null);
        setSelectedPlayers((previousPlayers) => {
            const remainingPlayers = reconcilePlayers(previousPlayers, data?.players).filter(
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
                <div className="header-account"><span className="eyebrow">{data ? `${data.season} / DATA GW ${data.latest_completed_gameweek ?? "—"}` : "CONNECTING"}</span><span className="account-avatar">N</span></div>
            </header>

            <main className="app-main">
                <DataState loading={loading} error={dataError} retry={retry} />
                {data && savedPlayers.length !== selectedPlayers.length && <p className="forge-state" role="status">Unavailable saved players have been excluded. Review your current squad.</p>}
                {error && location.pathname === "/player-explorer" && <p className="forge-state forge-state--error" role="alert">{error}</p>}
                {data && <Routes>
                    <Route
                        path="/"
                        element={<Navigate to="/squad" replace />}
                    />

                    <Route
                        path="/overview"
                        element={<OverviewPage data={data} selectedPlayers={selectedPlayers} currentGameweek={currentGameweek} freeTransfers={freeTransfers} bankMillions={bankMillions} />}
                    />

                    <Route
                        path="/fixture-planner"
                        element={<FixturePlannerPage data={data} />}
                    />

                    <Route
                        path="/player-explorer"
                        element={<PlayerExplorerPage data={data} lookback={lookback} setLookback={setLookback} selectedPlayers={selectedPlayers} onAddPlayer={handleAddPlayer} />}
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
                                    bankMillions={bankMillions}
                                    setBankMillions={setBankMillions}
                                    importedTeam={importedTeam}
                                    onImport={handleTeamImport}
                                    availablePlayers={data.players}
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
                </Routes>}
                <footer className="page-footer"><span>FPL FORGE / FIELDWORK</span><span>{data ? `DATABASE DATA / ${data.season} / THROUGH GW ${data.latest_completed_gameweek ?? "—"}` : "DATABASE CONNECTION REQUIRED"}</span></footer>
            </main>
        </div>
    );
}
