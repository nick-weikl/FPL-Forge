import { useState } from "react";
import type { Dashboard } from "../types/dashboard";
import FixtureMatrix from "../components/FixtureMatrix";
import "./FixturePlannerPage.css";

export default function FixturePlannerPage({data}: {data: Dashboard}) {
    const [start, setStart] = useState(data.next_gameweek ?? 38);
    const [horizon, setHorizon] = useState(5);
    const [club, setClub] = useState("");
    const fixtures = data.fixtures.filter(f => !club || f.home_team_id === Number(club) || f.away_team_id === Number(club));
    return <div className="planner-page page-stack">
        <header className="page-heading"><p className="eyebrow">FIXTURE PLANNER / {data.season}</p><h1>Read the run. Find the window.</h1><p>Stored fixtures and results, with an adjustable gameweek window.</p></header>
        <div className="planner-controls">
            <label className="field"><span className="eyebrow">STARTING GAMEWEEK</span><select value={start} onChange={event => setStart(Number(event.target.value))}>{Array.from({length: 38}, (_, i) => i + 1).map(week => <option key={week} value={week}>{week}</option>)}</select></label>
            <label className="field"><span className="eyebrow">HORIZON</span><select value={horizon} onChange={event => setHorizon(Number(event.target.value))}>{[1,3,5,10].map(n => <option key={n} value={n}>{n} gameweek{n === 1 ? "" : "s"}</option>)}</select></label>
            <label className="field"><span className="eyebrow">CLUB</span><select value={club} onChange={event => setClub(event.target.value)}><option value="">All clubs</option>{data.teams.map(team => <option key={team.id} value={team.id}>{team.name}</option>)}</select></label>
            <div className="planner-legend"><span className="eyebrow">EST. DIFFICULTY</span>{[1,2,3,4,5].map(rating => <span key={rating} className={`legend-rating legend-rating--${rating}`}>{rating}</span>)}</div>
        </div>
        <section className="panel planner-matrix-panel" aria-label="Database fixture schedule">
            {data.teams.length ? <div>
                <FixtureMatrix teams={data.teams} fixtures={fixtures} startGameweek={start} horizon={horizon} visibleTeamIds={club ? [Number(club)] : undefined} />
            </div> : <p>No clubs are available for this season.</p>}
            <div className="planner-note"><p className="eyebrow">H = HOME / A = AWAY / SCORES SHOWN FROM THE CLUB’S PERSPECTIVE</p><p className="small-note">{data.difficulty_description} Blank and double gameweeks reflect the stored schedule. Fixtures without a gameweek are excluded from the grid.</p>
                {data.fixtures.some(f => f.gameweek === null) && <p className="small-note">{data.fixtures.filter(f => f.gameweek === null).length} fixtures are awaiting a gameweek assignment.</p>}
            </div>
        </section>
    </div>;
}
