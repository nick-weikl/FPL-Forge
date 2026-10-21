import type { Player } from "../types/player";
import { useState } from "react";

interface Props {
    players: Player[];
    selectedPlayers: Player[];
    onAddPlayer: (player: Player) => void;
    onRemovePlayer: (playerId: number) => void;
    disabled: boolean;
}

export default function PlayerPicker({players, selectedPlayers, onAddPlayer, disabled}: Props) {
    const [search, setSearch] = useState("");
    const [position, setPosition] = useState("");
    const [club, setClub] = useState("");
    const [limit, setLimit] = useState(50);
    const clubs = [...new Map(players.map(player => [player.team_id, player.team_name])).entries()].sort((a,b) => (a[1] ?? "").localeCompare(b[1] ?? ""));
    const selectedIds = new Set(selectedPlayers.map(player => player.id));
    const order: Record<string, number> = {Goalkeeper: 0, Defender: 1, Midfielder: 2, Attacker: 3};
    const filtered = players.filter(player => !selectedIds.has(player.id) && player.name.toLocaleLowerCase().includes(search.trim().toLocaleLowerCase()) && (!position || player.position === position) && (!club || player.team_id === Number(club)))
        .sort((a,b) => (order[a.position] ?? 99) - (order[b.position] ?? 99) || a.name.localeCompare(b.name));
    return <>
        <h2>Add to your squad</h2>
        <div className="picker-filters">
            <label className="field" htmlFor="player-search"><span className="eyebrow">SEARCH PLAYERS</span><input id="player-search" type="search" placeholder="Search name…" value={search} onChange={event => {setSearch(event.target.value); setLimit(50);}} /></label>
            <div className="picker-filter-row">
                <select aria-label="Position" value={position} onChange={event => {setPosition(event.target.value); setLimit(50);}}><option value="">All positions</option>{[["Goalkeeper","Goalkeepers"],["Defender","Defenders"],["Midfielder","Midfielders"],["Attacker","Forwards"]].map(([value,label]) => <option key={value} value={value}>{label}</option>)}</select>
                <select aria-label="Club" value={club} onChange={event => {setClub(event.target.value); setLimit(50);}}><option value="">All clubs</option>{clubs.map(([id,name]) => <option key={id} value={id}>{name}</option>)}</select>
            </div>
        </div>
        {!filtered.length && <p className="forge-state" role="status">No players match your filters. Selected players are hidden.</p>}
        <ul>{filtered.slice(0,limit).map(player => <li key={player.id}>
            <span className="picker-player-name">{player.name}<span className="small-note">{player.team_name ?? "Unknown team"} · {player.position}</span></span>
            <span className="picker-price">{player.price_tenths == null ? "—" : `£${(player.price_tenths / 10).toFixed(1)}m`}</span>
            <button aria-label={`Add ${player.name}`} onClick={() => onAddPlayer(player)} disabled={disabled || selectedPlayers.length >= 15}>+</button>
        </li>)}</ul>
        {filtered.length > limit && <button className="forge-button forge-button--secondary" onClick={() => setLimit(previous => previous + 50)}>Show more players</button>}
    </>;
}
