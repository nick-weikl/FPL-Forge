import type { Player } from "../types/player";
import PlayerPicker from "../components/PlayerPicker";
import "./SquadPage.css";

interface SquadPageProps {
    selectedPlayers: Player[];
    onAddPlayer: (player: Player) => void;
    onRemovePlayer: (playerId: number) => void;
    bankMillions: string;
    disabled: boolean;
}

export default function SquadPage({ selectedPlayers, onAddPlayer, onRemovePlayer, bankMillions, disabled }: SquadPageProps) {
    const goalkeeperCount = selectedPlayers.filter(player => player.position === "Goalkeeper").length;
    const defenderCount = selectedPlayers.filter(player => player.position === "Defender").length;
    const midfielderCount = selectedPlayers.filter(player => player.position === "Midfielder").length;
    const attackerCount = selectedPlayers.filter(player => player.position === "Attacker").length;

    return (
        <div className="squad-page page-stack">
            <header className="page-heading"><p className="eyebrow">SQUAD WORKBENCH</p><h1>Build the team behind your next move.</h1><p>Your selected players, positional balance and player picker in one place.</p></header>
            <div className="squad-summary">
                <div><p className="eyebrow">SELECTED</p><p className="metric-value accent">{selectedPlayers.length} / 15</p></div>
                <div><p className="eyebrow">BANK</p><p className="metric-value">£{bankMillions || "—"}m</p></div>
                <div><p className="eyebrow">POSITION CHECK</p><p className="metric-value">{goalkeeperCount} / {defenderCount} / {midfielderCount} / {attackerCount}</p></div>
                <div><p className="eyebrow">CLUB LIMIT</p><p className="metric-value">Maximum 3</p></div>
            </div>
            <div className="squad-workspace">
                <aside className="squad-roster panel">
                    <p className="eyebrow accent">YOUR 15</p>
                    {[['Goalkeeper', 'GK'], ['Defender', 'DEF'], ['Midfielder', 'MID'], ['Attacker', 'FWD']].map(([position, label]) => <section key={position}>
                        <h2 className="eyebrow">{label}</h2>
                        <ul>{selectedPlayers.filter(player => player.position === position).map(player => <li key={player.id}><span>{player.name}</span><span>£{(player.price_tenths / 10).toFixed(1)}m</span></li>)}</ul>
                    </section>)}
                    {selectedPlayers.length === 0 && <p className="small-note">Add players to build your squad.</p>}
                </aside>
                <section className="squad-pitch panel">
                    <div className="panel-heading"><h2>Your squad on the pitch</h2><p className="eyebrow accent">{selectedPlayers.length} / 15</p></div>
                    <div className="squad-pitch-scroll"><div className="squad-pitch-field">
                        <img className="pitch-markings" src="/figma/tactical-pitch.svg" alt="" />
                        {selectedPlayers.length === 0 ? <div className="forge-state forge-state--empty squad-empty"><strong className="forge-state-title">Your squad starts here.</strong><p>Add players using the picker.</p></div> : <div className="squad-position-groups">
                            {[['Goalkeeper', 'GK'], ['Defender', 'DEF'], ['Midfielder', 'MID'], ['Attacker', 'FWD']].map(([position, label]) => <section className="squad-position-group" key={position} aria-label={position}>
                                <ul className="squad-player-tiles">{selectedPlayers.filter(player => player.position === position).map(player => <li className="squad-player-tile" key={player.id}>
                                    <strong>{player.name}</strong><span className="eyebrow">{player.team_name ?? "Unknown team"} / {label}</span>
                                    <div className="tile-value"><span>£{(player.price_tenths / 10).toFixed(1)}m</span><button type="button" className="tile-remove" onClick={() => onRemovePlayer(player.id)} disabled={disabled} aria-label={`Remove ${player.name}`}>×</button></div>
                                </li>)}</ul>
                            </section>)}
                        </div>}
                    </div></div>
                    <p className="small-note">Select and remove players using the picker and squad controls.</p>
                </section>
                <section className="squad-picker panel"><PlayerPicker selectedPlayers={selectedPlayers} onAddPlayer={onAddPlayer} onRemovePlayer={onRemovePlayer} disabled={disabled} /></section>
            </div>
        </div>
    );
}
