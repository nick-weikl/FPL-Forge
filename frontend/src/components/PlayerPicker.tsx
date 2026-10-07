import { getPlayers } from "../services/api";
import type { Player } from "../types/player";
import { useState, useEffect } from "react";

interface PlayerPickerProps {
    selectedPlayers: Player[];
    onAddPlayer: (player: Player) => void
    onRemovePlayer: (playerId: number) => void
    disabled: boolean
}

export default function PlayerPicker(props: PlayerPickerProps) {
    const [players, setPlayers] = useState<Player[]>([])
    const [loading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState<string>("")
    const [positionFilter, setPositionFilter] = useState<string>("")


    useEffect(() => {
        async function loadPlayers() {
            try {
                const result = await getPlayers()
                setPlayers(result)
            }
            catch (error) {
                setError("Could not load players. Please try again")
                console.error("Error", error)
            }
            finally {
                setIsLoading(false)
            }
        }

        loadPlayers();
    }, []);

    const filteredPlayers = players.filter((player) => {
        const matchesName = player.name
            .toLowerCase()
            .includes(searchTerm.trim().toLowerCase());

        const matchesPosition =
            positionFilter === "" || player.position === positionFilter;

        const alreadySelected = props.selectedPlayers.some(
            (selectedPlayer) => selectedPlayer.id === player.id
        );

        return matchesName && matchesPosition && !alreadySelected;
    });

    const positionOrder: Record<string, number> = {
        Goalkeeper: 0,
        Defender: 1,
        Midfielder: 2,
        Attacker: 3,
    };

    const sortedPlayers = [...filteredPlayers].sort((a, b) => {
        const positionDifference =
            (positionOrder[a.position] ?? 99) -
            (positionOrder[b.position] ?? 99);

        return positionDifference || a.name.localeCompare(b.name);
    });

    return (
    <>
        <h2>Players</h2>

        <div className="picker-filters">
            <div>
                <label htmlFor="player-search">Search players</label>

                <input
                    type="search"
                    value={searchTerm}
                    onChange={(event) => {
                        setSearchTerm(event.target.value);
                    }}
                    id="player-search"
                    placeholder="Search by name..."
                />
            </div>

            <div>
                <label htmlFor="player-position">Position</label>

                <select
                    id="player-position"
                    value={positionFilter}
                    onChange={(event) => {
                        setPositionFilter(event.target.value);
                    }}
                >
                    <option value="">All Positions</option>
                    <option value="Goalkeeper">Goalkeepers</option>
                    <option value="Defender">Defenders</option>
                    <option value="Midfielder">Midfielders</option>
                    <option value="Attacker">Attackers</option>
                </select>
            </div>
        </div>

        {loading && (
            <div
                className="forge-state forge-state--loading"
                role="status"
            >
                <strong className="forge-state-title">
                    Loading players…
                </strong>
                <p>Fetching the player list.</p>
            </div>
        )}

        {error && (
            <p
                className="forge-state forge-state--error"
                role="alert"
            >
                {error}
            </p>
        )}

        {!loading && !error && (
            <>
                {filteredPlayers.length === 0 && (
                    <div className="forge-state forge-state--empty">
                        <strong className="forge-state-title">
                            No players match your filters.
                        </strong>
                        <p>Try another name or position. Selected players are hidden.</p>
                    </div>
                )}

                <ul>
                    {sortedPlayers.map((player) => {
                        const isSelected = props.selectedPlayers.some(
                            (selectedPlayer) => selectedPlayer.id === player.id
                        );

                        return (
                            <li key={player.id}>
                                <span>
                                    {player.name} — {player.team_name ?? "Unknown team"} — {player.position} — £
                                    {(player.price_tenths / 10).toFixed(1)}m
                                    {isSelected ? " — Selected" : " — Available"}
                                </span>
                                <button
                                onClick={() => {
                                    if (isSelected) {
                                        props.onRemovePlayer(player.id)
                                    } else {
                                        props.onAddPlayer(player)
                                    }
                                }}
                                disabled={props.disabled}
                                >{isSelected ? "Remove" : "Add"}</button>
                            </li>
                        );
                    })}
                </ul>
            </>
        )}
    </>
);
}
