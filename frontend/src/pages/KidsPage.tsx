import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api";
import type { Meal, Member, WeekPlan } from "../types";

const emptyWishFields = () => ["", "", ""];

export default function KidsPage() {
  const [meals, setMeals] = useState<Meal[]>([]);
  const [plan, setPlan] = useState<WeekPlan | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [memberId, setMemberId] = useState<number | null>(null);
  const [wishFields, setWishFields] = useState<string[]>(emptyWishFields);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const reload = useCallback(async () => {
    const [m, w, mem] = await Promise.all([
      api.listMeals(),
      api.currentWeek(0),
      api.listMembers(),
    ]);
    setMeals(m);
    setPlan(w);
    setMembers(mem.filter((x) => x.role === "kid"));
  }, []);

  useEffect(() => {
    reload().catch((err) => setError(String(err.message || err)));
  }, [reload]);

  const suggestedMealIds = useMemo(() => {
    if (!plan) return new Set<number>();
    return new Set(
      plan.suggestions
        .filter((s) => memberId == null || s.member_id === memberId)
        .map((s) => s.meal_id),
    );
  }, [plan, memberId]);

  async function toggleSuggestion(meal: Meal) {
    if (!plan) return;
    setError(null);
    setMessage(null);
    setBusy(true);
    try {
      const existing = plan.suggestions.find(
        (s) =>
          s.meal_id === meal.id &&
          (memberId == null ? s.member_id == null : s.member_id === memberId),
      );
      if (existing) {
        await api.removeSuggestion(existing.id, 0);
        setMessage(`„${meal.title}“ entfernt`);
      } else {
        await api.addSuggestion(meal.id, memberId, 0);
        setMessage(`„${meal.title}“ vorgeschlagen`);
      }
      await reload();
    } catch (err) {
      setError(String((err as Error).message || err));
    } finally {
      setBusy(false);
    }
  }

  async function saveWishes() {
    const texts = wishFields.map((t) => t.trim()).filter(Boolean);
    if (!texts.length) {
      setError("Mindestens einen Wunsch eintragen");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api.addWishes(texts, memberId, 0);
      setWishFields(emptyWishFields());
      setMessage("Wünsche gespeichert – Mama/Papa schauen sie an");
      await reload();
    } catch (err) {
      setError(String((err as Error).message || err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <h1 className="page-title">Was wollt ihr essen?</h1>
      <p className="lede">
        {"Tippt auf die Fotos für eure Essens-Ideen. Unten könnt ihr Extra-Wünsche wie Schokolade oder Eis eintragen."}
      </p>

      {members.length > 0 && (
        <div className="member-chips" aria-label="Wer tippt?">
          <button
            type="button"
            className={memberId == null ? "chip active" : "chip"}
            onClick={() => setMemberId(null)}
          >
            Alle
          </button>
          {members.map((m) => (
            <button
              key={m.id}
              type="button"
              className={memberId === m.id ? "chip active" : "chip"}
              onClick={() => setMemberId(m.id)}
            >
              {m.name}
            </button>
          ))}
        </div>
      )}

      <div className="meal-grid">
        {meals.map((meal) => {
          const selected = suggestedMealIds.has(meal.id);
          return (
            <button
              key={meal.id}
              type="button"
              className={selected ? "meal-tile selected" : "meal-tile"}
              onClick={() => toggleSuggestion(meal)}
              disabled={busy}
            >
              {meal.photo_path ? (
                <img src={meal.photo_path} alt={meal.title} loading="lazy" />
              ) : (
                <div className="photo-fallback">{meal.title.slice(0, 1)}</div>
              )}
              <span className="caption">{meal.title}</span>
              {selected && (
                <span className="select-corner" aria-label="Ausgewählt">
                  <span className="select-check">✓</span>
                </span>
              )}
            </button>
          );
        })}
      </div>

      {!meals.length && (
        <p className="empty">{"Noch keine Essen im Katalog – Eltern legen welche an."}</p>
      )}

      <section className="section">
        <h2>{"Extra-Wünsche"}</h2>
        <div className="panel">
          <div className="wish-fields">
            {wishFields.map((value, idx) => (
              <input
                key={idx}
                value={value}
                placeholder={
                  idx === 0
                    ? "z.B. Schokolade"
                    : idx === 1
                      ? "z.B. Eis"
                      : "Weiterer Wunsch…"
                }
                onChange={(e) => {
                  const next = [...wishFields];
                  next[idx] = e.target.value;
                  setWishFields(next);
                }}
              />
            ))}
          </div>
          <div className="row" style={{ marginTop: "0.85rem" }}>
            <button
              type="button"
              className="btn secondary"
              onClick={() => setWishFields((f) => [...f, ""])}
            >
              + weiteres Feld
            </button>
            <button type="button" className="btn sun" disabled={busy} onClick={saveWishes}>
              {"Wünsche speichern"}
            </button>
          </div>
        </div>
      </section>

      {message && <div className="toast">{message}</div>}
      {error && <div className="toast error">{error}</div>}
    </div>
  );
}
