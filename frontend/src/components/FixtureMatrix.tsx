import "./FixtureMatrix.css";

interface DemoFixture {
    label: string;
    tone: "standard" | "warning" | "blank";
}

interface DemoClub {
    club: string;
    fixtures: DemoFixture[];
}

const gameweeks = [12, 13, 14, 15, 16];

const demoClubs: DemoClub[] = [
    {
        club: "North London",
        fixtures: [
            { label: "SOU (H) · 2", tone: "warning" },
            { label: "MCR (A) · 4", tone: "standard" },
            { label: "WES (H) · 3", tone: "standard" },
            { label: "NOR (A) · 5", tone: "warning" },
            { label: "EAS (H) · 2", tone: "standard" },
        ],
    },
    {
        club: "Merseyside",
        fixtures: [
            { label: "MCR (A) · 4", tone: "standard" },
            { label: "WES (H) · 3", tone: "standard" },
            { label: "NOR (A) · 5", tone: "warning" },
            { label: "WES (H) / NOR (A)", tone: "standard" },
            { label: "SOU (H) · 2", tone: "standard" },
        ],
    },
    {
        club: "West London",
        fixtures: [
            { label: "WES (H) · 3", tone: "standard" },
            { label: "NOR (A) · 5", tone: "warning" },
            { label: "BLANK", tone: "blank" },
            { label: "SOU (H) · 2", tone: "standard" },
            { label: "MCR (A) · 4", tone: "warning" },
        ],
    },
    {
        club: "Manchester",
        fixtures: [
            { label: "NOR (A) · 5", tone: "warning" },
            { label: "EAS (H) · 2", tone: "standard" },
            { label: "SOU (H) · 2", tone: "standard" },
            { label: "MCR (A) · 4", tone: "warning" },
            { label: "WES (H) · 3", tone: "standard" },
        ],
    },
    {
        club: "South Coast",
        fixtures: [
            { label: "EAS (H) · 2", tone: "standard" },
            { label: "SOU (H) · 2", tone: "standard" },
            { label: "MCR (A) · 4", tone: "warning" },
            { label: "WES (H) · 3", tone: "standard" },
            { label: "NOR (A) · 5", tone: "standard" },
        ],
    },
];

export default function FixtureMatrix() {
    return (
        <div className="planner-matrix-scroll">
            <table className="planner-matrix">
                <thead>
                    <tr>
                        <th scope="col">CLUB</th>

                        {gameweeks.map((gameweek) => (
                            <th key={gameweek} scope="col">
                                GW {gameweek}
                            </th>
                        ))}
                    </tr>
                </thead>

                <tbody>
                    {demoClubs.map((row) => (
                        <tr key={row.club}>
                            <th scope="row">{row.club}</th>

                            {row.fixtures.map((fixture, index) => (
                                <td key={index}>
                                    <span
                                        className={
                                            `planner-fixture planner-fixture--${fixture.tone}`
                                        }
                                    >
                                        {fixture.label}
                                    </span>
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}