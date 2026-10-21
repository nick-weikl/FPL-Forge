import type { Player } from "../types/player";
import LineupEditor from "../components/LineupEditor";
import type { Lineup } from "../utils/lineup";
import PlayerPicker from "../components/PlayerPicker";
import TeamImport from "../components/TeamImport";
import type { ImportedTeam, TeamImportPreview } from "../types/teamImport";
import "./SquadPage.css";

interface SquadPageProps {
    selectedPlayers: Player[];
    lineup: Lineup;
    onLineupChange: (lineup: Lineup) => void;
    bankMillions: string;
    setBankMillions: (value: string) => void;
    importedTeam: ImportedTeam | null;
    onImport: (preview: TeamImportPreview) => void;
    availablePlayers: Player[];
    onAddPlayer: (player: Player) => void;
    onRemovePlayer: (playerId: number) => void;
    disabled: boolean;
}

export default function SquadPage({ lineup, onLineupChange, bankMillions, setBankMillions, importedTeam, onImport, availablePlayers, selectedPlayers, onAddPlayer, onRemovePlayer, disabled }: SquadPageProps) {
    const marketValueTenths = selectedPlayers.reduce(
        (total, player) => total + player.price_tenths,
        0,
    );
    const goalkeeperCount = selectedPlayers.filter(player => player.position === "Goalkeeper").length;
    const defenderCount = selectedPlayers.filter(player => player.position === "Defender").length;
    const midfielderCount = selectedPlayers.filter(player => player.position === "Midfielder").length;
    const attackerCount = selectedPlayers.filter(player => player.position === "Attacker").length;

    return (
        <div className="squad-page page-stack">
            <header className="page-heading"><p className="eyebrow">SQUAD WORKBENCH</p><h1>Build the team behind your next move.</h1><p>Your selected players, positional balance and player picker in one place.</p></header>
            <TeamImport onImport={onImport} initialTeamId={importedTeam?.entry_id} />
            {importedTeam && <section className="panel" role="status" aria-label="Imported squad source">
                <p><strong>{importedTeam.team_name} · #{importedTeam.entry_id}</strong> · {importedTeam.season} · As of the GW{importedTeam.gameweek} deadline</p>
                <p className="small-note">Imported deadline: {new Date(importedTeam.deadline_time).toLocaleString()}. Recorded bank: £{(importedTeam.bank_tenths / 10).toFixed(1)}m. Transfers after this deadline may not be included. This is not a live FPL account connection.</p>
                {importedTeam.edited && <p className="small-note">You have edited this squad since importing it.</p>}
                {Number(bankMillions) * 10 !== importedTeam.bank_tenths && <p className="small-note">Your bank has been edited since the import.</p>}
            </section>}
            <label className="field squad-bank-field"><span className="eyebrow">BANK / £m</span><input type="number" min="0" step="0.1" value={bankMillions} onChange={event => setBankMillions(event.target.value)} /><span className="small-note">Shared with Transfer Lab. Update this if you made transfers after the imported deadline. Market price changes do not alter your bank.</span></label>
            <div className="squad-summary">
                <div><p className="eyebrow">SELECTED</p><p className="metric-value accent">{selectedPlayers.length} / 15</p></div>
                <div><p className="eyebrow">BANK</p><p className="metric-value">{bankMillions.trim() && Number.isFinite(Number(bankMillions)) && Number(bankMillions) >= 0 ? `£${Number(bankMillions).toFixed(1)}m` : "—"}</p></div>
                <div><p className="eyebrow">POSITION CHECK</p><p className="metric-value">{goalkeeperCount} / {defenderCount} / {midfielderCount} / {attackerCount}</p></div>
                <div><p className="eyebrow">MARKET VALUE</p><p className="metric-value">£{(marketValueTenths / 10).toFixed(1)}m</p></div>
            </div>
            <LineupEditor players={selectedPlayers} lineup={lineup} onChange={onLineupChange} />
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
                    <div className="panel-heading"><h2>Your starting XI on the pitch</h2><p className="eyebrow accent">{lineup.starters.length} / 11</p></div>
                    <div className="squad-pitch-scroll"><div className="squad-pitch-field">
                        <img className="pitch-markings" src="/figma/tactical-pitch.svg" alt="" />
                        {lineup.starters.length === 0 ? <div className="forge-state forge-state--empty squad-empty"><strong className="forge-state-title">Your starting XI starts here.</strong><p>Complete your squad using the picker to set a lineup.</p></div> : <div className="squad-position-groups">
                            {[['Goalkeeper', 'GK'], ['Defender', 'DEF'], ['Midfielder', 'MID'], ['Attacker', 'FWD']].map(([position, label]) => <section className="squad-position-group" key={position} aria-label={position}>
                                <ul className="squad-player-tiles">{selectedPlayers.filter(player => lineup.starters.includes(player.id) && player.position === position).map(player => <li className="squad-player-tile" key={player.id}>
                                    <strong>{player.name}</strong><span className="eyebrow">{player.team_name ?? "Unknown team"} / {label}</span>
                                    <div className="tile-value"><span>£{(player.price_tenths / 10).toFixed(1)}m</span><button type="button" className="tile-remove" onClick={() => onRemovePlayer(player.id)} disabled={disabled} aria-label={`Remove ${player.name}`}>×</button></div>
                                </li>)}</ul>
                            </section>)}
                        </div>}
                    </div></div>
                    <p className="small-note">Select and remove players using the picker and squad controls.</p>
                </section>
                <section className="squad-picker panel"><PlayerPicker players={availablePlayers} selectedPlayers={selectedPlayers} onAddPlayer={onAddPlayer} onRemovePlayer={onRemovePlayer} disabled={disabled} /></section>
            </div>
        </div>
    );
}
