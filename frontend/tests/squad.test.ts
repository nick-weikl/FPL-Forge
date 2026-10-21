import { test } from "node:test";
import assert from "node:assert/strict";
import { reconcilePlayers } from "../src/utils/squad.ts";
import type { Player } from "../src/types/player.ts";

const saved: Player = {
  id: 1,
  name: "Old name",
  team_id: 1,
  team_name: "Old club",
  position: "Defender",
  price_tenths: 45,
  external_api_id: null,
};
const current: Player = {
  ...saved,
  name: "Current name",
  team_id: 2,
  team_name: "Current club",
  price_tenths: 50,
};

test("saved players use current database prices, names and clubs", () => {
  assert.deepEqual(reconcilePlayers([saved], [current]), [current]);
});
test("unavailable IDs are removed, allowing an obsolete squad to be rebuilt", () => {
  assert.deepEqual(reconcilePlayers([{ ...saved, id: 99 }], [current]), []);
});
test("duplicate saved IDs cannot inflate the squad", () => {
  assert.deepEqual(reconcilePlayers([saved, saved], [current]), [current]);
});
test("stored order is preserved while using the current roster", () => {
  const second = { ...current, id: 2 };
  assert.deepEqual(reconcilePlayers([second, saved], [current, second]), [second, current]);
});
