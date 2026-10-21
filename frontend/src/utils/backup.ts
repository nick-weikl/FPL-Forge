import type { Lineup } from "./lineup";
export interface SquadBackup {
  version: 1;
  season: string;
  squadIds: number[];
  lineup: Lineup;
  bank: string;
  freeTransfers: string;
  gameweek: string;
  sellingPrices: Record<number, string>;
}
export function parseBackup(text: string, season: string, availableIds: number[]): SquadBackup {
  if (text.length > 65536)
    throw new Error("Backup is too large. Choose an FPL Forge backup smaller than 64 KB.");
  let value;
  try {
    value = JSON.parse(text);
  } catch {
    throw new Error("This file is not valid JSON. Choose an FPL Forge backup.");
  }
  if (!value || value.version !== 1 || value.season !== season)
    throw new Error("Choose a version 1 FPL Forge backup from the current season.");
  const ids = value.squadIds;
  if (
    !Array.isArray(ids) ||
    ids.length > 15 ||
    ids.some((id) => !Number.isInteger(id) || !availableIds.includes(id)) ||
    new Set(ids).size !== ids.length
  )
    throw new Error(
      "The backup contains duplicate or unavailable players. Import your current FPL team instead.",
    );
  const lineup = value.lineup;
  if (
    !lineup ||
    ![lineup.starters, lineup.bench].every(
      (group) => Array.isArray(group) && group.every((id) => ids.includes(id)),
    ) ||
    new Set([...lineup.starters, ...lineup.bench]).size !==
      lineup.starters.length + lineup.bench.length
  )
    throw new Error("The backup has an invalid lineup.");
  const bank = Number(value.bank),
    free = Number(value.freeTransfers),
    week = Number(value.gameweek);
  if (
    typeof value.bank !== "string" ||
    !value.bank.trim() ||
    !Number.isFinite(bank) ||
    bank < 0 ||
    Math.abs(bank * 10 - Math.round(bank * 10)) > 0.00001 ||
    typeof value.freeTransfers !== "string" ||
    !value.freeTransfers.trim() ||
    !Number.isInteger(free) ||
    free < 0 ||
    free > 5 ||
    typeof value.gameweek !== "string" ||
    (value.gameweek !== "" && (!Number.isInteger(week) || week < 1 || week > 38))
  )
    throw new Error("The backup has invalid bank or transfer settings.");
  const selling = value.sellingPrices;
  if (
    !selling ||
    typeof selling !== "object" ||
    Array.isArray(selling) ||
    Object.entries(selling).some(
      ([id, price]) =>
        !ids.includes(Number(id)) ||
        typeof price !== "string" ||
        (price.trim() &&
          (!Number.isFinite(Number(price)) ||
            Number(price) < 0 ||
            Math.abs(Number(price) * 10 - Math.round(Number(price) * 10)) > 0.00001)),
    )
  )
    throw new Error("The backup has invalid selling values.");
  return {
    version: 1,
    season,
    squadIds: ids,
    lineup: {
      starters: lineup.starters,
      bench: lineup.bench,
      captainId: lineup.captainId,
      viceCaptainId: lineup.viceCaptainId,
    },
    bank: value.bank,
    freeTransfers: value.freeTransfers,
    gameweek: value.gameweek,
    sellingPrices: selling,
  };
}
