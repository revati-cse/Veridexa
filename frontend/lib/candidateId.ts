const STORAGE_KEY = "veridexa_candidate_id";

/**
 * No auth system for the hackathon (BLUEPRINT.md Section D/T) — a per-browser
 * candidate id is generated once and reused so evidence/challenge history
 * persists across page reloads within the same demo session.
 */
export function getCandidateId(): string {
  if (typeof window === "undefined") return "";

  const existing = window.localStorage.getItem(STORAGE_KEY);
  if (existing) return existing;

  const id = crypto.randomUUID();
  window.localStorage.setItem(STORAGE_KEY, id);
  return id;
}
