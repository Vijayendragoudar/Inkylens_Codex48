export type RuleType =
  | "forbidden_term"
  | "preferred_term"
  | "tone"
  | "approved_fact"
  | "claim_constraint";

export type DecisionState =
  | "open"
  | "resolved"
  | "dismissed"
  | "accepted_exception";

export interface GuidelineRule {
  id?: string;
  rule_key: string;
  rule_type: RuleType;
  title: string;
  content: string;
  replacement: string | null;
  created_at?: string;
}

export interface Brand {
  id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
  guidelines: GuidelineRule[];
}

export interface FindingDecision {
  state: DecisionState;
  note: string;
  updated_at: string;
}

export interface Finding {
  id: string;
  source: "deterministic" | "ai_assisted";
  severity: "low" | "medium" | "high";
  category: string;
  label: string;
  explanation: string;
  suggestion: string;
  excerpt: string;
  rule_keys: string[];
  created_at: string;
  decision: FindingDecision | null;
}

export interface Review {
  id: string;
  brand_id: string;
  submission_id: string;
  submission_text: string;
  revision_number: number;
  ai_status: "completed" | "unavailable" | "failed";
  ai_error: string | null;
  created_at: string;
  findings: Finding[];
}

export interface ReviewHistoryItem {
  id: string;
  revision_number: number;
  created_at: string;
  ai_status: string;
  finding_count: number;
  excerpt: string;
}

export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...init.headers,
    },
  });
  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const detail =
      payload && typeof payload === "object" && "detail" in payload
        ? String(payload.detail)
        : `Request failed with status ${response.status}.`;
    throw new ApiError(detail, response.status);
  }
  return payload as T;
}

export const api = {
  listBrands: () => request<Brand[]>("/api/brands"),
  getBrand: (brandId: string) => request<Brand>(`/api/brands/${brandId}`),
  createBrand: (name: string) =>
    request<Brand>("/api/brands", {
      method: "POST",
      body: JSON.stringify({ name, description: "", guidelines: [] }),
    }),
  updateBrand: (brand: Brand) =>
    request<Brand>(`/api/brands/${brand.id}`, {
      method: "PUT",
      body: JSON.stringify({
        name: brand.name,
        description: brand.description,
        guidelines: brand.guidelines.map(({ rule_key, rule_type, title, content, replacement }) => ({
          rule_key,
          rule_type,
          title,
          content,
          replacement: replacement || null,
        })),
      }),
    }),
  createReview: (brandId: string, text: string, priorReviewId?: string) =>
    request<Review>("/api/reviews", {
      method: "POST",
      body: JSON.stringify({
        brand_id: brandId,
        text,
        prior_review_id: priorReviewId || null,
      }),
    }),
  getReview: (reviewId: string) => request<Review>(`/api/reviews/${reviewId}`),
  listReviewHistory: (brandId: string) =>
    request<ReviewHistoryItem[]>(`/api/brands/${brandId}/reviews`),
  updateDecision: (findingId: string, state: DecisionState, note: string) =>
    request<FindingDecision>(`/api/findings/${findingId}/decision`, {
      method: "PATCH",
      body: JSON.stringify({ state, note }),
    }),
};
