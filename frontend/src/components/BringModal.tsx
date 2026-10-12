import { useState } from "react";

type Props = {
  open: boolean;
  onClose: () => void;
  onSubmit: (password: string, includeMeals: boolean, includeWishes: boolean) => Promise<void>;
};

export default function BringModal({ open, onClose, onSubmit }: Props) {
  const [password, setPassword] = useState("");
  const [includeMeals, setIncludeMeals] = useState(true);
  const [includeWishes, setIncludeWishes] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await onSubmit(password, includeMeals, includeWishes);
      setPassword("");
      onClose();
    } catch (err) {
      setError(String((err as Error).message || err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>In Bring! legen</h2>
        <p className="muted">
          {"Passwort eingeben. Zutaten werden auf die Personenanzahl skaliert; freigegebene Wünsche kommen mit."}
        </p>
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="bring-pw">Passwort</label>
            <input
              id="bring-pw"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <label className="row">
            <input
              type="checkbox"
              checked={includeMeals}
              onChange={(e) => setIncludeMeals(e.target.checked)}
            />
            Rezept-Zutaten
          </label>
          <label className="row" style={{ marginTop: "0.4rem" }}>
            <input
              type="checkbox"
              checked={includeWishes}
              onChange={(e) => setIncludeWishes(e.target.checked)}
            />
            {"Freigegebene Wünsche"}
          </label>
          {error && <div className="toast error">{error}</div>}
          <div className="row" style={{ marginTop: "1rem" }}>
            <button type="button" className="btn secondary" onClick={onClose}>
              Abbrechen
            </button>
            <button type="submit" className="btn sun" disabled={busy}>
              {busy ? "Sende…" : "Pushen"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
