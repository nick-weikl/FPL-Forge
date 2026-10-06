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

        <input 
        type="search"
        value={searchTerm}
        onChange={(event) => {setSearchTerm(event.target.value)}}
        id="1"/>
        <select value={positionFilter}
        onChange={(event) => {setPositionFilter(event.target.value)}}>
            <option value={""}>All Positions</option>
            <option value={"Goalkeeper"}>Goalkeepers</option>
            <option value={"Defender"}>Defenders</option>
            <option value={"Midfielder"}>Midfielders</option>
            <option value={"Attacker"}>Attackers</option>
        </select>

        {loading && <p>Loading players...</p>}

        {error && <p role="alert">{error}</p>}

        {!loading && !error && (
            <>
                {filteredPlayers.length === 0 && (
                    <p>No players match your filters.</p>
                )}

                <ul>
                    {sortedPlayers.map((player) => {
                        const isSelected = props.selectedPlayers.some(
                            (selectedPlayer) => selectedPlayer.id === player.id
                        );

                        return (
                            <li key={player.id}>
                                {player.name} — {player.team_name ?? "Unknown team"} — {player.position} — £
                                {(player.price_tenths / 10).toFixed(1)}m
                                {isSelected ? " — Selected" : " — Available"}
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
