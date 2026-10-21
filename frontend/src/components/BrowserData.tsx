import { useState } from "react";
import type { SquadBackup } from "../utils/backup";
import { parseBackup } from "../utils/backup";
export default function BrowserData({
  backup,
  availableIds,
  onRestore,
}: {
  backup: SquadBackup;
  availableIds: number[];
  onRestore: (backup: SquadBackup) => void;
}) {
  const [preview, setPreview] = useState<SquadBackup | null>(null);
  const [message, setMessage] = useState("");
  function download() {
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(backup, null, 2)], { type: "application/json" }),
    );
    const link = document.createElement("a");
    link.href = url;
    link.download = "fpl-forge-squad.json";
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    setMessage("Backup downloaded. Keep this file private if you share your device.");
  }
  return (
    <section className="panel help-section" aria-labelledby="browser-data-title">
      <h2 id="browser-data-title">Your browser data</h2>
      <p>
        There is no account or cloud backup. Clearing site data, using a private window, or changing
        browser or device can remove access to your saved squad. A backup includes your squad,
        lineup and transfer settings; restoring uses current player data.
      </p>
      <div className="guide-actions">
        <button
          className="forge-button forge-button--secondary"
          type="button"
          disabled={!backup.season}
          onClick={download}
        >
          Download backup
        </button>
        <label className="backup-upload">
          Restore a backup
          <input
            type="file"
            accept=".json,application/json"
            disabled={!availableIds.length}
            onChange={async (event) => {
              const file = event.target.files?.[0];
              event.target.value = "";
              setPreview(null);
              setMessage("");
              if (!file) return;
              try {
                if (file.size > 65536) throw new Error("Choose a backup smaller than 64 KB.");
                setPreview(parseBackup(await file.text(), backup.season, availableIds));
              } catch (error) {
                setMessage(error instanceof Error ? error.message : "Could not read this backup.");
              }
            }}
          />
        </label>
      </div>
      {!availableIds.length && (
        <p className="small-note">Load season data before restoring a backup.</p>
      )}
      {preview && (
        <div className="backup-preview">
          <p>
            Restore {preview.squadIds.length} players, a £{Number(preview.bank).toFixed(1)}m bank
            and transfer settings from {preview.season}? This replaces your current browser
            selection.
          </p>
          <div className="guide-actions">
            <button
              className="forge-button"
              onClick={() => {
                onRestore(preview);
                setPreview(null);
                setMessage("Backup restored. Check My Squad and your transfer settings.");
              }}
            >
              Confirm restore
            </button>
            <button className="text-button" onClick={() => setPreview(null)}>
              Cancel
            </button>
          </div>
        </div>
      )}
      {message && <p role="status">{message}</p>}
    </section>
  );
}
