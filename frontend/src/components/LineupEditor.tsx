import type { Player } from "../types/player";
import { moveSubstitute, swapStarter, validStarters } from "../utils/lineup";
import type { Lineup } from "../utils/lineup";

interface Props { players: Player[]; lineup: Lineup; onChange: (lineup: Lineup) => void }
export default function LineupEditor({players, lineup, onChange}: Props) {
    const ready = players.length === 15 && validStarters(lineup.starters, players) && lineup.bench.length === 4;
    const starters = players.filter(player => lineup.starters.includes(player.id));
    const formation = ["Defender", "Midfielder", "Attacker"].map(role => starters.filter(player => player.position === role).length).join("–");
    return <section className="panel lineup-editor" aria-label="Starting XI and bench">
        <div className="panel-heading"><h2>Starting XI & bench</h2><span className="eyebrow accent">{ready ? formation : "SQUAD INCOMPLETE"}</span></div>
        <p className="small-note">Choose a bench player to swap into your XI. Valid formations require one goalkeeper, at least three defenders, two midfielders and one forward. Changes save automatically in this browser.</p>
        {!ready ? <p role="status">Complete your 15-player squad (2 goalkeepers, 5 defenders, 5 midfielders and 3 forwards) to set your lineup.</p> : <>
            <div className="lineup-starters">{["Goalkeeper", "Defender", "Midfielder", "Attacker"].map(role => <section key={role}><h3 className="eyebrow">{role}</h3><ul>{starters.filter(player => player.position === role).map(player => <li key={player.id}><span>{player.name}</span><label><span className="small-note">Swap with</span><select aria-label={`Replace starter ${player.name}`} value="" onChange={event => onChange(swapStarter(lineup, player.id, Number(event.target.value), players))}><option value="">Choose substitute</option>{lineup.bench.map(id => players.find(candidate => candidate.id === id)!).filter(candidate => swapStarter(lineup, player.id, candidate.id, players) !== lineup).map(candidate => <option key={candidate.id} value={candidate.id}>{candidate.name} · {candidate.position}</option>)}</select></label></li>)}</ul></section>)}</div>
            <h3>Bench order</h3><p className="small-note">The reserve goalkeeper has a separate slot. Outfield substitutes are ordered from first to third priority.</p>
            <ol className="lineup-bench">{lineup.bench.map((id, index) => {
                const player = players.find(candidate => candidate.id === id)!;
                const goalkeeper = player.position === "Goalkeeper";
                return <li key={id}><span className="eyebrow accent">{goalkeeper ? "RESERVE GK" : `SUB ${index}`}</span><strong>{player.name}</strong><span className="small-note">{player.position}</span>{!goalkeeper && <div className="lineup-order"><button type="button" disabled={index === 1} aria-label={`Move ${player.name} earlier`} onClick={() => onChange(moveSubstitute(lineup, id, -1, players))}>↑ Earlier</button><button type="button" disabled={index === 3} aria-label={`Move ${player.name} later`} onClick={() => onChange(moveSubstitute(lineup, id, 1, players))}>↓ Later</button></div>}</li>;
            })}</ol>
        </>}
    </section>;
}
