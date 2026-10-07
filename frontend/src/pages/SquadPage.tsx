import type { Player } from "../types/player";
import PlayerPicker from "../components/PlayerPicker";
import "./SquadPage.css"

interface SquadPageProps {
    selectedPlayers: Player[];
    onAddPlayer: (player: Player) => void;
    onRemovePlayer: (playerId: number) => void;
    disabled: boolean;
}

export default function SquadPage({
    selectedPlayers,
    onAddPlayer,
    onRemovePlayer,
    disabled,
}: SquadPageProps) {
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

    return (
        <div className="squad-page">
            <header className="page-heading">
                <div className="context-bar">
                    <p>WORKSPACE / MY SQUAD</p>
                    <p>Historical demo / Nick</p>
                </div>

                <div className="squad-heading-row">
                    <div>
                        <h1>Your squad. Your call.</h1>
                        <p>A manual squad workspace for your next gameweek.</p>
                    </div>

                    <button type="button" className="forge-button" disabled>
                        Import screenshot
                    </button>
                </div>
            </header>

            <div className="squad-summary">
                <div>
                    <p className="squad-label">BANK</p>
                    <p className="squad-summary-value">—</p>
                </div>

                <div>
                    <p className="squad-label">STARTING XI</p>
                    <p className="squad-summary-value">—</p>
                </div>

                <div>
                    <p className="squad-label">FORMATION</p>
                    <p className="squad-summary-value">—</p>
                </div>

                <div>
                    <p className="squad-label">PROJECTION</p>
                    <p className="squad-summary-value">—</p>
                </div>
            </div>

            <div className="squad-workspace">
                <section className="squad-pitch">
                    <h2>Selected squad</h2>

                    <p className="squad-description">
                        {selectedPlayers.length} / 15 players selected
                    </p>

                    {selectedPlayers.length === 0 ? (
                        <div className="forge-state forge-state--empty">
                            <strong className="forge-state-title">
                                Your squad starts here.
                            </strong>
                            <p>Add players using the picker below.</p>
                        </div>
                    ) : (
                        <div className="squad-position-groups">
                            {[
                                "Goalkeeper",
                                "Defender",
                                "Midfielder",
                                "Attacker",
                            ].map((position) => (
                                <section
                                    className="squad-position-group"
                                    key={position}
                                >
                                    <h3 className="squad-label">{position}</h3>

                                    <ul className="squad-player-tiles">
                                        {selectedPlayers
                                            .filter(
                                                (player) =>
                                                    player.position === position
                                            )
                                            .map((player) => (
                                                <li
                                                    className="squad-player-tile"
                                                    key={player.id}
                                                >
                                                    <strong>{player.name}</strong>

                                                    <span>
                                                        {player.team_name ?? "Unknown team"}
                                                    </span>

                                                    <span>
                                                        £
                                                        {(player.price_tenths / 10).toFixed(1)}
                                                        m
                                                    </span>

                                                    <button
                                                        type="button"
                                                        className="tile-remove"
                                                        onClick={() =>
                                                            onRemovePlayer(player.id)
                                                        }
                                                        disabled={disabled}
                                                    >
                                                        Remove
                                                    </button>
                                                </li>
                                            ))}
                                    </ul>
                                </section>
                            ))}
                        </div>
                    )}
                </section>

                <section className="squad-review">
                    <h2>Squad overview</h2>

                    <div className="squad-counts">
                        <p>Goalkeepers: {goalkeeperCount} / 2</p>
                        <p>Defenders: {defenderCount} / 5</p>
                        <p>Midfielders: {midfielderCount} / 5</p>
                        <p>Attackers: {attackerCount} / 3</p>
                    </div>

                    <p className="squad-description">
                        Prices and budget calculations currently use demo values.
                    </p>

                    <p className="squad-label">CHIP PLANNING · LATER</p>

                    <p className="squad-description">
                        Plan an available chip inside its verified season window.
                    </p>
                </section>
            </div>

            <section className="squad-picker">
                <PlayerPicker
                    selectedPlayers={selectedPlayers}
                    onAddPlayer={onAddPlayer}
                    onRemovePlayer={onRemovePlayer}
                    disabled={disabled}
                />
            </section>
        </div>
    );
}