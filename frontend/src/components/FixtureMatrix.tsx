import "./FixtureMatrix.css";

// Illustrative fixtures transcribed from the design, not a live schedule.
const demoClubs = [
    ["Arsenal", "BRE H 1", "BHA A 3", "CHE H 5", "COV A 2", "CRY H 4"],
    ["Aston Villa", "BHA H 2", "CHE A 4", "COV H 1", "CRY A 3", "EVE H 5"],
    ["Bournemouth", "CHE H 3", "COV A 5", "CRY H 2", "EVE A 4", "FUL H 1"],
    ["Brentford", "COV H 4", "CRY A 1", "EVE H 3", "FUL A 5", "HUL H 2"],
    ["Brighton", "CRY H 5", "EVE A 2", "FUL H 4", "HUL A 1", "IPS H 3"],
    ["Chelsea", "EVE H 1", "FUL A 3", "BLANK", "IPS A 2", "LEE H 4"],
    ["Coventry City", "FUL H 2", "HUL A 4", "IPS H 1", "LEE A 3", "LIV H 5"],
    ["Crystal Palace", "HUL H 3", "IPS A 5", "LEE H 2", "LIV A 4", "MCI H 1"],
    ["Everton", "IPS H 4", "LEE A 1", "LIV H 3", "MCI A 5", "MUN H 2"],
    ["Fulham", "LEE H 5", "LIV A 2", "MCI H 4", "MUN A 1", "NEW H 3"],
    ["Hull City", "LIV H 1", "MCI A 3", "MUN H 5", "NEW A 2", "NFO H 4"],
    ["Ipswich Town", "MCI H 2", "MUN A 4", "NEW H 1", "NFO A 3", "TOT H 5"],
    ["Leeds", "MUN H 3", "NEW A 5", "NFO H 2", "TOT A 4", "SUN H 1"],
    ["Liverpool", "NEW H 4", "NFO A 1", "TOT H 3", "SUN A 5", "ARS H 2"],
    ["Man City", "NFO H 5", "TOT A 2", "SUN H 4", "ARS A 1", "AVL H 3"],
    ["Man Utd", "TOT H 1", "SUN A 3", "ARS H 5", "AVL A 2", "BOU H 4"],
    ["Newcastle", "SUN H 2", "ARS A 4", "AVL H 1", "BOU A 3", "BRE H 5"],
    ["Nott’m Forest", "ARS H 3", "AVL A 5", "BOU H 2", "BRE A 4", "BHA H 1"],
    ["Spurs", "AVL H 4", "BOU A 1", "BRE H 3", "BHA A 5", "CHE H 2"],
    ["Sunderland", "BOU H 5", "BRE A 2", "BHA H 4", "CHE A 1", "COV H 3"],
];

const runwayClubs = [
    ["Arsenal", "NEW H 2", "FUL A 3", "AVL H 4", "CHE A 2", "SUN H 1"],
    ["Liverpool", "CRY A 3", "MUN H 4", "BHA A 2", "FUL H 1", "AVL A 2"],
    ["Man City", "AVL H 4", "BRE A 2", "SUN H 1", "ARS A 2", "EVE H 3"],
    ["Chelsea", "FUL A 2", "NEW H 1", "ARS H 2", "LIV A 3", "LEE H 4"],
];

export default function FixtureMatrix({ compact = false }: { compact?: boolean }) {
    return (
        <div className="planner-matrix-scroll">
            <table className={`planner-matrix${compact ? " planner-matrix--compact" : ""}`}>
                <thead><tr><th scope="col">CLUB</th>{[6, 7, 8, 9, 10].map(week => <th scope="col" key={week}>{compact ? "GW" : "GAMEWEEK"} {week}</th>)}</tr></thead>
                <tbody>{(compact ? runwayClubs : demoClubs).map(([club, ...fixtures], index) => <tr key={club}>
                    <th scope="row">{!compact && `${String(index + 1).padStart(2, "0")} `}{club}</th>
                    {fixtures.map((fixture, column) => {
                        const [opponent, venue, rating] = fixture.split(" ");
                        // The overview uses the design's column highlights.
                        const tone = opponent === "BLANK" ? "blank" : compact ? ["easy", "easy", "medium", "hard", "easy"][column] : Number(rating) <= 2 ? "easy" : rating === "3" ? "medium" : "hard";
                        return <td key={column}><span className={`planner-fixture planner-fixture--${tone}`}><span>{opponent}{venue && ` · ${venue}`}</span><span>{rating ?? "—"}</span></span></td>;
                    })}
                </tr>)}</tbody>
            </table>
        </div>
    );
}
