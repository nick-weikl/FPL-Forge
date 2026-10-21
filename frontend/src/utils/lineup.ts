import type { Player } from "../types/player";

export interface Lineup { starters: number[]; bench: number[]; captainId?: number | null; viceCaptainId?: number | null }
export const formations = [[3,4,3], [3,5,2], [4,4,2], [4,3,3], [4,5,1], [5,3,2], [5,4,1]];
const roles = ["Goalkeeper", "Defender", "Midfielder", "Attacker"];

export function validStarters(ids: number[], players: Player[]): boolean {
    if (ids.length !== 11 || new Set(ids).size !== 11) return false;
    const selected = ids.map(id => players.find(player => player.id === id));
    if (selected.some(player => !player)) return false;
    const counts = roles.map(role => selected.filter(player => player?.position === role).length);
    return counts[0] === 1 && formations.some(formation => formation.every((count, index) => count === counts[index + 1]));
}

export function readLineup(value: string | null): Lineup {
    try {
        const parsed = JSON.parse(value ?? "null");
        if (parsed && [parsed.starters, parsed.bench].every(ids => Array.isArray(ids) && ids.every(id => Number.isInteger(id) && id > 0))) return parsed;
    } catch { /* Ignore unavailable or malformed saved selections. */ }
    return {starters: [], bench: []};
}

export function reconcileLineup(saved: Lineup, players: Player[]): Lineup {
    const ids = new Set(players.map(player => player.id));
    const preferred = [...new Set(saved.starters)].filter(id => ids.has(id));
    const counts = roles.map(role => players.filter(player => player.position === role).length);
    if (players.length !== 15 || counts.some((count, index) => count !== [2,5,5,3][index])) {
        return {...saved, starters: preferred, bench: [...new Set([...saved.bench, ...players.map(player => player.id)])].filter(id => ids.has(id) && !preferred.includes(id))};
    }
    let starters = validStarters(preferred, players) ? preferred : [];
    if (!starters.length) {
        const options = formations.map(formation => roles.flatMap((role, index) => {
            const ordered = [...preferred, ...players.map(player => player.id)];
            return [...new Set(ordered)].filter(id => players.find(player => player.id === id)?.position === role).slice(0, [1, ...formation][index]);
        }));
        options.sort((a, b) => b.filter(id => preferred.includes(id)).length - a.filter(id => preferred.includes(id)).length);
        starters = options[0];
    }
    const remaining = [...new Set([...saved.bench, ...players.map(player => player.id)])].filter(id => ids.has(id) && !starters.includes(id));
    const captainId = starters.includes(saved.captainId ?? -1) ? saved.captainId! : starters.find(id => players.find(player => player.id === id)?.position === "Attacker") ?? starters[0];
    const viceCaptainId = starters.includes(saved.viceCaptainId ?? -1) && saved.viceCaptainId !== captainId ? saved.viceCaptainId! : starters.find(id => id !== captainId && players.find(player => player.id === id)?.position === "Attacker") ?? starters.find(id => id !== captainId)!;
    return {starters, captainId, viceCaptainId, bench: [...remaining.filter(id => players.find(player => player.id === id)?.position === "Goalkeeper"), ...remaining.filter(id => players.find(player => player.id === id)?.position !== "Goalkeeper")]};
}

export function swapStarter(lineup: Lineup, outgoing: number, incoming: number, players: Player[]): Lineup {
    if (!lineup.starters.includes(outgoing) || !lineup.bench.includes(incoming)) return lineup;
    const starters = lineup.starters.map(id => id === outgoing ? incoming : id);
    if (!validStarters(starters, players)) return lineup;
    return reconcileLineup({...lineup, captainId: lineup.captainId === outgoing ? incoming : lineup.captainId, viceCaptainId: lineup.viceCaptainId === outgoing ? incoming : lineup.viceCaptainId, starters, bench: lineup.bench.map(id => id === incoming ? outgoing : id)}, players);
}

export function moveSubstitute(lineup: Lineup, id: number, direction: -1 | 1, players: Player[]): Lineup {
    const bench = [...lineup.bench];
    const index = bench.indexOf(id), target = index + direction;
    const isOutfield = (playerId: number) => players.some(player => player.id === playerId && player.position !== "Goalkeeper");
    if (index < 0 || target < 0 || target >= bench.length || !isOutfield(id) || !isOutfield(bench[target])) return lineup;
    [bench[index], bench[target]] = [bench[target], bench[index]];
    return {...lineup, bench};
}
