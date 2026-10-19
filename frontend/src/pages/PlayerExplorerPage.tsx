import "./PlayerExplorerPage.css";

// Static design content. Player exploration will be implemented separately.
const demoPlayers = [
    ["Ryan Cherki", "Man City", "MID", "£7.8m", "360", "2", "7.10"],
    ["Erling Haaland", "Man City", "FWD", "£15.6m", "450", "5", "7.03"],
    ["Mohamed Salah", "Liverpool", "MID", "£12.5m", "438", "4", "6.94"],
    ["Cole Palmer", "Chelsea", "MID", "£10.0m", "421", "3", "6.89"],
    ["João Pedro", "Chelsea", "FWD", "£7.7m", "390", "3", "6.89"],
    ["Lewis Hall", "Newcastle", "DEF", "£5.3m", "405", "0", "6.69"],
    ["J. Timber", "Arsenal", "DEF", "£4.5m", "450", "1", "6.55"],
    ["J. Gvardiol", "Man City", "DEF", "£5.7m", "432", "1", "6.55"],
    ["A. Robinson", "Fulham", "DEF", "£4.5m", "450", "0", "6.52"],
    ["B. Fernandes", "Man Utd", "MID", "£11.9m", "450", "2", "6.42"],
];

export default function PlayerExplorerPage() {
    return (
        <div className="explorer-page page-stack">
            <div className="explorer-heading">
                <header className="page-heading"><p className="eyebrow">PLAYER EXPLORER</p><h1>Find your next difference-maker.</h1><p>Filter the player pool. Compare the numbers. Build your shortlist.</p></header>
                <label className="field"><span className="eyebrow">FIND A PLAYER</span><input type="search" placeholder="Search players…" disabled /></label>
            </div>
            <div className="explorer-workspace">
                <aside className="explorer-filters" aria-label="Player filters">
                    <p className="eyebrow">REFINE THE POOL</p>
                    <div className="explorer-positions">{["All positions", "Goalkeepers", "Defenders", "Midfielders", "Forwards"].map((position, index) => <button className={index === 0 ? "selected" : ""} key={position} disabled>{position}</button>)}</div>
                    <hr className="rule" />
                    <label className="field"><span className="eyebrow">CLUB</span><select disabled><option>All clubs</option></select></label>
                    <label className="field"><span className="eyebrow">MATCH WINDOW</span><select disabled><option>Last 5 matches</option></select></label>
                    <p className="small-note">Illustrative player pool<br />Sample rows for design review</p>
                </aside>
                <section className="explorer-results panel">
                    <div className="panel-heading"><h2>The player pool</h2><p className="eyebrow">10 SHOWN</p></div>
                    <div className="explorer-table-scroll"><table className="explorer-table">
                        <thead><tr>{["PLAYER", "POS", "PRICE", "MINS", "GOALS", "SCORE"].map(label => <th scope="col" key={label}>{label}</th>)}</tr></thead>
                        <tbody>{demoPlayers.map(([name, club, ...stats], index) => <tr key={name} className={index === 1 ? "is-focused" : ""}><th scope="row">{String(index + 1).padStart(2, "0")} {name}<span>{club}</span></th>{stats.map((stat, i) => <td key={i}>{stat}</td>)}</tr>)}</tbody>
                    </table></div>
                    <p className="eyebrow explorer-note">SAMPLE DATA / SCORES ARE ILLUSTRATIVE</p>
                </section>
                <aside className="explorer-focus panel">
                    <p className="eyebrow">IN FOCUS</p>
                    <div className="explorer-shirt"><img src="/figma/manchester-shirt.svg" alt="Manchester City blue shirt" /></div>
                    <h2>Erling<br />Haaland</h2>
                    <p className="eyebrow">MANCHESTER CITY / FORWARD</p>
                    <hr className="rule" />
                    <div className="metrics"><div><p className="eyebrow">PRICE</p><p className="metric-value">£15.6m</p></div><div><p className="eyebrow">FORGE SCORE</p><p className="metric-value accent">7.03</p></div></div>
                    <hr className="rule" />
                    <p className="eyebrow">RECENT MATCH MINUTES</p>
                    <div className="minutes-chart" role="img" aria-label="Illustrative minutes across five recent matches"><span /><span /><span /><span /><span /></div>
                    <div className="minutes-labels eyebrow"><span>MATCH 1</span><span>2</span><span>3</span><span>4</span><span>5</span></div>
                    <button className="forge-button forge-button--secondary" disabled>Compare selected</button>
                </aside>
            </div>
        </div>
    );
}
