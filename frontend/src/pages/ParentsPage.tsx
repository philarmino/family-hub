import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api";
import BringModal from "../components/BringModal";
import MealEditor from "../components/MealEditor";
import type { Meal, Member, WeekPlan } from "../types";

const WEEKDAYS = [
  "Montag",
  "Dienstag",
  "Mittwoch",
  "Donnerstag",
  "Freitag",
  "Samstag",
  "Sonntag",
];

const WEEK_LABELS = ["Diese Woche", "Nächste Woche", "Übernächste Woche"];

type WeekTab = "plan" | "wishes";
type View = WeekTab | "catalog" | "family";

function formatWeekRange(weekStart: string): string {
  const start = new Date(`${weekStart}T12:00:00`);
  const end = new Date(start);
  end.setDate(start.getDate() + 6);
  const fmt = (d: Date) =>
    d.toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit" });
  return `${fmt(start)} – ${fmt(end)}`;
}

export default function ParentsPage() {
  const [view, setView] = useState<View>("plan");
  const [weekOffset, setWeekOffset] = useState(0);
  const isWeekView = view === "plan" || view === "wishes";
  const [meals, setMeals] = useState<Meal[]>([]);
  const [plan, setPlan] = useState<WeekPlan | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [bringOpen, setBringOpen] = useState(false);
  const [editing, setEditing] = useState<Meal | null | "new">(null);
  const [chefkochUrl, setChefkochUrl] = useState("");
  const [newMember, setNewMember] = useState("");

  const reload = useCallback(async () => {
    const [m, w, mem] = await Promise.all([
      api.listMeals(false),
      api.currentWeek(weekOffset),
      api.listMembers(),
    ]);
    setMeals(m.filter((x) => x.active));
    setPlan(w);
    setMembers(mem);
  }, [weekOffset]);

  useEffect(() => {
    reload().catch((err) => setError(String(err.message || err)));
  }, [reload]);

  const groupedSuggestions = useMemo(() => {
    if (!plan) return [];
    const byMeal = new Map<
      number,
      { meal_id: number; meal_title: string; names: string[] }
    >();
    for (const s of plan.suggestions) {
      const existing = byMeal.get(s.meal_id);
      const name = s.member_name?.trim() || "ohne Name";
      if (existing) {
        if (!existing.names.includes(name)) existing.names.push(name);
      } else {
        byMeal.set(s.meal_id, {
          meal_id: s.meal_id,
          meal_title: s.meal_title || "Gericht",
          names: [name],
        });
      }
    }
    return Array.from(byMeal.values());
  }, [plan]);

  const plannedMealIds = useMemo(() => {
    if (!plan) return new Set<number>();
    return new Set(
      plan.days.map((d) => d.meal_id).filter((id): id is number => id != null),
    );
  }, [plan]);



  function dayPayload(
    weekday: number,
    patch: { meal_id?: number | null; servings?: number },
  ) {
    if (!plan) return [];
    return plan.days.map((d) => ({
      weekday: d.weekday,
      meal_id: d.weekday === weekday && "meal_id" in patch ? patch.meal_id! : d.meal_id,
      servings: d.weekday === weekday && patch.servings != null ? patch.servings : d.servings,
    }));
  }

  async function assignDay(weekday: number, mealId: number | null) {
    if (!plan || plan.status === "finalized") return;
    setBusy(true);
    setError(null);
    try {
      setPlan(await api.updateDays(dayPayload(weekday, { meal_id: mealId }), weekOffset));
    } catch (err) {
      setError(String((err as Error).message || err));
    } finally {
      setBusy(false);
    }
  }

  async function setDayServings(weekday: number, servings: number) {
    if (!plan || plan.status === "finalized") return;
    setBusy(true);
    try {
      setPlan(
        await api.updateDays(
          dayPayload(weekday, { servings: Math.max(1, servings) }),
          weekOffset,
        ),
      );
    } catch (err) {
      setError(String((err as Error).message || err));
    } finally {
      setBusy(false);
    }
  }

  async function finalize() {
    setBusy(true);
    try {
      setPlan(await api.finalize(weekOffset));
      setMessage("Wochenplan finalisiert");
    } catch (err) {
      setError(String((err as Error).message || err));
    } finally {
      setBusy(false);
    }
  }

  async function reopen() {
    setPlan(await api.reopen(weekOffset));
    setMessage("Plan wieder geöffnet");
  }

  async function resetDays() {
    if (!plan) return;
    if (!confirm("Alle Tage dieser Woche zurücksetzen? Essen und Personen werden geleert.")) return;
    setBusy(true);
    setError(null);
    try {
      setPlan(await api.resetDays(weekOffset));
      setMessage("Tage zurückgesetzt");
    } catch (err) {
      setError(String((err as Error).message || err));
    } finally {
      setBusy(false);
    }
  }

  async function setWishStatus(id: number, status: string) {
    await api.updateWish(id, status, weekOffset);
    await reload();
  }

  async function importChefkoch() {
    if (!chefkochUrl.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await api.importChefkoch(chefkochUrl.trim());
      setChefkochUrl("");
      setMessage("Chefkoch-Rezept importiert");
      await reload();
    } catch (err) {
      setError(String((err as Error).message || err));
    } finally {
      setBusy(false);
    }
  }

  async function addMember() {
    if (!newMember.trim()) return;
    await api.createMember(newMember.trim(), "kid");
    setNewMember("");
    await reload();
  }

  async function removeMember(id: number, name: string) {
    if (!confirm(`„${name}“ wirklich entfernen?`)) return;
    await api.deleteMember(id);
    await reload();
  }

  return (
    <div>
      <h1 className="page-title">Eltern</h1>
      <p className="lede">
        {view === "catalog"
          ? "Rezepte anlegen, Fotos pflegen und Chefkoch importieren."
          : view === "family"
            ? "Kinder für die Vorschläge und Wunschfelder verwalten."
            : "Vorschläge prüfen, Wochen planen und Einkauf nach Bring! schicken."}
      </p>

      {isWeekView && (
        <>
          <div className="week-switcher" aria-label="Woche wählen">
            {WEEK_LABELS.map((label, idx) => (
              <button
                key={label}
                type="button"
                className={weekOffset === idx ? "chip active" : "chip"}
                onClick={() => setWeekOffset(idx)}
              >
                {label}
              </button>
            ))}
          </div>
          {plan && (
            <p className="muted week-range">{formatWeekRange(plan.week_start)}</p>
          )}

          <div className="tabs">
            {(
              [
                ["plan", "Wochenplan"],
                ["wishes", "Wünsche"],
              ] as const
            ).map(([id, label]) => (
              <button
                key={id}
                type="button"
                className={view === id ? "tab active" : "tab"}
                onClick={() => setView(id)}
              >
                {label}
              </button>
            ))}
          </div>
        </>
      )}

      {!isWeekView && (
        <div className="setup-bar">
          <button type="button" className="text-link" onClick={() => setView("plan")}>
            ← Zur Woche
          </button>
          <div className="setup-tabs" role="tablist" aria-label="Verwaltung">
            <button
              type="button"
              className={view === "catalog" ? "tab active" : "tab"}
              onClick={() => setView("catalog")}
            >
              Katalog
            </button>
            <button
              type="button"
              className={view === "family" ? "tab active" : "tab"}
              onClick={() => setView("family")}
            >
              Familie
            </button>
          </div>
        </div>
      )}

      {view === "plan" && plan && (
        <section>
          <div className="row" style={{ marginBottom: "1rem" }}>
            <span className="muted">Status: {plan.status}</span>
            {plan.status !== "finalized" ? (
              <button type="button" className="btn" disabled={busy} onClick={finalize}>
                Finalisieren
              </button>
            ) : (
              <button type="button" className="btn secondary" onClick={reopen}>
                {"Wieder öffnen"}
              </button>
            )}
            <button type="button" className="btn sun" onClick={() => setBringOpen(true)}>
              In Bring! legen
            </button>
            <button type="button" className="btn secondary" disabled={busy} onClick={resetDays}>
              Tage zurücksetzen
            </button>
          </div>

          <div className="week-list">
            {plan.days.map((day) => (
              <div
                key={day.weekday}
                className={day.meal_id ? "day-row filled" : "day-row"}
              >
                <div className="day-row-main">
                  <h3>{WEEKDAYS[day.weekday]}</h3>
                  <p className="meal-name">{day.meal?.title || "— offen —"}</p>
                </div>
                <div className="day-row-controls">
                  <label className="servings-field">
                    <span>Personen</span>
                    <input
                      type="number"
                      min={1}
                      max={50}
                      value={day.servings}
                      disabled={plan.status === "finalized" || busy}
                      onChange={(e) =>
                        setDayServings(day.weekday, Number(e.target.value) || 1)
                      }
                    />
                  </label>
                  {plan.status !== "finalized" && (
                    <select
                      value={day.meal_id ?? ""}
                      disabled={busy}
                      onChange={(e) =>
                        assignDay(
                          day.weekday,
                          e.target.value ? Number(e.target.value) : null,
                        )
                      }
                    >
                      <option value="">Kein Essen</option>
                      {meals.map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.title}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              </div>
            ))}
          </div>

          <section className="section">
            <h2>{"Vorschläge der Kinder"}</h2>
            <ul className="list">
              {groupedSuggestions.map((s) => (
                <li key={s.meal_id} className="list-item">
                  <div>
                    <strong>{s.meal_title}</strong>
                    <div className="muted">{s.names.join(", ")}</div>
                  </div>
                  {plan.status !== "finalized" && (
                    <button
                      type="button"
                      className={
                        plannedMealIds.has(s.meal_id)
                          ? "btn in-plan"
                          : "btn secondary"
                      }
                      disabled={busy || plannedMealIds.has(s.meal_id)}
                      onClick={() => {
                        if (plannedMealIds.has(s.meal_id)) return;
                        const empty = plan.days.find((d) => !d.meal_id);
                        if (empty) assignDay(empty.weekday, s.meal_id);
                      }}
                    >
                      {plannedMealIds.has(s.meal_id) ? "Im Plan" : "In Plan"}
                    </button>
                  )}
                </li>
              ))}
              {!groupedSuggestions.length && (
                <li className="empty">Noch keine Vorschläge</li>
              )}
            </ul>
          </section>
        </section>
      )}

      {view === "wishes" && plan && (
        <section>
          <ul className="list">
            {plan.wishes.map((w) => (
              <li key={w.id} className="list-item">
                <div>
                  <strong>{w.text}</strong>
                  <div className="muted">{w.member_name || "Kind"}</div>
                  <div className={`status ${w.status}`}>{w.status}</div>
                </div>
                <div className="row">
                  {w.status !== "approved" && w.status !== "pushed" && (
                    <button
                      type="button"
                      className="btn"
                      onClick={() => setWishStatus(w.id, "approved")}
                    >
                      Freigeben
                    </button>
                  )}
                  {w.status !== "rejected" && w.status !== "pushed" && (
                    <button
                      type="button"
                      className="btn secondary"
                      onClick={() => setWishStatus(w.id, "rejected")}
                    >
                      Verwerfen
                    </button>
                  )}
                </div>
              </li>
            ))}
            {!plan.wishes.length && <li className="empty">{"Keine Wünsche diese Woche"}</li>}
          </ul>
          <div className="row" style={{ marginTop: "1rem" }}>
            <button type="button" className="btn sun" onClick={() => setBringOpen(true)}>
              Freigegebene nach Bring!
            </button>
          </div>
        </section>
      )}

      {view === "catalog" && (
        <section>
          <div className="panel" style={{ marginBottom: "1rem" }}>
            <h2 style={{ marginTop: 0 }}>Aus Chefkoch importieren</h2>
            <div className="row">
              <input
                style={{ flex: 1, minWidth: "12rem" }}
                placeholder={"https://www.chefkoch.de/rezepte/…"}
                value={chefkochUrl}
                onChange={(e) => setChefkochUrl(e.target.value)}
              />
              <button type="button" className="btn" disabled={busy} onClick={importChefkoch}>
                Import
              </button>
            </div>
          </div>

          <div className="row" style={{ marginBottom: "1rem" }}>
            <button type="button" className="btn sun" onClick={() => setEditing("new")}>
              + Eigenes Rezept
            </button>
          </div>

          <div className="meal-grid">
            {meals.map((meal) => (
              <button
                key={meal.id}
                type="button"
                className="meal-tile"
                onClick={() => setEditing(meal)}
              >
                {meal.photo_path ? (
                  <img src={meal.photo_path} alt={meal.title} />
                ) : (
                  <div className="photo-fallback">{meal.title.slice(0, 1)}</div>
                )}
                <span className="caption">
                  {meal.title}
                  {meal.source === "chefkoch" ? " · Chefkoch" : ""}
                </span>
              </button>
            ))}
          </div>

          {editing && (
            <MealEditor
              meal={editing === "new" ? null : editing}
              onClose={() => setEditing(null)}
              onSaved={async () => {
                setEditing(null);
                await reload();
                setMessage("Rezept gespeichert");
              }}
            />
          )}
        </section>
      )}

      {view === "family" && (
        <section className="panel">
          <h2 style={{ marginTop: 0 }}>Kinder</h2>
          <ul className="list">
            {members
              .filter((m) => m.role === "kid")
              .map((m) => (
                <li key={m.id} className="list-item">
                  <strong>{m.name}</strong>
                  <button
                    type="button"
                    className="btn danger"
                    onClick={() => removeMember(m.id, m.name)}
                  >
                    Entfernen
                  </button>
                </li>
              ))}
            {!members.filter((m) => m.role === "kid").length && (
              <li className="empty">Noch keine Kinder angelegt</li>
            )}
          </ul>
          <div className="row" style={{ marginTop: "1rem" }}>
            <input
              placeholder="Name"
              value={newMember}
              onChange={(e) => setNewMember(e.target.value)}
            />
            <button type="button" className="btn" onClick={addMember}>
              {"Hinzufügen"}
            </button>
          </div>
        </section>
      )}

      {isWeekView && (
        <nav className="manage-links" aria-label="Verwaltung">
          <button type="button" className="text-link" onClick={() => setView("catalog")}>
            Katalog
          </button>
          <span className="manage-sep" aria-hidden="true">
            ·
          </span>
          <button type="button" className="text-link" onClick={() => setView("family")}>
            Familie
          </button>
        </nav>
      )}

      {message && <div className="toast">{message}</div>}
      {error && <div className="toast error">{error}</div>}

      <BringModal
        open={bringOpen}
        onClose={() => setBringOpen(false)}
        onSubmit={async (password, includeMeals, includeWishes) => {
          const result = await api.pushBring(
            {
              password,
              include_meals: includeMeals,
              include_wishes: includeWishes,
            },
            weekOffset,
          );
          setMessage(result.message);
          await reload();
        }}
      />
    </div>
  );
}
