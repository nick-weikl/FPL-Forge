import { useEffect, useState } from "react";
import { readStored, saveStored } from "../utils/storage";
export default function ThemeControl() {
  const [theme, setTheme] = useState(() => readStored("fpl-forge-theme", "system"));
  useEffect(() => {
    const preference = ["light", "dark"].includes(theme) ? theme : "system";
    const media = matchMedia("(prefers-color-scheme: dark)");
    const apply = () => {
      document.documentElement.dataset.theme =
        preference === "system" ? (media.matches ? "dark" : "light") : preference;
    };
    apply();
    saveStored("fpl-forge-theme", preference);
    media.addEventListener("change", apply);
    return () => media.removeEventListener("change", apply);
  }, [theme]);
  return (
    <label className="theme-control">
      <span className="sr-only">Color theme</span>
      <select
        aria-label="Color theme"
        value={theme}
        onChange={(event) => setTheme(event.target.value)}
      >
        <option value="system">System theme</option>
        <option value="light">Light mode</option>
        <option value="dark">Dark mode</option>
      </select>
    </label>
  );
}
