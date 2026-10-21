import { useState, useEffect, useMemo, useSyncExternalStore } from "react";
import ThemeControl from "./components/ThemeControl";
import GettingStarted from "./components/GettingStarted";
import HelpPage from "./pages/HelpPage";
import {
  readStored,
  saveStored,
  storageUnavailable,
  storageRecovery,
  readJSONStored,
  subscribeStorageIssue,
} from "./utils/storage";
import type { SquadBackup } from "./utils/backup";
import type { Player } from "./types/player";
import { Navigate, Route, Routes, NavLink, Link, useLocation } from "react-router";
import SquadPage from "./pages/SquadPage";
import RecommendationPage from "./pages/RecommendationPage";
import "./App.css";
import PlayerExplorerPage from "./pages/PlayerExplorerPage";
import FixturePlannerPage from "./pages/FixturePlannerPage";
import OverviewPage from "./pages/OverviewPage";
import { useDashboard } from "./hooks/useDashboard";
import DataState from "./components/DataState";
import { readLineup, reconcileLineup } from "./utils/lineup";
import type { Lineup } from "./utils/lineup";
import { reconcilePlayers } from "./utils/squad";
import { importedTeamMetadata, readImportedTeam } from "./utils/teamImport";
import type { ImportedTeam, TeamImportPreview } from "./types/teamImport";

