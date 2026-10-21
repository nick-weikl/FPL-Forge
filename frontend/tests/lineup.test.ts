import { test } from "node:test";
import assert from "node:assert/strict";
import { formations, moveSubstitute, readLineup, reconcileLineup, swapStarter, validStarters } from "../src/utils/lineup.ts";
import type { Player } from "../src/types/player.ts";
const players: Player[] = ["Goalkeeper", "Goalkeeper", ...Array(5).fill("Defender"), ...Array(5).fill("Midfielder"), ...Array(3).fill("Attacker")].map((position, index) => ({id: index + 1, position, name: `Player ${index + 1}`, team_id: index, team_name: "Club", external_api_id: null, price_tenths: 50}));
const empty = {starters: [], bench: []};
test("all legal formations pass; duplicate, missing and invalid position selections fail", () => {
    for (const formation of formations) {
        const ids = [1, ...["Defender", "Midfielder", "Attacker"].flatMap((role, i) => players.filter(p => p.position === role).slice(0, formation[i]).map(p => p.id))];
        assert.equal(validStarters(ids, players), true);
    }
    for (const ids of [[1,2,3,4,5,6,7,8,9,10,11], [1,3,4,8,9,10,11,12,13,14,15], [1,3,4,5,8,9,10,11,13,14,99], Array(11).fill(1)]) assert.equal(validStarters(ids, players), false);
});
test("default complete squads get 3-4-3 and a separate reserve goalkeeper", () => {
    const lineup = reconcileLineup(empty, players);
    assert.equal(validStarters(lineup.starters, players), true);
    assert.deepEqual(lineup.bench, [2,6,7,12]);
});
test("swaps enforce formation and goalkeeper rules while allowing formation changes", () => {
    const lineup = reconcileLineup(empty, players);
    for (const [outgoing, incoming] of [[3,12],[3,2],[99,12]]) assert.equal(swapStarter(lineup, outgoing, incoming, players), lineup);
    const swapped = swapStarter(lineup, 13, 12, players);
    assert.equal(validStarters(swapped.starters, players), true);
    assert.equal(swapped.starters.includes(12), true);
    assert.equal(swapped.bench.includes(13), true);
    assert.equal(swapStarter(lineup, 1, 2, players).bench[0], 1);
});
test("bench priority moves preserve goalkeeper separation and boundaries", () => {
    const lineup = reconcileLineup(empty, players);
    const moved = moveSubstitute(lineup, 12, -1, players);
    assert.deepEqual(moved.bench, [2,6,12,7]);
    assert.deepEqual(moveSubstitute(moved, 12, 1, players), lineup);
    assert.equal(moveSubstitute(lineup, 6, -1, players), lineup);
    assert.equal(moveSubstitute(lineup, 2, 1, players), lineup);
});
test("saved swaps and priority survive reload and price refresh", () => {
    const lineup = moveSubstitute(swapStarter(reconcileLineup(empty, players), 13, 12, players), 13, -1, players);
    assert.deepEqual(reconcileLineup(readLineup(JSON.stringify(lineup)), players.map(p => ({...p, price_tenths: 99}))), lineup);
});
test("removed players, replacements and position changes reconcile safely", () => {
    const lineup = reconcileLineup(empty, players);
    assert.equal(reconcileLineup(lineup, players.filter(p => p.id !== 3)).starters.includes(3), false);
    const replacement = [...players.filter(p => p.id !== 3), {...players[2], id: 99}];
    const repaired = reconcileLineup(lineup, replacement);
    assert.equal(validStarters(repaired.starters, replacement), true);
    assert.equal(new Set([...repaired.starters,...repaired.bench]).size, 15);
    const changed = players.map(p => p.id === 3 ? {...p, position: "Midfielder"} : p.id === 8 ? {...p, position: "Defender"} : p);
    assert.equal(validStarters(reconcileLineup(lineup, changed).starters, changed), true);
});
test("malformed storage and stale or duplicate IDs cannot corrupt the XI", () => {
    for (const value of [null, "bad", "{}", '{"starters": ["1"], "bench": []}']) assert.deepEqual(readLineup(value), empty);
    const lineup = reconcileLineup({starters: [999,1,1], bench: [999,2,2]}, players);
    assert.equal(validStarters(lineup.starters, players), true);
    assert.equal(new Set([...lineup.starters,...lineup.bench]).size, 15);
});
