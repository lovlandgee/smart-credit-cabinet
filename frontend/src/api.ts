const TOKEN_KEY = "cabinet_token";
export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}
async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(path, { ...init, headers });
  if (!response.ok) {
    let detail = "Ошибка запроса";
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}
export type User = {
  id: number;
  email: string;
  full_name: string;
  role: string;
  job_title: string;
  company_id: number | null;
};
export type Company = {
  id: number;
  inn: string;
  ogrn: string;
  legal_name: string;
  short_name: string;
  legal_form: string;
  okved: string;
  okved_name: string;
  region: string;
  employees: number;
  revenue_last_year: number;
  revenue_prev_year: number;
  profit_last_year: number;
  existing_debt: number;
  monthly_turnover: number;
  tax_regime: string;
};
export type Product = {
  id: string;
  name: string;
  short_name: string;
  purpose_hint: string;
  min_amount: number;
  max_amount: number;
  min_term_months: number;
  max_term_months: number;
  base_rate: number;
  collateral_required: boolean;
  description: string;
  suitable_for: string[];
};
export type EventItem = {
  id: number;
  actor: string;
  stage: string;
  title: string;
  detail: string;
  created_at: string;
};
export type Application = {
  id: number;
  public_id: string;
  product_id: string;
  status: string;
  amount: number;
  term_months: number;
  purpose: string;
  purpose_details: string;
  offered_amount: number | null;
  offered_term_months: number | null;
  offered_rate: number | null;
  decision_code: string | null;
  decision_reason: string | null;
  info_request: string | null;
  client_comment: string | null;
  score: number | null;
  risk_band: string | null;
  score_breakdown: {
    risk_band_name?: string;
    factors?: { title: string; value: string; points: number; note: string }[];
  } | null;
  enrichment: Record<string, unknown> | null;
  signed: boolean;
  created_at: string;
  updated_at: string;
  events: EventItem[];
  product?: Product;
  company?: Company;
};

export type NewsItem = {
  id: number;
  title: string;
  body: string;
  category: string;
  published_at: string;
  why: string | null;
};
export const api = {
  login: (email: string, password: string) =>
    request<{ access_token: string }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => request<{ user: User; company: Company | null }>("/api/auth/me"),
  products: () => request<Product[]>("/api/products"),
  recommend: (purpose: string, amount: number, urgency: string) =>
    request<Product[]>("/api/products/recommend", {
      method: "POST",
      body: JSON.stringify({ purpose, amount, urgency }),
    }),
  applications: () => request<Application[]>("/api/applications"),
  application: (id: number) => request<Application>(`/api/applications/${id}`),
  createApplication: (payload: {
    product_id: string;
    amount: number;
    term_months: number;
    purpose: string;
    purpose_details: string;
  }) =>
    request<Application>("/api/applications", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  replyInfo: (id: number, comment: string) =>
    request<Application>(`/api/applications/${id}/info`, {
      method: "POST",
      body: JSON.stringify({ comment }),
    }),
  accept: (id: number) => request<Application>(`/api/applications/${id}/accept`, { method: "POST" }),
  sign: (id: number) => request<Application>(`/api/applications/${id}/sign`, { method: "POST" }),
  cancel: (id: number) => request<Application>(`/api/applications/${id}/cancel`, { method: "POST" }),
  manual: (id: number, payload: Record<string, unknown>) =>
    request<Application>(`/api/applications/${id}/manual-decision`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  news: () => request<NewsItem[]>("/api/news"),
};
export function money(value: number | null | undefined): string {
  if (value == null) return "—";
  return new Intl.NumberFormat("ru-RU").format(value) + " ₽";
}
export const STATUS_LABEL: Record<string, string> = {
  draft: "Черновик",
  submitted: "Отправлена",
  intake: "Комплектность",
  enrichment: "Обогащение",
  scoring: "Скоринг",
  decision: "Решение",
  need_info: "Нужны сведения",
  offered: "Предложение",
  documents: "Документы",
  disbursement: "Выдача",
  completed: "Завершена",
  rejected: "Отказ",
  cancelled: "Отозвана",
};