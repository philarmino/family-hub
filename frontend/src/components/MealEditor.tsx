import { useState } from "react";
import { api } from "../api";
import type { Ingredient, Meal } from "../types";

type Props = {
  meal: Meal | null;
  onClose: () => void;
  onSaved: () => Promise<void>;
};

function blankIngredient(): Ingredient {
  return { name: "", amount: null, unit: "", sort_order: 0 };
}

export default function MealEditor({ meal, onClose, onSaved }: Props) {
  const [title, setTitle] = useState(meal?.title ?? "");
  const [baseServings, setBaseServings] = useState(meal?.base_servings ?? 4);
  const [instructions, setInstructions] = useState(meal?.instructions ?? "");
  const [ingredients, setIngredients] = useState<Ingredient[]>(
    meal?.ingredients?.length
      ? meal.ingredients.map((i) => ({ ...i, unit: i.unit ?? "" }))
      : [blankIngredient()],
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    const cleaned = ingredients
      .map((ing, idx) => ({
        name: ing.name.trim(),
        amount: ing.amount,
        unit: ing.unit?.trim() || null,
        sort_order: idx,
      }))
      .filter((ing) => ing.name);

    try {
      if (meal) {
        await api.updateMeal(meal.id, {
          title: title.trim(),
          base_servings: baseServings,
          instructions,
          ingredients: cleaned,
        });
      } else {
        await api.createMeal({
          title: title.trim(),
          base_servings: baseServings,
          instructions,
          ingredients: cleaned,
        });
      }
      await onSaved();
    } catch (err) {
      setError(String((err as Error).message || err));
    } finally {
      setBusy(false);
    }
  }

  async function onPhoto(file: File | null) {
    if (!file || !meal) return;
    setBusy(true);
    try {
      await api.uploadPhoto(meal.id, file);
      await onSaved();
    } catch (err) {
      setError(String((err as Error).message || err));
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    if (!meal) return;
    if (!confirm(`„${meal.title}“ wirklich entfernen?`)) return;
    await api.deleteMeal(meal.id);
    await onSaved();
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal"
        style={{ width: "min(640px, 100%)", maxHeight: "90svh", overflow: "auto" }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2>{meal ? "Rezept bearbeiten" : "Eigenes Rezept"}</h2>
        <form onSubmit={save}>
          <div className="field">
            <label>Titel</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} required />
          </div>
          <div className="field">
            <label>Portionen (Basis)</label>
            <input
              type="number"
              min={1}
              max={50}
              value={baseServings}
              onChange={(e) => setBaseServings(Number(e.target.value) || 1)}
            />
          </div>
          <div className="field">
            <label>Zubereitung (optional)</label>
            <textarea
              rows={3}
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
            />
          </div>

          <h3>Zutaten</h3>
          {ingredients.map((ing, idx) => (
            <div className="ingredient-row" key={idx}>
              <input
                placeholder="Name"
                value={ing.name}
                onChange={(e) => {
                  const next = [...ingredients];
                  next[idx] = { ...ing, name: e.target.value };
                  setIngredients(next);
                }}
              />
              <input
                placeholder="Menge"
                type="number"
                step="any"
                value={ing.amount ?? ""}
                onChange={(e) => {
                  const next = [...ingredients];
                  next[idx] = {
                    ...ing,
                    amount: e.target.value === "" ? null : Number(e.target.value),
                  };
                  setIngredients(next);
                }}
              />
              <input
                placeholder="Einheit"
                value={ing.unit ?? ""}
                onChange={(e) => {
                  const next = [...ingredients];
                  next[idx] = { ...ing, unit: e.target.value };
                  setIngredients(next);
                }}
              />
              <button
                type="button"
                className="btn ghost"
                onClick={() => setIngredients(ingredients.filter((_, i) => i !== idx))}
              >
                {"✕"}
              </button>
            </div>
          ))}
          <button
            type="button"
            className="btn secondary"
            onClick={() => setIngredients([...ingredients, blankIngredient()])}
          >
            + Zutat
          </button>

          {meal && (
            <div className="field" style={{ marginTop: "1rem" }}>
              <label>Foto</label>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => onPhoto(e.target.files?.[0] ?? null)}
              />
            </div>
          )}

          {error && <div className="toast error">{error}</div>}

          <div className="row" style={{ marginTop: "1rem" }}>
            <button type="button" className="btn secondary" onClick={onClose}>
              Abbrechen
            </button>
            {meal && (
              <button type="button" className="btn danger" onClick={remove}>
                Entfernen
              </button>
            )}
            <button type="submit" className="btn" disabled={busy}>
              Speichern
            </button>
          </div>
          {!meal && (
            <p className="muted" style={{ marginTop: "0.75rem" }}>
              {"Foto kannst du nach dem Speichern hochladen."}
            </p>
          )}
        </form>
      </div>
    </div>
  );
}
