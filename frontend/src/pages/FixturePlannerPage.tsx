import "./FixturePlannerPage.css";
import FixtureMatrix from "../components/FixtureMatrix";

export default function FixturePlannerPage() {
    return (
        <div className="planner-page page-stack">
            <header className="page-heading"><p className="eyebrow">FIXTURE PLANNER</p><h1>Read the run. Find the window.</h1><p>A league-wide view of the next five gameweeks.</p></header>
            <div className="planner-controls">
                <label className="field"><span className="eyebrow">STARTING GAMEWEEK</span><input value="6" disabled /></label>
                <label className="field"><span className="eyebrow">HORIZON</span><select disabled><option>5 gameweeks</option></select></label>
                <label className="field"><span className="eyebrow">CLUB</span><select disabled><option>All clubs</option></select></label>
                <div className="planner-legend"><span className="eyebrow">DIFFICULTY</span>{[1, 2, 3, 4, 5].map(rating => <span key={rating} className={`legend-rating legend-rating--${rating}`}>{rating}</span>)}</div>
            </div>
            <section className="panel planner-matrix-panel" aria-label="Illustrative five-gameweek fixtures">
                <FixtureMatrix />
                <div className="planner-note"><p className="eyebrow">H = HOME / A = AWAY</p><p className="small-note">Blank and double gameweeks stay visible. Fixture examples are illustrative.</p></div>
            </section>
        </div>
    );
}
