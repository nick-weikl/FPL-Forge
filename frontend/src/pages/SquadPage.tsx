import type { Player } from "../types/player";
import LineupEditor from "../components/LineupEditor";
import type { Lineup } from "../utils/lineup";
import PlayerPicker from "../components/PlayerPicker";
import TeamImport from "../components/TeamImport";
import type { ImportedTeam, TeamImportPreview } from "../types/teamImport";
import { Link } from "react-router";
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

export default function SquadPage({lineup, onLineupChange, bankMillions, setBankMillions, importedTeam, onImport, availablePlayers, selectedPlayers, onAddPlayer, onRemovePlayer, disabled}: SquadPageProps) {
    const value = selectedPlayers.reduce((total, player) => total + player.price_tenths, 0);
    return <div className="squad-page page-stack">
        <header className="squad-heading"><div className="page-heading"><h1>My squad</h1><p>Pick your XI, set the bench, and plan your next move.</p></div><Link className="forge-button forge-button--secondary" to="/transfer-lab">Open Transfer Lab</Link></header>
        <div className="squad-workspace">
            <LineupEditor players={selectedPlayers} lineup={lineup} onChange={onLineupChange} />
            <aside className="squad-tools">
                <section className="panel squad-budget"><h2>Team details</h2><dl><div><dt>Squad</dt><dd>{selectedPlayers.length} / 15</dd></div><div><dt>Market value</dt><dd>£{(value / 10).toFixed(1)}m</dd></div></dl><label className="field"><span>Bank / £m</span><input type="number" min="0" step="0.1" value={bankMillions} onChange={event => setBankMillions(event.target.value)} /></label><p className="small-note">Shared with Transfer Lab. Market price changes do not alter your bank.</p></section>
                <details className="panel squad-import" open={selectedPlayers.length === 0 ? true : undefined}><summary>Import from FPL</summary><TeamImport onImport={onImport} initialTeamId={importedTeam?.entry_id} /></details>
                {importedTeam && <section className="squad-source" aria-label="Imported squad source"><h3>{importedTeam.team_name}</h3><p className="small-note">#{importedTeam.entry_id} · {importedTeam.season}<br />As of the GW{importedTeam.gameweek} deadline<br />{new Date(importedTeam.deadline_time).toLocaleDateString()}</p><p className="small-note">Later transfers may not be included.{importedTeam.edited ? " Squad edited since import." : ""}</p></section>}
                <p className="small-note">Choose 1 goalkeeper, at least 3 defenders, 2 midfielders and 1 forward in your starting XI.</p>
            </aside>
        </div>
        <details className="panel squad-edit" open={selectedPlayers.length < 15 ? true : undefined}><summary>Edit squad <span className="small-note">Add or remove players · {selectedPlayers.length} / 15</span></summary><div className="squad-picker"><PlayerPicker players={availablePlayers} selectedPlayers={selectedPlayers} onAddPlayer={onAddPlayer} onRemovePlayer={onRemovePlayer} disabled={disabled} /></div></details>
    </div>;
}
