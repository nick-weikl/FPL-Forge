let storageIssue = false;
export function storageUnavailable() {
  return storageIssue;
}
function reportIssue() {
  storageIssue = true;
  if (typeof window !== "undefined") window.dispatchEvent(new Event("fpl-storage-error"));
}
export function readStored(key: string, fallback: string): string {
  try {
    return localStorage.getItem(key) ?? fallback;
  } catch {
    reportIssue();
    return fallback;
  }
}
export function saveStored(key: string, value: string): boolean {
  try {
    localStorage.setItem(key, value);
    return true;
  } catch {
    reportIssue();
    return false;
  }
}

export function subscribeStorageIssue(listener: () => void) {
  window.addEventListener("fpl-storage-error", listener);
  return () => window.removeEventListener("fpl-storage-error", listener);
}

let recoveredData = false;
export function storageRecovery() {
  return recoveredData;
}
export function readJSONStored(key: string, fallback: string): string {
  const text = readStored(key, fallback);
  try {
    JSON.parse(text);
    return text;
  } catch {
    recoveredData = true;
    if (typeof window !== "undefined") window.dispatchEvent(new Event("fpl-storage-error"));
    return fallback;
  }
}
