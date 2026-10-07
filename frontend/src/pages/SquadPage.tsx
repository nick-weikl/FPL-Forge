import type { Player } from "../types/player";
import PlayerPicker from "../components/PlayerPicker";

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
        <>
            <div className="squad-builder">
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
                                    <span>
                                        {player.name} — {player.team_name ?? "Unknown team"} — {player.position}
                                        {" — £"}{(player.price_tenths / 10).toFixed(1)}m
                                    </span>
                                    <button
                                        type="button"
                                        onClick={() => onRemovePlayer(player.id)}
                                        disabled={disabled}
                                    >
                                        Remove
                                    </button>
                                </li>
                            ))}
                        </ul>
                    )}
                </section>
                <section className="player-picker">
                    <PlayerPicker
                        selectedPlayers={selectedPlayers}
                        onAddPlayer={onAddPlayer}
                        onRemovePlayer={onRemovePlayer}
                        disabled={disabled}
                    />
                </section>
            </div>
        </>
    );
}