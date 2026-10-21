import { test } from "node:test";
import assert from "node:assert/strict";
import { parseTeamId, importedTeamMetadata, readImportedTeam } from "../src/utils/teamImport.ts";
import type { TeamImportPreview } from "../src/types/teamImport.ts";

test("team ID parsing accepts public numeric IDs and rejects URLs or invalid IDs", () => {
  assert.equal(parseTeamId(" 123456 "), 123456);
  for (const value of ["", "0", "-1", "1.5", "abc", "001", "https://example.com", "2147483648"])
    assert.equal(parseTeamId(value), null);
});
test("import metadata preserves a zero bank without deriving it from prices", () => {
  const preview: TeamImportPreview = {
    entry_id: 123,
    team_name: "Example",
    season: "2026/27",
    gameweek: 7,
    deadline_time: "2026-10-17T10:00:00Z",
    bank_tenths: 0,
    analysis_gameweek: 7,
    players: [],
    warnings: [],
  };
  const metadata = importedTeamMetadata(preview);
  assert.equal(metadata.bank_tenths, 0);
  assert.equal(metadata.gameweek, 7);
  assert.equal(metadata.edited, false);
});
test("missing browser storage does not break import metadata loading", () => {
  assert.equal(readImportedTeam(), null);
});
