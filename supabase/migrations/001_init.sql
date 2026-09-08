-- Veridexa AI — initial schema
-- Matches BLUEPRINT.md Section F. Minimal, relational, no graph DB.
-- Run against a Supabase (Postgres) project.

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- users
-- No real auth for the hackathon: a candidate_id (uuid) is generated
-- client-side on first load and used as the foreign key everywhere below.
-- ---------------------------------------------------------------------------
create table users (
  id uuid primary key default gen_random_uuid(),
  display_name text,
  created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- jobs / skills / job_skills
-- ---------------------------------------------------------------------------
create table jobs (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  raw_description text not null,
  created_at timestamptz not null default now()
);

create table skills (
  id uuid primary key default gen_random_uuid(),
  name text unique not null,
  category text not null check (category in (
    'programming', 'database', 'data', 'ai_ml', 'cloud',
    'business', 'communication', 'problem_solving', 'tools'
  ))
);
create index idx_skills_category on skills (category);

create table job_skills (
  job_id uuid not null references jobs(id) on delete cascade,
  skill_id uuid not null references skills(id) on delete cascade,
  importance text not null check (importance in ('high', 'medium', 'low')),
  required boolean not null default true,
  primary key (job_id, skill_id)
);

-- ---------------------------------------------------------------------------
-- repositories / repository_files / repository_evidence
-- ---------------------------------------------------------------------------
create table repositories (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  url text not null,
  default_branch text,
  languages_summary jsonb,
  analyzed_at timestamptz
);
create index idx_repositories_user on repositories (user_id);

create table repository_files (
  id uuid primary key default gen_random_uuid(),
  repository_id uuid not null references repositories(id) on delete cascade,
  path text not null,
  extension text,
  size_bytes int,
  selected_for_analysis boolean not null default false
);
create index idx_repository_files_repo on repository_files (repository_id);

create table repository_evidence (
  id uuid primary key default gen_random_uuid(),
  repository_id uuid not null references repositories(id) on delete cascade,
  skill_id uuid not null references skills(id),
  evidence_strength text not null check (evidence_strength in ('weak', 'moderate', 'strong')),
  confidence numeric(4, 3) not null check (confidence >= 0 and confidence <= 1),
  observations jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);
create index idx_repository_evidence_repo on repository_evidence (repository_id);
create index idx_repository_evidence_skill on repository_evidence (skill_id);

-- ---------------------------------------------------------------------------
-- challenges (self-referencing for mutation lineage)
-- ---------------------------------------------------------------------------
create table challenges (
  id uuid primary key default gen_random_uuid(),
  job_id uuid references jobs(id),
  user_id uuid not null references users(id) on delete cascade,
  parent_challenge_id uuid references challenges(id),
  title text not null,
  role text,
  scenario text not null,
  instructions text not null,
  required_skills text[] not null default '{}',
  difficulty int not null check (difficulty in (1, 2, 3)),
  dataset jsonb,
  expected_output text,
  evaluation_criteria jsonb not null default '{}'::jsonb,
  mutation_reason text,
  created_at timestamptz not null default now()
);
create index idx_challenges_user on challenges (user_id);
create index idx_challenges_job on challenges (job_id);
create index idx_challenges_parent on challenges (parent_challenge_id);

-- ---------------------------------------------------------------------------
-- submissions / evaluations
-- ---------------------------------------------------------------------------
create table submissions (
  id uuid primary key default gen_random_uuid(),
  challenge_id uuid not null references challenges(id) on delete cascade,
  user_id uuid not null references users(id) on delete cascade,
  code text,
  explanation text,
  submitted_at timestamptz not null default now()
);
create index idx_submissions_challenge on submissions (challenge_id);
create index idx_submissions_user on submissions (user_id);

create table evaluations (
  id uuid primary key default gen_random_uuid(),
  submission_id uuid not null references submissions(id) on delete cascade,
  rubric_scores jsonb not null,
  overall_score numeric(5, 2) not null,
  strengths jsonb not null default '[]'::jsonb,
  weaknesses jsonb not null default '[]'::jsonb,
  skill_gaps jsonb not null default '[]'::jsonb,
  sql_execution_result jsonb,
  created_at timestamptz not null default now()
);
create index idx_evaluations_submission on evaluations (submission_id);

-- ---------------------------------------------------------------------------
-- evidence — the traceability backbone for every skill % shown in the UI
-- ---------------------------------------------------------------------------
create table evidence (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  skill_id uuid not null references skills(id),
  source_type text not null check (source_type in (
    'resume', 'project', 'github', 'challenge', 'submission'
  )),
  source_reference text,
  challenge_id uuid references challenges(id),
  repository_id uuid references repositories(id),
  observation text,
  confidence numeric(4, 3) not null check (confidence >= 0 and confidence <= 1),
  created_at timestamptz not null default now()
);
create index idx_evidence_user_skill on evidence (user_id, skill_id);
create index idx_evidence_source_type on evidence (source_type);
