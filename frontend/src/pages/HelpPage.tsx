import { Link } from "react-router";
import BrowserData from "../components/BrowserData";
import type { SquadBackup } from "../utils/backup";
export default function HelpPage(props: {
  backup: SquadBackup;
  availableIds: number[];
  onRestore: (backup: SquadBackup) => void;
}) {
  return (
    <div className="page-stack help-page">
      <header className="page-heading">
        <h1>Help & getting started</h1>
        <p>A guide to your squad, recommendations and saved data.</p>
      </header>
      <section className="panel help-section">
        <h2>Start with your team</h2>
        <ol>
          <li>
            <strong>Find your FPL team ID.</strong> Open the official FPL website in a browser, go
            to your Points page and look at the address: <code>/entry/123456/event/7/</code>. In
            this example, your ID is <strong>123456</strong>. It is not your league code. Never
            enter your FPL password here.
          </li>
          <li>
            On <Link to="/squad">My Squad</Link>, open “Import from FPL”, enter the ID and preview
            your players before confirming. You can also add 15 players manually under “Edit squad”.
          </li>
          <li>
            Select a starter on the pitch, then a highlighted substitute to swap. Set your captain
            and vice-captain, and use the bench arrows for priority.
          </li>
          <li>
            In <Link to="/transfer-lab">Transfer Lab</Link>, enter the last completed gameweek (7 if
            GW8 is next), your bank and available free transfers. Confirm selling values from your
            FPL team, then run analysis.
          </li>
        </ol>
      </section>
      <section className="panel help-section">
        <h2>What a recommendation means</h2>
        <p>
          Net gain is the estimated <strong>total over the displayed gameweek range</strong>,
          compared with keeping your starting XI. It is not a gain per week or a guaranteed result.
          Transfer hits are deducted once.
        </p>
        <p>
          The forecast uses recent official FPL points per club fixture, including non-appearances,
          and upcoming fixture counts. It is a simple baseline, not a calibrated prediction or an
          opponent-adjusted model. Injuries, rotation, future form and uncertain minutes can make
          the result inaccurate.
        </p>
        <p>
          Your XI stays fixed over the forecast horizon. Incoming players inherit the outgoing
          player’s slot and captaincy. Captain points count twice; bench points, automatic
          substitutions, vice-captain fallback and chips are excluded. Bench order is saved for
          planning.
        </p>
        <p>
          Imported squads and bank reflect a published deadline. Transfers after that deadline may
          be missing. Purchase prices, exact selling values and free transfers are not imported.
          Blank selling values use current market prices, which may overstate your budget. Nothing
          here submits transfers to FPL.
        </p>
      </section>
      <BrowserData {...props} />
      <section className="panel help-section">
        <h2>Privacy & accessibility</h2>
        <p>
          Your squad, lineup, bank, selling values, guide preference and theme are saved in this
          browser. To run analysis, selected player IDs and transfer settings are sent to the FPL
          Forge backend. Team imports send your public team ID to the backend, which requests its
          public deadline snapshot from FPL. The app does not create user accounts or store these
          user selections in its database. Hosting infrastructure may keep request logs; do not
          enter private credentials.
        </p>
        <p>
          There are no advertising or analytics trackers in the app. Fonts load from your device,
          without a third-party font request. Choose light, dark or system theme in the header. All
          lineup controls work with a keyboard, with visible focus outlines; wide data tables scroll
          horizontally.
        </p>
        <p className="small-note">
          FPL Forge is an independent planning tool and is not affiliated with the Premier League or
          Fantasy Premier League.
        </p>
      </section>
    </div>
  );
}
