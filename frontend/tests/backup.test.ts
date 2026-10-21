import { test } from "node:test";
import assert from "node:assert/strict";
import { parseBackup } from "../src/utils/backup.ts";
const value = {
  version: 1,
  season: "2026/27",
  squadIds: [1, 2],
  lineup: { starters: [1], bench: [2] },
  bank: "0.1",
  freeTransfers: "1",
  gameweek: "7",
  sellingPrices: { 1: "4.5" },
};
test("backups preserve IDs and explicit transfer settings", () =>
  assert.deepEqual(parseBackup(JSON.stringify(value), "2026/27", [1, 2]), {
    ...value,
    lineup: { ...value.lineup, captainId: undefined, viceCaptainId: undefined },
  }));
test("invalid backups are rejected before any browser state is changed", () => {
  for (const change of [
    { version: 2 },
    { season: "2025/26" },
    { squadIds: [1, 1] },
    { squadIds: [999] },
    { bank: "-1" },
    { bank: "1.23" },
    { freeTransfers: "6" },
    { gameweek: "39" },
    { lineup: { starters: [1], bench: [1] } },
    { sellingPrices: { 3: "4.5" } },
    { sellingPrices: { 1: "oops" } },
  ])
    assert.throws(() => parseBackup(JSON.stringify({ ...value, ...change }), "2026/27", [1, 2]));
  assert.throws(() => parseBackup("oops", "2026/27", [1, 2]));
  assert.throws(() => parseBackup(" ".repeat(65537), "2026/27", [1, 2]));
});