export default function App() {
  const location = useLocation();
  const [savedLineup, setLineup] = useState<Lineup>(() =>
    readLineup(readJSONStored("fpl-forge-lineup", "null")),
  );
  const [lookback, setLookback] = useState(5);
  const { data, loading, error: dataError, retry } = useDashboard(lookback);
  const [importedTeam, setImportedTeam] = useState<ImportedTeam | null>(readImportedTeam);
  const [error, setError] = useState<string | null>(null);
  const [gameweekOverride, setCurrentGameweek] = useState<string>(() =>
    readStored("fpl-forge-gameweek", ""),
  );

  const [freeTransfers, setFreeTransfers] = useState<string>(() =>
    readStored("fpl-forge-free-transfers", "1"),
  );

  const [bankMillions, setBankMillions] = useState<string>(() =>
    readStored("fpl-forge-bank", "0.0"),
  );

  const [savedPlayers, setSelectedPlayers] = useState<Player[]>(() => {
    try {
      const savedSquad = readJSONStored("fpl-forge-squad", "null");

      if (savedSquad === null) {
        return [];
      }

      const parsedSquad: unknown = JSON.parse(savedSquad);

      return Array.isArray(parsedSquad)
        ? parsedSquad.filter(
            (player): player is Player =>
              player !== null &&
              typeof player === "object" &&
              typeof player.id === "number" &&
              Number.isInteger(player.id),
          )
        : [];
    } catch {
      return [];
    }
  });

  const storageWarning = useSyncExternalStore(
    subscribeStorageIssue,
    storageUnavailable,
    () => false,
  );
  const recoveredData = useSyncExternalStore(subscribeStorageIssue, storageRecovery, () => false);
  const [guideHidden, setGuideHidden] = useState(
    () => readStored("fpl-forge-guide-hidden", "false") === "true",
  );
  const [sellingPrices, setSellingPrices] = useState<Record<number, string>>(() => {
    try {
      const value: unknown = JSON.parse(readJSONStored("fpl-forge-selling-values", "{}"));
      return value && typeof value === "object" && !Array.isArray(value)
        ? Object.fromEntries(
            Object.entries(value).filter(
              ([key, price]) => /^[1-9]\d*$/.test(key) && typeof price === "string",
            ),
          )
        : {};
    } catch {
      return {};
    }
  });
  useEffect(() => {
    saveStored("fpl-forge-selling-values", JSON.stringify(sellingPrices));
  }, [sellingPrices]);
  useEffect(() => {
    const names: Record<string, string> = {
      "/squad": "My Squad",
      "/overview": "Overview",
      "/player-explorer": "Players",
      "/fixture-planner": "Fixtures",
      "/transfer-lab": "Transfer Lab",
      "/help": "Help",
    };
    document.title = `${names[location.pathname] ?? "FPL Forge"} · FPL Forge`;
    document.getElementById("main-content")?.focus({ preventScroll: true });
    window.scrollTo(0, 0);
  }, [location.pathname]);
  const currentGameweek = gameweekOverride || (data?.latest_completed_gameweek?.toString() ?? "");
  const selectedPlayers = useMemo(() => {
    return reconcilePlayers(savedPlayers, data?.players);
  }, [data, savedPlayers]);

  const lineup = useMemo(
    () => reconcileLineup(savedLineup, selectedPlayers),
    [savedLineup, selectedPlayers],
  );
  useEffect(() => {
    if (!data) return;
    saveStored("fpl-forge-lineup", JSON.stringify(lineup));
  }, [data, lineup]);

  useEffect(() => {
    if (!data) return;
    saveStored("fpl-forge-season", data.season);
    saveStored("fpl-forge-squad", JSON.stringify(selectedPlayers));
  }, [data, selectedPlayers]);

  useEffect(() => {
    if (currentGameweek) saveStored("fpl-forge-gameweek", currentGameweek);
    saveStored("fpl-forge-free-transfers", freeTransfers);
    saveStored("fpl-forge-bank", bankMillions);
  }, [currentGameweek, freeTransfers, bankMillions]);

  useEffect(() => {
    saveStored("fpl-forge-import", JSON.stringify(importedTeam));
  }, [importedTeam]);

  function handleTeamImport(preview: TeamImportPreview) {
    setSellingPrices({});
    setSelectedPlayers(preview.players);
    setLineup(
      reconcileLineup(
        {
          starters: preview.players.slice(0, 11).map((player) => player.id),
          bench: preview.players.slice(11).map((player) => player.id),
        },
        preview.players,
      ),
    );
    setBankMillions((preview.bank_tenths / 10).toFixed(1));
    if (preview.analysis_gameweek !== null)
      setCurrentGameweek(preview.analysis_gameweek.toString());
    setImportedTeam(importedTeamMetadata(preview));
    setError(null);
  }

  function handleAddPlayer(player: Player) {
    setError(null);

    if (
      selectedPlayers.some((selected) => selected.id === player.id) ||
      selectedPlayers.length >= 15
    ) {
      return;
    }

    const playersFromTeam = selectedPlayers.filter(
      (selectedPlayer) => selectedPlayer.team_id === player.team_id,
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
      (selectedPlayer) => selectedPlayer.position === player.position,
    ).length;

    if (playersInPosition >= positionLimits[player.position]) {
      setError(`You have reached the limit for ${player.position} players.`);
      return;
    }

    setImportedTeam((previous) => (previous ? { ...previous, edited: true } : null));
    setSelectedPlayers([...selectedPlayers, player]);
  }

  function handleRemovePlayer(playerId: number) {
    setError(null);
    setImportedTeam((previous) => (previous ? { ...previous, edited: true } : null));
    setSelectedPlayers(selectedPlayers.filter((player) => player.id !== playerId));
  }

  const backup: SquadBackup = {
    version: 1,
    season: data?.season ?? importedTeam?.season ?? readStored("fpl-forge-season", ""),
    squadIds: selectedPlayers.map((player) => player.id),
    lineup,
    bank: bankMillions,
    freeTransfers,
    gameweek: currentGameweek,
    sellingPrices: Object.fromEntries(
      Object.entries(sellingPrices).filter(([id]) =>
        selectedPlayers.some((player) => player.id === Number(id)),
      ),
    ),
  };
  function restoreBackup(value: SquadBackup) {
    if (!data) return;
    const players = value.squadIds.map((id) => data.players.find((player) => player.id === id)!);
    setSelectedPlayers(players);
    setLineup(reconcileLineup(value.lineup, players));
    setBankMillions(value.bank);
    setFreeTransfers(value.freeTransfers);
    setCurrentGameweek(value.gameweek);
    setSellingPrices(value.sellingPrices);
    setImportedTeam(null);
    setError(null);
  }
  return (
    <div className="app-layout">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <header className="app-header">
        <div className="header-brand">
          <img src="/figma/forge-mark.svg" alt="" />
          FPL FORGE
        </div>
        <nav className="header-nav" aria-label="Main navigation">
          <NavLink to="/overview" onClick={() => setError(null)}>
            Overview
          </NavLink>
          <NavLink to="/player-explorer" onClick={() => setError(null)}>
            <span className="desktop-label">Player explorer</span>
            <span className="mobile-label">Players</span>
          </NavLink>
          <NavLink to="/fixture-planner" onClick={() => setError(null)}>
            <span className="desktop-label">Fixture planner</span>
            <span className="mobile-label">Fixtures</span>
          </NavLink>
          <NavLink to="/squad" onClick={() => setError(null)}>
            <span className="desktop-label">My squad</span>
            <span className="mobile-label">Squad</span>
          </NavLink>
          <NavLink to="/transfer-lab" onClick={() => setError(null)}>
            <span className="desktop-label">Transfer lab</span>
            <span className="mobile-label">Transfers</span>
          </NavLink>
        </nav>
        <div className="header-account">
          <span className="eyebrow">
            {data
              ? `${data.season} / DATA GW ${data.latest_completed_gameweek ?? "—"}`
              : "CONNECTING"}
          </span>
          <Link to="/help" className="help-link">
            Help
          </Link>
          <ThemeControl />
        </div>
      </header>

      <main className="app-main" id="main-content" tabIndex={-1}>
        {storageWarning && (
          <p className="forge-state forge-state--error" role="alert">
            Browser storage is unavailable. Your changes may be lost when this tab closes. Enable
            site storage or download a backup in Help.
          </p>
        )}
        {recoveredData && (
          <p className="forge-state" role="status">
            Some saved browser data could not be read and was reset. Review your squad and settings,
            or restore a backup in Help.
          </p>
        )}
        {!guideHidden && location.pathname !== "/help" && (
          <GettingStarted
            onDismiss={() => {
              setGuideHidden(true);
              saveStored("fpl-forge-guide-hidden", "true");
            }}
          />
        )}
        {location.pathname === "/help" && (
          <HelpPage
            backup={backup}
            availableIds={data?.players.map((player) => player.id) ?? []}
            onRestore={restoreBackup}
          />
        )}
        <DataState loading={loading} error={dataError} retry={retry} />
        {data && savedPlayers.length !== selectedPlayers.length && (
          <p className="forge-state" role="status">
            Unavailable saved players have been excluded. Review your current squad.
          </p>
        )}
        {error && location.pathname === "/player-explorer" && (
          <p className="forge-state forge-state--error" role="alert">
            {error}
          </p>
        )}
        {data && (
          <Routes>
            <Route path="/" element={<Navigate to="/squad" replace />} />

            <Route
              path="/overview"
              element={
                <OverviewPage
                  sellingPrices={sellingPrices}
                  lineup={lineup}
                  data={data}
                  selectedPlayers={selectedPlayers}
                  currentGameweek={currentGameweek}
                  freeTransfers={freeTransfers}
                  bankMillions={bankMillions}
                />
              }
            />

            <Route path="/fixture-planner" element={<FixturePlannerPage data={data} />} />

            <Route
              path="/player-explorer"
              element={
                <PlayerExplorerPage
                  data={data}
                  lookback={lookback}
                  setLookback={setLookback}
                  selectedPlayers={selectedPlayers}
                  onAddPlayer={handleAddPlayer}
                />
              }
            />

            <Route
              path="/squad"
              element={
                <>
                  {error && (
                    <p className="forge-state forge-state--error" role="alert">
                      {error}
                    </p>
                  )}

                  <SquadPage
                    lineup={lineup}
                    onLineupChange={setLineup}
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
                  sellingPrices={sellingPrices}
                  setSellingPrices={setSellingPrices}
                  lineup={lineup}
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
            <Route path="/help" element={null} />
            <Route
              path="*"
              element={
                <section className="forge-state">
                  <h1>Page not found</h1>
                  <p>That page is not part of FPL Forge.</p>
                  <Link to="/squad">Go to My Squad</Link>
                </section>
              }
            />
          </Routes>
        )}
        <footer className="page-footer">
          <span>
            FPL FORGE · Independent FPL planning tool · <Link to="/help">Help & privacy</Link>
          </span>
          <span>
            {data
              ? `DATABASE DATA / ${data.season} / THROUGH GW ${data.latest_completed_gameweek ?? "—"}`
              : "DATABASE CONNECTION REQUIRED"}
          </span>
        </footer>
      </main>
    </div>
  );
}
