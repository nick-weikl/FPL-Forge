import FixtureMatrix from "../components/FixtureMatrix";
import "./OverviewPage.css";

export default function OverviewPage() {
    return (
        <div className="overview-page page-stack">
            <div className="overview-hero">
                <header className="overview-intro">
                    <p className="overview-badge eyebrow">THE GAMEWEEK BRIEF</p>
                    <h1>Your edge,<br />next gameweek.</h1>
                    <p>Know your squad. Read the fixtures.<br />Make the move that earns its place.</p>
                    <div className="overview-actions">
                        <button className="forge-button" disabled>Open my squad</button>
                        <button className="forge-button forge-button--secondary" disabled>Explore players</button>
                    </div>
                </header>
                <section className="overview-context panel" aria-label="Sample gameweek">
                    <div className="overview-gameweek"><strong>06</strong><div><p className="eyebrow accent">NEXT UP</p><h2>Your plan<br />starts here.</h2><p className="small-note">Sample gameweek</p></div></div>
                    <hr className="rule" />
                    <div className="metrics"><div><p className="eyebrow">FREE TRANSFERS</p><p className="metric-value">1</p></div><div><p className="eyebrow">IN THE BANK</p><p className="metric-value">£1.0m</p></div></div>
                </section>
            </div>
            <section className="overview-next-move">
                <div><p className="eyebrow">YOUR NEXT MOVE / SINGLE TRANSFER</p><h2>J. Timber → A. Robinson</h2></div>
                <div><p className="overview-gain">+4.61</p><p className="eyebrow">NET FORGE SCORE GAIN</p></div>
                <button className="forge-button forge-button--secondary" disabled>Open Transfer Lab</button>
            </section>
            <div className="overview-planning">
                <section className="panel overview-runway"><div className="panel-heading"><h2>The fixture runway</h2><p className="eyebrow">GW 06 — 10</p></div><FixtureMatrix compact /></section>
                <section className="panel overview-squad">
                    <div className="overview-squad-count"><strong>15</strong><p className="eyebrow">PLAYERS<br />SELECTED</p></div>
                    <hr className="rule" />
                    <div><span>Goalkeepers</span><span className="eyebrow accent">2 / 2</span></div>
                    <div><span>Defenders</span><span className="eyebrow accent">5 / 5</span></div>
                    <div><span>Midfielders</span><span className="eyebrow accent">5 / 5</span></div>
                    <div><span>Forwards</span><span className="eyebrow accent">3 / 3</span></div>
                </section>
            </div>
        </div>
    );
}
