import { useEffect, useRef, useState } from "react";
import { previewTeamImport } from "../services/api";
import { parseTeamId } from "../utils/teamImport";
import type { TeamImportPreview } from "../types/teamImport";

export default function TeamImport({onImport, initialTeamId}: {onImport: (preview: TeamImportPreview) => void; initialTeamId?: number}) {
    const [teamId, setTeamId] = useState(initialTeamId?.toString() ?? "");
    const [preview, setPreview] = useState<TeamImportPreview | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const controller = useRef<AbortController | null>(null);
    useEffect(() => () => controller.current?.abort(), []);
    async function loadPreview(event: React.SubmitEvent<HTMLFormElement>) {
        event.preventDefault();
        const id = parseTeamId(teamId);
        setError(null); setPreview(null);
        if (id === null) { setError("Enter a positive numeric FPL team ID, such as 123456."); return; }
        controller.current?.abort();
        const request = new AbortController(); controller.current = request;
        setLoading(true);
        try {
            const response = await previewTeamImport(id, request.signal);
            if (!request.signal.aborted) setPreview(response);
        } catch (error) {
            if (!request.signal.aborted) setError(error instanceof Error ? error.message : "Could not import this team.");
        } finally { if (!request.signal.aborted) setLoading(false); }
    }
    return <section className="panel team-import" aria-labelledby="team-import-heading">
        <h2 id="team-import-heading">Import your FPL squad</h2>
        <p className="small-note">Enter your team ID from the address of your FPL Points page: /entry/<strong>123456</strong>/event/7/. No sign-in is required. Your squad stays unchanged until you confirm the preview.</p>
        <form onSubmit={loadPreview} className="team-import-form">
            <label className="field"><span className="eyebrow">FPL TEAM ID</span><input inputMode="numeric" value={teamId} disabled={loading} placeholder="123456" onChange={event => {setTeamId(event.target.value); setPreview(null); setError(null);}} /></label>
            <button className="forge-button" type="submit" disabled={loading}>{loading ? "Fetching squad…" : "Preview squad"}</button>
        </form>
        {loading && <p role="status">Loading the latest published deadline squad from FPL…</p>}
        {error && <p className="forge-state forge-state--error" role="alert">{error}</p>}
        {preview && <div className="team-import-preview" aria-label="Imported squad preview">
            <h3>{preview.team_name} · #{preview.entry_id}</h3>
            <p>As of the GW{preview.gameweek} deadline · {new Date(preview.deadline_time).toLocaleString()} · {preview.season}</p>
            <p><strong>Recorded bank: £{(preview.bank_tenths / 10).toFixed(1)}m</strong> · {preview.players.length} players</p>
            <div className="team-import-scroll"><table>
                <thead><tr><th scope="col">Player</th><th scope="col">Club</th><th scope="col">Position</th><th scope="col">Current price</th></tr></thead>
                <tbody>{preview.players.map(player => <tr key={player.id}><th scope="row">{player.name}</th><td>{player.team_name}</td><td>{player.position}</td><td>{player.price_tenths == null ? "—" : `£${(player.price_tenths / 10).toFixed(1)}m`}</td></tr>)}</tbody>
            </table></div>
            <ul className="small-note">{preview.warnings.map(warning => <li key={warning}>{warning}</li>)}</ul>
            <p className="small-note">Confirming replaces your selected squad and bank. Free transfers remain unchanged; review them in Transfer Lab. Selling values still need confirmation.</p>
            <div className="team-import-actions"><button className="forge-button" onClick={() => {onImport(preview); setPreview(null);}}>Replace my squad and bank</button><button className="forge-button forge-button--secondary" onClick={() => setPreview(null)}>Cancel</button></div>
        </div>}
    </section>;
}
