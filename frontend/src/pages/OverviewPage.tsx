import { useEffect, useState } from "react";
import { Link } from "react-router";
import FixtureMatrix from "../components/FixtureMatrix";
import type { Dashboard } from "../types/dashboard";
import type { Player } from "../types/player";
import type { Lineup } from "../utils/lineup";
import { validStarters } from "../utils/lineup";
import type { StrategyRequest, StrategyResponse } from "../types/recommendation";
import { getTransferStrategy } from "../services/api";
import "./OverviewPage.css";

interface Props {
  sellingPrices: Record<number, string>;
  lineup: Lineup;
  data: Dashboard;
  selectedPlayers: Player[];
  currentGameweek: string;
  freeTransfers: string;
  bankMillions: string;
}

export default function OverviewPage({
  sellingPrices,
  lineup,
  data,
  selectedPlayers,
  currentGameweek,
  freeTransfers,
  bankMillions,
}: Props) {
  const counts = Object.fromEntries(
    ["Goalkeeper", "Defender", "Midfielder", "Attacker"].map((position) => [
      position,
      selectedPlayers.filter((player) => player.position === position).length,
    ]),
  );
  const gameweek = Number(currentGameweek),
    transfers = Number(freeTransfers),
    bank = Number(bankMillions);
  const settingsValid =
    currentGameweek.trim() !== "" &&
    freeTransfers.trim() !== "" &&
    bankMillions.trim() !== "" &&
    Number.isInteger(gameweek) &&
    gameweek >= 1 &&
    gameweek <= 38 &&
    Number.isInteger(transfers) &&
    transfers >= 0 &&
    transfers <= 5 &&
    Number.isFinite(bank) &&
    bank >= 0 &&
    Math.abs(bank * 10 - Math.round(bank * 10)) < 0.00001;
  const sellingValid = selectedPlayers.every((player) => {
    const value = sellingPrices[player.id]?.trim();
    return (
      !value ||
      (Number.isFinite(Number(value)) &&
        Number(value) >= 0 &&
        Math.abs(Number(value) * 10 - Math.round(Number(value) * 10)) < 0.00001)
    );
  });
  const ready =
    sellingValid &&
    selectedPlayers.length === 15 &&
    settingsValid &&
    validStarters(lineup.starters, selectedPlayers) &&
    !!lineup.captainId &&
    !!lineup.viceCaptainId;
  const request: StrategyRequest = {
    starting_player_ids: lineup.starters,
    bench_player_ids: lineup.bench,
    captain_id: lineup.captainId ?? 0,
    vice_captain_id: lineup.viceCaptainId ?? 0,
    current_gameweek: gameweek,
    free_transfers: transfers,
    bank_tenths: Math.round(bank * 10),
    owned_player_ids: selectedPlayers.map((player) => player.id),
    candidates_per_player: 10,
    selling_prices_tenths: Object.fromEntries(
      selectedPlayers
        .filter(
          (player) =>
            sellingPrices[player.id]?.trim() &&
            Number.isFinite(Number(sellingPrices[player.id])) &&
            Number(sellingPrices[player.id]) >= 0 &&
            Math.abs(
              Number(sellingPrices[player.id]) * 10 -
                Math.round(Number(sellingPrices[player.id]) * 10),
            ) < 0.00001,
        )
        .map((player) => [player.id, Math.round(Number(sellingPrices[player.id]) * 10)]),
    ),
  };
  const requestKey = JSON.stringify(request);
  const [analysis, setAnalysis] = useState<{
    key: string;
    result?: StrategyResponse;
    error?: string;
  }>({ key: "" });
  useEffect(() => {
    if (!ready) return;
    const controller = new AbortController();
    getTransferStrategy(JSON.parse(requestKey), controller.signal)
      .then((result) => {
        if (!controller.signal.aborted) setAnalysis({ key: requestKey, result });
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted)
          setAnalysis({
            key: requestKey,
            error: error instanceof Error ? error.message : "Could not analyze your squad.",
          });
      });
    return () => controller.abort();
  }, [ready, requestKey]);
  const result = ready && analysis.key === requestKey ? analysis.result : undefined;
  const error = ready && analysis.key === requestKey ? analysis.error : undefined;
  const pending = ready && analysis.key !== requestKey;
  const moves =
    result?.recommended_strategy === "single_transfer" && result.single_transfer
      ? [result.single_transfer.transfer]
      : result?.recommended_strategy === "double_transfer"
        ? (result.double_transfer?.transfer_pair.transfers ?? [])
        : [];
  const labels = {
    single_transfer: "SINGLE TRANSFER",
    double_transfer: "DOUBLE TRANSFER",
    no_transfer: "KEEP YOUR SQUAD",
  };
  const squadClubs = [...new Set(selectedPlayers.map((player) => player.team_id))];
  const visibleTeamIds = squadClubs.length
    ? squadClubs
    : data.teams.slice(0, 4).map((team) => team.id);
  return (
    <div className="overview-page page-stack">
      <div className="overview-hero">
        <header className="overview-intro">
          <p className="overview-badge eyebrow">THE GAMEWEEK BRIEF</p>
          <h1>
            Your edge,
            <br />
            next gameweek.
          </h1>
          <p>
            Know your squad. Read the fixtures.
            <br />
            Make the move that earns its place.
          </p>
          <div className="overview-actions">
            <Link className="forge-button" to="/squad">
              Open my squad
            </Link>
            <Link className="forge-button forge-button--secondary" to="/player-explorer">
              Explore players
            </Link>
          </div>
        </header>
        <section className="overview-context panel" aria-label="Current season context">
          <div className="overview-gameweek">
            <strong>{data.next_gameweek?.toString().padStart(2, "0") ?? "—"}</strong>
            <div>
              <p className="eyebrow accent">{data.next_gameweek ? "NEXT UP" : "SEASON COMPLETE"}</p>
              <h2>
                Your plan
                <br />
                starts here.
              </h2>
              <p className="small-note">
                {data.season} /{" "}
                {data.latest_completed_gameweek == null
                  ? "No completed gameweek imported"
                  : `Data through GW ${data.latest_completed_gameweek}`}
              </p>
            </div>
          </div>
          <hr className="rule" />
          <div className="metrics">
            <div>
              <p className="eyebrow">FREE TRANSFERS</p>
              <p className="metric-value">{freeTransfers || "—"}</p>
            </div>
            <div>
              <p className="eyebrow">IN THE BANK</p>
              <p className="metric-value">
                {bankMillions.trim() && Number.isFinite(bank) && bank >= 0
                  ? `£${bank.toFixed(1)}m`
                  : "—"}
              </p>
            </div>
          </div>
          <p className="small-note">Your saved transfer settings. Update them in Transfer Lab.</p>
        </section>
      </div>
      <section
        className="overview-next-move"
        aria-label="Your next transfer decision"
        aria-live="polite"
      >
        <div>
          <p className="eyebrow">
            YOUR NEXT MOVE{result && ` / ${labels[result.recommended_strategy]}`}
          </p>
          {moves.length ? (
            moves.map((move) => (
              <h2 key={move.player_out.player_id}>
                {move.player_out.name} → {move.player_in.name}
              </h2>
            ))
          ) : (
            <h2>
              {!ready
                ? "Build your squad. Set your plan."
                : pending
                  ? "Analyzing your squad…"
                  : error
                    ? "Analysis unavailable"
                    : "Keep your current squad."}
            </h2>
          )}
          <p>
            {!ready
              ? "Choose your squad, starting XI and valid transfer settings to see your recommendation."
              : (error ?? result?.reason.summary)}
          </p>
        </div>
        <div>
          <p className="overview-gain">
            {result
              ? `${result.best_net_score_gain > 0 ? "+" : ""}${result.best_net_score_gain.toFixed(2)}`
              : "—"}
          </p>
          <p className="eyebrow">
            {result
              ? `TOTAL NET GAIN · ${result.horizon_gameweeks} GAMEWEEKS`
              : "ESTIMATED NET GAIN"}
          </p>
        </div>
        <Link className="forge-button forge-button--secondary" to="/transfer-lab">
          Open Transfer Lab
        </Link>
      </section>
      {result && (
        <p className="small-note">
          GW{gameweek + 1}–{gameweek + result.horizon_gameweeks}: a total over{" "}
          {result.horizon_gameweeks} gameweeks, including transfer hits and captain points.
          Estimates are not guaranteed. Check selling values and the full breakdown in Transfer Lab.
        </p>
      )}
      <div className="overview-planning">
        <section className="panel overview-runway">
          <div className="panel-heading">
            <h2>The fixture runway</h2>
            <p className="eyebrow">
              {data.next_gameweek
                ? `GW ${data.next_gameweek}–${Math.min(38, data.next_gameweek + 4)}`
                : "NO UPCOMING FIXTURES"}
            </p>
          </div>
          {data.next_gameweek ? (
            <FixtureMatrix
              compact
              teams={data.teams}
              fixtures={data.fixtures}
              startGameweek={data.next_gameweek}
              visibleTeamIds={visibleTeamIds}
            />
          ) : (
            <p>No upcoming fixtures remain in the stored season.</p>
          )}
          <p className="small-note">
            {squadClubs.length
              ? "Clubs in your selected squad."
              : "Alphabetical club preview; choose a squad to personalize it."}{" "}
            {data.difficulty_description}
          </p>
        </section>
        <section className="panel overview-squad">
          <div className="overview-squad-count">
            <strong>{selectedPlayers.length}</strong>
            <p className="eyebrow">
              PLAYERS
              <br />
              SELECTED
            </p>
          </div>
          <hr className="rule" />
          {[
            ["Goalkeeper", "Goalkeepers", 2],
            ["Defender", "Defenders", 5],
            ["Midfielder", "Midfielders", 5],
            ["Attacker", "Forwards", 3],
          ].map(([position, label, required]) => (
            <div key={position}>
              <span>{label}</span>
              <span className="eyebrow accent">
                {counts[position]} / {required}
              </span>
            </div>
          ))}
        </section>
      </div>
    </div>
  );
}
