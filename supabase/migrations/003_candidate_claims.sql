-- Veridexa AI — candidate claims
-- Closes the gap noted in BLUEPRINT.md checklist item 11 / CLAUDE.md:
-- POST /candidates/claims previously only acknowledged receipt. A claim is
-- never evidence (Section M) — this table exists purely so
-- readiness_engine's claim-alignment bonus (capped at 10% weight, Section N)
-- has something real to read per candidate, instead of every caller having
-- to pass claims=[] because nothing was ever persisted.

create table candidate_claims (
  user_id uuid not null references users(id) on delete cascade,
  skill_id uuid not null references skills(id) on delete cascade,
  level text not null check (level in ('beginner', 'intermediate', 'advanced')),
  claimed_at timestamptz not null default now(),
  primary key (user_id, skill_id)
);
create index idx_candidate_claims_user on candidate_claims (user_id);
