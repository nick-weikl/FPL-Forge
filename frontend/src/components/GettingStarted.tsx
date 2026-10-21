import { Link } from "react-router";
export default function GettingStarted({ onDismiss }: { onDismiss: () => void }) {
  return (
    <section className="panel welcome-guide" aria-labelledby="welcome-title">
      <div className="panel-heading">
        <h2 id="welcome-title">Your first gameweek with FPL Forge</h2>
        <button type="button" className="text-button" onClick={onDismiss}>
          Hide guide
        </button>
      </div>
      <ol>
        <li>
          <strong>Bring in your squad</strong>
          <p>On My Squad, import your public FPL team ID or add players manually.</p>
        </li>
        <li>
          <strong>Choose your matchday team</strong>
          <p>Pick 11 starters, order the bench, and check your captain and vice-captain.</p>
        </li>
        <li>
          <strong>Compare your next move</strong>
          <p>
            In Transfer Lab, check your bank, free transfers and selling values before running
            analysis.
          </p>
        </li>
      </ol>
      <div className="guide-actions">
        <Link to="/squad" className="forge-button">
          Set up my squad
        </Link>
        <Link to="/help">Where do I find my team ID?</Link>
      </div>
      <p className="small-note">
        No account needed. Your squad is saved only in this browser. Download a backup in Help
        before changing devices or clearing browser data.
      </p>
    </section>
  );
}
