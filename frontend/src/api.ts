import type { Meal, Member, Suggestion, WeekPlan, Wish, Ingredient } from "./types";

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

function weekUrl(path: string, offset = 0): string {
  const sep = path.includes("?") ? "&" : "?";
  return `${path}${sep}offset=${offset}`;
}

export type DayPayload = {
  weekday: number;
  meal_id: number | null;
  servings?: number;
};

export const api = {
  health: () => request<{ ok: boolean }>("/api/health"),

  listMeals: (activeOnly = true) =>
    request<Meal[]>(`/api/meals?active_only=${activeOnly}`),

  createMeal: (body: {
    title: string;
    base_servings: number;
    instructions?: string;
    notes?: string;
    ingredients: Ingredient[];
  }) =>
    request<Meal>("/api/meals", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),

  updateMeal: (
    id: number,
    body: Partial<{
      title: string;
      base_servings: number;
      instructions: string;
      notes: string;
      ingredients: Ingredient[];
      active: boolean;
    }>,
  ) =>
    request<Meal>(`/api/meals/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),

  deleteMeal: (id: number) =>
    request<{ ok: boolean }>(`/api/meals/${id}`, { method: "DELETE" }),

  importChefkoch: (url: string) =>
    request<Meal>("/api/meals/from-chefkoch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    }),

  uploadPhoto: async (id: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<Meal>(`/api/meals/${id}/photo`, { method: "POST", body: form });
  },

  listMembers: () => request<Member[]>("/api/members"),

  createMember: (name: string, role = "kid") =>
    request<Member>("/api/members", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, role }),
    }),

  deleteMember: (id: number) =>
    request<{ ok: boolean }>(`/api/members/${id}`, { method: "DELETE" }),

  currentWeek: (offset = 0) =>
    request<WeekPlan>(weekUrl("/api/weeks/current", offset)),

  addSuggestion: (meal_id: number, member_id?: number | null, offset = 0) =>
    request<Suggestion>(weekUrl("/api/weeks/current/suggestions", offset), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ meal_id, member_id: member_id ?? null }),
    }),

  removeSuggestion: (id: number, offset = 0) =>
    request<{ ok: boolean }>(
      weekUrl(`/api/weeks/current/suggestions/${id}`, offset),
      { method: "DELETE" },
    ),

  addWishes: (texts: string[], member_id?: number | null, offset = 0) =>
    request<Wish[]>(weekUrl("/api/weeks/current/wishes", offset), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texts, member_id: member_id ?? null }),
    }),

  updateWish: (id: number, status: string, offset = 0) =>
    request<Wish>(weekUrl(`/api/weeks/current/wishes/${id}`, offset), {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    }),

  updateDays: (days: DayPayload[], offset = 0) =>
    request<WeekPlan>(weekUrl("/api/weeks/current/days", offset), {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ days }),
    }),

  finalize: (offset = 0) =>
    request<WeekPlan>(weekUrl("/api/weeks/current/finalize", offset), {
      method: "POST",
    }),

  reopen: (offset = 0) =>
    request<WeekPlan>(weekUrl("/api/weeks/current/reopen", offset), {
      method: "POST",
    }),

  resetDays: (offset = 0) =>
    request<WeekPlan>(weekUrl("/api/weeks/current/reset-days", offset), {
      method: "POST",
    }),

  pushBring: (
    body: {
      password: string;
      include_meals?: boolean;
      include_wishes?: boolean;
      wish_ids?: number[];
    },
    offset = 0,
  ) =>
    request<{ ok: boolean; items_added: number; message: string }>(
      weekUrl("/api/weeks/current/push-bring", offset),
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
    ),

  bringLists: (password: string) =>
    request<{ list_uuid: string; name: string }[]>("/api/bring/lists", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    }),
};
