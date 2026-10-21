import type { Player } from "../types/player";

export function reconcilePlayers(saved: Player[], catalog?: Player[]): Player[] {
    const current = catalog ? new Map(catalog.map(player => [player.id, player])) : undefined;
    const seen = new Set<number>();
    return saved.flatMap(player => {
        if (seen.has(player.id)) return [];
        seen.add(player.id);
        const latest = current ? current.get(player.id) : player;
        return latest ? [latest] : [];
    });
}
