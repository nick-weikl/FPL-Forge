import type { Fixture, Team } from "../types/dashboard";
import "./FixtureMatrix.css";

interface Props {
    teams: Team[];
    fixtures: Fixture[];
    startGameweek: number;
    horizon?: number;
    compact?: boolean;
    visibleTeamIds?: number[];
}

export default function FixtureMatrix({teams, fixtures, startGameweek, horizon = 5, compact = false, visibleTeamIds}: Props) {
    const weeks = Array.from({length: Math.min(horizon, 39 - startGameweek)}, (_, i) => startGameweek + i);
    const byId = new Map(teams.map(team => [team.id, team]));
    return <div className="planner-matrix-scroll">
        <table className={`planner-matrix${compact ? " planner-matrix--compact" : ""}`}>
            <thead><tr><th scope="col">CLUB</th>{weeks.map(week => <th scope="col" key={week}>{compact ? "GW" : "GAMEWEEK"} {week}</th>)}</tr></thead>
            <tbody>{teams.filter(team => !visibleTeamIds || visibleTeamIds.includes(team.id)).map((team, index) => <tr key={team.id}>
                <th scope="row">{!compact && `${String(index + 1).padStart(2, "0")} `}{team.name}</th>
                {weeks.map(week => {
                    const matches = fixtures.filter(fixture => fixture.gameweek === week && (fixture.home_team_id === team.id || fixture.away_team_id === team.id));
                    return <td key={week}>{matches.length ? matches.map(fixture => {
                        const home = fixture.home_team_id === team.id;
                        const opponent = byId.get(home ? fixture.away_team_id : fixture.home_team_id);
                        const rating = home ? fixture.home_difficulty : fixture.away_difficulty;
                        const tone = rating == null ? "blank" : rating <= 2 ? "easy" : rating === 3 ? "medium" : "hard";
                        const score = fixture.status === "FT" && fixture.home_score != null && fixture.away_score != null
                            ? `${home ? fixture.home_score : fixture.away_score}–${home ? fixture.away_score : fixture.home_score}` : null;
                        return <span key={fixture.id} className={`planner-fixture planner-fixture--${tone}`} title={`${team.name} v ${opponent?.name ?? "Unknown club"} · ${new Date(fixture.fixture_date).toLocaleString()} · ${fixture.status ?? "Status unavailable"}`}>
                            <span>{opponent?.short_name ?? "—"} · {home ? "H" : "A"}{score && ` · ${score}`}</span><span aria-label={`Estimated difficulty ${rating ?? "unavailable"}`}>{rating ?? "—"}</span>
                        </span>;
                    }) : <span className="planner-fixture planner-fixture--blank">BLANK</span>}</td>;
                })}
            </tr>)}</tbody>
        </table>
    </div>;
}
