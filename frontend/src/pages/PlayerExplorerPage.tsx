import "./PlayerExplorerPage.css";

const demoPlayers = [
    {
        name: "Ellis",
        club: "North London",
        position: "MID",
        price: "£7.2m",
        minutes: 421,
        goals: 3,
        rank: 1,
    },
    {
        name: "Rowan",
        club: "Merseyside",
        position: "FWD",
        price: "£8.1m",
        minutes: 438,
        goals: 4,
        rank: 2,
    },
    {
        name: "Hayes",
        club: "West London",
        position: "MID",
        price: "£6.8m",
        minutes: 390,
        goals: 2,
        rank: 3,
    },
    {
        name: "Brooks",
        club: "South Coast",
        position: "DEF",
        price: "£4.7m",
        minutes: 450,
        goals: 0,
        rank: 4,
    },
    {
        name: "Reed",
        club: "Manchester",
        position: "MID",
        price: "£8.4m",
        minutes: 362,
        goals: 2,
        rank: 5,
    },
    {
        name: "Morgan",
        club: "East London",
        position: "MID",
        price: "£6.9m",
        minutes: 336,
        goals: 1,
        rank: 6,
    },
];

export default function PlayerExplorerPage() {
    return (
        <div className="explorer-page">
            <header className="page-heading">
                <div className="context-bar">
                    <p>WORKSPACE / PLAYER EXPLORER</p>
                    <p>Demo GW 12 / Nick</p>
                </div>

                <h1>Find the right player.</h1>
                <p>
                    Compare the underlying football performance before
                    making a fantasy decision.
                </p>
            </header>

            <div className="explorer-filters">
                <input
                    type="search"
                    placeholder="Search players…"
                    aria-label="Search players"
                    disabled
                />

                <select aria-label="Club" disabled>
                    <option>All clubs</option>
                </select>

                <select aria-label="Position" disabled>
                    <option>All positions</option>
                </select>

                <select aria-label="Match window" disabled>
                    <option>Last 5 matches</option>
                </select>
            </div>

            <div className="explorer-scope">
                <p>
                    SAMPLE SCOPE · Hardcoded demo data · Price data and
                    fantasy positions require verification
                </p>
            </div>

            <section className="explorer-results">
                <h2>Player explorer</h2>

                <div className="explorer-table-scroll">
                    <table className="explorer-table">
                        <thead>
                            <tr>
                                <th scope="col">PLAYER / CLUB</th>
                                <th scope="col">POSITION</th>
                                <th scope="col">PRICE</th>
                                <th scope="col">MINUTES</th>
                                <th scope="col">GOALS</th>
                                <th scope="col">FORGE RANK</th>
                            </tr>
                        </thead>

                        <tbody>
                            {demoPlayers.map((player) => (
                                <tr key={player.rank}>
                                    <th scope="row">
                                        {player.name} / {player.club}
                                    </th>
                                    <td>{player.position}</td>
                                    <td>{player.price}</td>
                                    <td>{player.minutes}</td>
                                    <td>{player.goals}</td>
                                    <td>{player.rank}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                <p className="explorer-note">
                    6 sample rows shown / Demo values
                </p>

                <button
                    type="button"
                    className="explorer-compare"
                    disabled
                >
                    Compare selected
                </button>
            </section>

            <div className="explorer-metric-notes">
                <section>
                    <h2>Football facts</h2>
                    <p>
                        Minutes, goals and assists will come from stored
                        match records.
                    </p>
                </section>

                <section>
                    <h2>Fantasy metadata</h2>
                    <p>
                        Position, price and eligibility will come from
                        a separately verified source.
                    </p>
                </section>

                <section>
                    <h2>Forge rank</h2>
                    <p>
                        A transparent heuristic ranking, labelled with
                        its version and scope.
                    </p>
                </section>
            </div>

            <p className="explorer-note">
                ILLUSTRATIVE DESIGN DATA · Forge estimates are not
                official FPL points.
            </p>
        </div>
    );
}