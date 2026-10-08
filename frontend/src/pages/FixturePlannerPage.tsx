import "./FixturePlannerPage.css";
import FixtureMatrix from "../components/FixtureMatrix";


export default function FixturePlannerPage() {
    return (
        <div className="planner-page">
            <header className="page-heading">
                <div className="context-bar">
                    <p>WORKSPACE / FIXTURE PLANNER</p>
                    <p>Demo GW 12 / Nick</p>
                </div>

                <h1>See the run ahead.</h1>
                <p>
                    Look beyond one gameweek. Compare a five-week
                    fixture horizon.
                </p>
            </header>

            <div className="planner-controls">
                <button type="button" disabled>
                    GW 12–16
                </button>
                <button type="button" disabled>
                    Five-week view
                </button>
                <button type="button" disabled>
                    All clubs
                </button>
            </div>

            <section className="planner-matrix-panel">
                <h2>Fixture difficulty · Forge method v0.1</h2>

                <div className="planner-matrix-scroll">
                    <FixtureMatrix />
                </div>

                <p className="planner-note">
                    H = home · A = away · 1 easy → 5 hard · Text
                    labels accompany every rating.
                </p>
            </section>

            <div className="planner-details">
                <section className="planner-fixture-detail">
                    <h2>Merseyside has two fixtures in GW 15</h2>

                    <div className="planner-match-row">
                        <p>Merseyside vs West London</p>
                        <p>HOME</p>
                        <p>Scheduled</p>
                    </div>

                    <div className="planner-match-row">
                        <p>North London vs Merseyside</p>
                        <p>AWAY</p>
                        <p>Scheduled</p>
                    </div>

                    <p className="planner-description">
                        Gameweek mapping is reviewed separately from
                        provider round labels.
                    </p>
                </section>

                <section className="planner-schedule-note">
                    <h2>Dates can move</h2>

                    <p className="planner-description">
                        Postponed matches remain visible. Unknown
                        kickoffs and unmapped weeks are labelled, and
                        affected projections are marked incomplete.
                    </p>

                    <div className="planner-blank-note">
                        <p>Blank GW 14 · West London</p>
                        <p>No fixture in the demo mapping</p>
                    </div>
                </section>
            </div>

            <p className="planner-note">
                ILLUSTRATIVE DESIGN DATA · Hardcoded fixtures and
                ratings · Forge estimates are not official FPL points.
            </p>
        </div>
    );
}