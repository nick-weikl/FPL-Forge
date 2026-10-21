import { useState } from "react";
import type { Dashboard } from "../types/dashboard";
import type { Player } from "../types/player";
import "./PlayerExplorerPage.css";

const positions = [["", "All positions"], ["Goalkeeper", "Goalkeepers"], ["Defender", "Defenders"], ["Midfielder", "Midfielders"], ["Attacker", "Forwards"]];
const abbreviations: Record<string, string> = {Goalkeeper: "GK", Defender: "DEF", Midfielder: "MID", Attacker: "FWD"};

interface Props {
    data: Dashboard;
    lookback: number;
    setLookback: (value: number) => void;
    selectedPlayers: Player[];
    onAddPlayer: (player: Player) => void;
}

export default function PlayerExplorerPage({data, lookback, setLookback, selectedPlayers, onAddPlayer}: Props) {
    const [search, setSearch] = useState("");
    const [position, setPosition] = useState("");
    const [club, setClub] = useState("");
    const [sort, setSort] = useState("points");
    const [limit, setLimit] = useState(25);
    const [focusId, setFocusId] = useState<number | null>(null);
    const filtered = data.players.filter(player => player.name.toLocaleLowerCase().includes(search.trim().toLocaleLowerCase()) && (!position || player.position === position) && (!club || player.team_id === Number(club)));
    const sorted = [...filtered].sort((a, b) => {
        if (sort === "name") return a.name.localeCompare(b.name);
        const aValue = sort === "price" ? a.price_tenths : sort === "minutes" ? a.minutes : a.points;
        const bValue = sort === "price" ? b.price_tenths : sort === "minutes" ? b.minutes : b.points;
        return (bValue ?? -Infinity) - (aValue ?? -Infinity) || a.name.localeCompare(b.name);
    });
    const focused = sorted.find(player => player.id === focusId) ?? sorted[0];
    const selected = focused && selectedPlayers.some(player => player.id === focused.id);
    const maxMinutes = Math.max(90, ...(focused?.recent_minutes.map(match => match.minutes ?? 0) ?? []));
    const windowLabel = data.window.start == null ? "No imported match history" : `GW ${data.window.start}–${data.window.end}`;
    function updateFilter(callback: () => void) { callback(); setLimit(25); }
    return <div className="explorer-page page-stack">
        <div className="explorer-heading">
            <header className="page-heading"><p className="eyebrow">PLAYER EXPLORER / {data.season}</p><h1>Find your next difference-maker.</h1><p>Compare official FPL points, minutes and goals from the database.</p></header>
            <label className="field"><span className="eyebrow">FIND A PLAYER</span><input type="search" placeholder="Search players…" value={search} onChange={event => updateFilter(() => setSearch(event.target.value))} /></label>
        </div>
        <div className="explorer-workspace">
            <aside className="explorer-filters" aria-label="Player filters">
                <p className="eyebrow">REFINE THE POOL</p>
                <div className="explorer-positions">{positions.map(([value, label]) => <button className={position === value ? "selected" : ""} aria-pressed={position === value} key={label} onClick={() => updateFilter(() => setPosition(value))}>{label}</button>)}</div>
                <hr className="rule" />
                <label className="field"><span className="eyebrow">CLUB</span><select value={club} onChange={event => updateFilter(() => setClub(event.target.value))}><option value="">All clubs</option>{data.teams.map(team => <option key={team.id} value={team.id}>{team.name}</option>)}</select></label>
                <label className="field"><span className="eyebrow">MATCH WINDOW</span><select value={lookback} onChange={event => updateFilter(() => setLookback(Number(event.target.value)))}><option value={5}>Last 5 gameweeks</option><option value={38}>Season to date</option></select></label>
                <label className="field"><span className="eyebrow">SORT BY</span><select value={sort} onChange={event => updateFilter(() => setSort(event.target.value))}><option value="points">FPL points</option><option value="minutes">Minutes</option><option value="price">Price</option><option value="name">Name</option></select></label>
                <p className="small-note">{windowLabel}. Prices are current. A dash means no imported history; zero means a recorded zero.</p>
            </aside>
            <section className="explorer-results panel">
                <div className="panel-heading"><h2>The player pool</h2><p className="eyebrow">{Math.min(limit, sorted.length)} OF {sorted.length} SHOWN</p></div>
                <div className="explorer-table-scroll"><table className="explorer-table">
                    <thead><tr>{["PLAYER", "POS", "PRICE", "MINS", "GOALS", "FPL PTS"].map(label => <th scope="col" key={label}>{label}</th>)}</tr></thead>
                    <tbody>{sorted.slice(0, limit).map(player => <tr key={player.id} className={focused?.id === player.id ? "is-focused" : ""}>
                        <th scope="row"><button className="player-focus-button" aria-pressed={focused?.id === player.id} onClick={() => setFocusId(player.id)}>{player.name}</button><span>{player.team_name}</span></th>
                        <td>{abbreviations[player.position] ?? player.position}</td><td>{player.price_tenths == null ? "—" : `£${(player.price_tenths / 10).toFixed(1)}m`}</td><td>{player.minutes ?? "—"}</td><td>{player.goals ?? "—"}</td><td>{player.points ?? "—"}</td>
                    </tr>)}</tbody>
                </table></div>
                {!sorted.length && <p className="forge-state" role="status">No players match your filters.</p>}
                {sorted.length > limit && <button className="forge-button forge-button--secondary" onClick={() => setLimit(previous => previous + 25)}>Show more players</button>}
                <p className="eyebrow explorer-note">OFFICIAL FPL POINTS / {windowLabel}</p>
            </section>
            <aside className="explorer-focus panel" aria-label="Selected player details">
                {focused ? <>
                    <p className="eyebrow">IN FOCUS</p>
                    <div className="explorer-shirt" aria-hidden="true"><span className="player-initials">{focused.name.split(" ").map(part => part[0]).slice(0,2).join("")}</span></div>
                    <h2>{focused.name}</h2><p className="eyebrow">{focused.team_name} / {focused.position}</p>
                    <hr className="rule" />
                    <div className="metrics"><div><p className="eyebrow">PRICE</p><p className="metric-value">{focused.price_tenths == null ? "—" : `£${(focused.price_tenths / 10).toFixed(1)}m`}</p></div><div><p className="eyebrow">FPL POINTS</p><p className="metric-value accent">{focused.points ?? "—"}</p></div></div>
                    <p className="small-note">{focused.assists ?? "—"} assists / {focused.points_per_match ?? "—"} points per recorded fixture. Availability: {focused.availability_status === "a" ? "Available" : focused.availability_status === "i" ? "Injured" : focused.availability_status === "d" ? "Doubtful" : focused.availability_status === "s" ? "Suspended" : "Unavailable or unknown"}.</p>
                    <hr className="rule" /><p className="eyebrow">RECENT GAMEWEEK MINUTES</p>
                    {focused.recent_minutes.length ? <><div className="minutes-chart" role="img" aria-label={focused.recent_minutes.map(match => `Gameweek ${match.gameweek}: ${match.minutes ?? "unknown"} minutes`).join(", ")}>
                        {focused.recent_minutes.map(match => <span key={match.gameweek} style={{height: `${(match.minutes ?? 0) / maxMinutes * 100}%`, minHeight: match.minutes === null ? 0 : 2}} title={`GW${match.gameweek}: ${match.minutes ?? "unknown"} minutes`} />)}
                    </div><div className="minutes-labels eyebrow">{focused.recent_minutes.map(match => <span key={match.gameweek}>GW{match.gameweek}<br />{match.minutes ?? "—"}</span>)}</div></> : <p className="small-note">No match history has been imported.</p>}
                    <button className="forge-button forge-button--secondary" disabled={!!selected || selectedPlayers.length >= 15} onClick={() => onAddPlayer(focused)}>{selected ? "Already in squad" : selectedPlayers.length >= 15 ? "Squad is full" : "Add to my squad"}</button>
                </> : <p>No player is available for the current filters.</p>}
            </aside>
        </div>
    </div>;
}
