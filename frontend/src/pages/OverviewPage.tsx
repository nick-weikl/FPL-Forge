import FixtureMatrix from "../components/FixtureMatrix";
import "./OverviewPage.css";

export default function OverviewPage() {
    return (
        <div className="overview-page">
            <header className="page-heading">
                <div className="context-bar">
                    <p>WORKSPACE / OVERVIEW</p>
                    <p>Demo GW 12 / Nick</p>
                </div>

                <div className="overview-heading-row">
                    <div>
                        <h1>Build your next move.</h1>
                        <p>
                            Start with the fixtures. Then find the
                            player who fits your plan.
                        </p>
                    </div>

                    <button
                        type="button"
                        className="forge-button overview-button"
                        disabled
                    >
                        Open my squad
                    </button>
                </div>
            </header>

            <div className="overview-summary">
                <section>
                    <p className="overview-label">
                        SQUAD PROJECTION
                    </p>
                    <p className="overview-metric">58.4</p>
                    <p className="overview-note">
                        Demo estimate · GW 12
                    </p>
                </section>

                <section>
                    <p className="overview-label">BANK</p>
                    <p className="overview-metric">£1.2m</p>
                    <p className="overview-note">
                        Hardcoded demo value
                    </p>
                </section>

                <section>
                    <p className="overview-label">
                        FREE TRANSFERS
                    </p>
                    <p className="overview-metric">2</p>
                    <p className="overview-note">
                        Season rule pending verification
                    </p>
                </section>
            </div>

            <div className="overview-decision-area">
                <section className="overview-transfer-card">
                    <h2>One move worth exploring</h2>

                    <p className="overview-move">
                        Morgan → Ellis
                    </p>

                    <p className="overview-description">
                        A stronger five-week outlook, with a slightly
                        higher minutes risk.
                    </p>

                    <div className="overview-transfer-measures">
                        <p>+4.8 demo score gain</p>
                        <p>£0.3m cost</p>
                        <p>5 gameweeks</p>
                    </div>

                    <button
                        type="button"
                        className="forge-button overview-button"
                        disabled
                    >
                        Review transfer
                    </button>
                </section>

                <section className="overview-coverage-card">
                    <h2>Know what is available</h2>

                    <p className="overview-description">
                        This overview uses hardcoded sample data.
                        Fantasy prices, squad values and transfer
                        suggestions are illustrative.
                    </p>

                    <div className="overview-coverage-detail">
                        <p>Hardcoded design preview</p>
                        <p>Full league coverage not confirmed</p>
                    </div>

                    <button
                        type="button"
                        className={
                            "overview-button overview-button--secondary"
                        }
                        disabled
                    >
                        Explore players
                    </button>
                </section>
            </div>

            <section className="overview-fixture-card">
                <div className="overview-fixture-heading">
                    <h2>Fixture outlook</h2>

                    <button
                        type="button"
                        className={
                            "overview-button overview-button--secondary"
                        }
                        disabled
                    >
                        View fixtures
                    </button>
                </div>

                <FixtureMatrix />
            </section>

            <p className="overview-note">
                ILLUSTRATIVE DESIGN DATA · Forge estimates are not
                official FPL points.
            </p>
        </div>
    );
}