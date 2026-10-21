import { useState } from "react";
import type { Player } from "../types/player";
import { moveSubstitute, swapStarter, validStarters } from "../utils/lineup";
import type { Lineup } from "../utils/lineup";

interface Props { players: Player[]; lineup: Lineup; onChange: (lineup: Lineup) => void }
export default function LineupEditor({players, lineup, onChange}: Props) {
    const [selectedStarter, selectStarter] = useState<number | null>(null);
    const ready = players.length === 15 && validStarters(lineup.starters, players) && lineup.bench.length === 4;
    const starters = players.filter(player => lineup.starters.includes(player.id));
    const selected = starters.find(player => player.id === selectedStarter);
    const formation = ["Defender", "Midfielder", "Attacker"].map(role => starters.filter(player => player.position === role).length).join("–");
    const shortName = (name: string) => name.split(" ").length > 3 ? name.split(" ").slice(0, 2).join(" ") : name;
    return <section className="lineup-editor" aria-label="Starting XI and bench">
        <div className="panel-heading"><div><h2>Starting XI</h2><p className="small-note">Select a starter, then a highlighted substitute to swap.</p></div><span className="formation-label">{ready ? formation : `${players.length} / 15`}</span></div>
        <p className="lineup-instruction" role="status">{!ready ? "Complete your squad below to choose a starting XI." : selected ? `Replacing ${selected.name}. Choose a highlighted substitute, or select this player again to cancel.` : "Your lineup is saved automatically in this browser."}</p>
        <div className="lineup-pitch">
            <div className="pitch-center-circle" aria-hidden="true" />
            {ready ? ["Goalkeeper", "Defender", "Midfielder", "Attacker"].map(role => <div className="lineup-row" key={role} style={{gridTemplateColumns: `repeat(${starters.filter(player => player.position === role).length}, minmax(0, 1fr))`}}>
                {starters.filter(player => player.position === role).map(player => <button type="button" className={`lineup-player${selectedStarter === player.id ? " is-selected" : ""}`} key={player.id} aria-label={`Select ${player.name} to substitute`} aria-pressed={selectedStarter === player.id} onClick={() => selectStarter(selectedStarter === player.id ? null : player.id)} title={player.name}>
                    <span className="player-shirt" aria-hidden="true">{lineup.captainId === player.id ? "C" : lineup.viceCaptainId === player.id ? "V" : ""}</span>
                    <strong>{shortName(player.name)}</strong><span>{player.team_name}</span>
                </button>)}
            </div>) : <div className="lineup-empty"><h3>Build your matchday team</h3><p>Import your FPL squad or add players in “Edit squad”.</p></div>}
        </div>
        {ready && <>
            <div className="panel-heading bench-heading"><h3>Substitutes</h3>{selected && <button className="text-button" type="button" onClick={() => selectStarter(null)}>Cancel swap</button>}</div>
            <ol className="lineup-bench">{lineup.bench.map((id, index) => {
                const player = players.find(candidate => candidate.id === id)!;
                const goalkeeper = player.position === "Goalkeeper";
                const canSwap = !!selected && swapStarter(lineup, selected.id, id, players) !== lineup;
                return <li key={id} className={canSwap ? "can-swap" : ""}>
                    <span className="small-note">{goalkeeper ? "Reserve goalkeeper" : `${index}. Outfield substitute`}</span>
                    <button type="button" className="bench-player" disabled={!canSwap} aria-label={`Bring on ${player.name}`} onClick={() => { if (selected) onChange(swapStarter(lineup, selected.id, id, players)); selectStarter(null); }}><strong>{shortName(player.name)}</strong><span className="small-note">{player.position}</span></button>
                    {!goalkeeper && <div className="lineup-order"><button type="button" disabled={index === 1} aria-label={`Move ${player.name} earlier`} onClick={() => onChange(moveSubstitute(lineup, id, -1, players))}>←</button><button type="button" disabled={index === 3} aria-label={`Move ${player.name} later`} onClick={() => onChange(moveSubstitute(lineup, id, 1, players))}>→</button></div>}
                </li>;
            })}</ol>
            <div className="captain-controls">{([["captainId", "Captain · double points"], ["viceCaptainId", "Vice-captain"]] as const).map(([key, label]) => <label className="field" key={key}><span>{label}</span><select value={lineup[key] ?? ""} onChange={event => onChange({...lineup, [key]: Number(event.target.value)})}>{starters.filter(player => player.id !== lineup[key === "captainId" ? "viceCaptainId" : "captainId"]).map(player => <option value={player.id} key={player.id}>{player.name}</option>)}</select></label>)}</div>
            <p className="small-note">The reserve goalkeeper has a separate slot. Use the arrows to order your three outfield substitutes. Swaps always keep a valid formation.</p>
        </>}
    </section>;
}
