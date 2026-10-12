export type Ingredient = {
  id?: number;
  name: string;
  amount: number | null;
  unit: string | null;
  sort_order: number;
};

export type Meal = {
  id: number;
  title: string;
  photo_path: string | null;
  source: string;
  chefkoch_url: string | null;
  chefkoch_id: string | null;
  base_servings: number;
  instructions: string | null;
  notes: string | null;
  active: boolean;
  ingredients: Ingredient[];
};

export type Member = {
  id: number;
  name: string;
  role: string;
};

export type Suggestion = {
  id: number;
  meal_id: number;
  member_id: number | null;
  meal_title: string | null;
  member_name: string | null;
  created_at: string;
};

export type Wish = {
  id: number;
  text: string;
  status: "pending" | "approved" | "rejected" | "pushed";
  member_id: number | null;
  member_name: string | null;
  created_at: string;
};

export type Day = {
  weekday: number;
  meal_id: number | null;
  servings: number;
  meal: Meal | null;
};

export type WeekPlan = {
  id: number;
  week_start: string;
  week_offset: number;
  status: string;
  target_servings: number;
  days: Day[];
  suggestions: Suggestion[];
  wishes: Wish[];
};
