-- Sentinel Anti-Cheat logical schema for Supabase/Postgres

create extension if not exists pgcrypto;

create table if not exists federations (
  id text primary key,
  name text not null,
  code text unique,
  country_code text,
  policy_settings jsonb not null default '{}'::jsonb,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists app_users (
  id uuid primary key default gen_random_uuid(),
  email text unique,
  display_name text,
  auth_provider text,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists federation_memberships (
  federation_id text not null references federations(id) on delete cascade,
  user_id uuid not null references app_users(id) on delete cascade,
  role text not null check (role in ('arbiter', 'chief_arbiter', 'federation_admin', 'system_admin', 'analyst', 'reviewer')),
  status text not null default 'active' check (status in ('active', 'invited', 'suspended')),
  can_lock_reports boolean not null default false,
  can_sign_cases boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (federation_id, user_id, role)
);

create table if not exists players (
  id text primary key,
  fide_id text,
  display_name text,
  federation_id text references federations(id),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

alter table players add column if not exists display_name text;
alter table players add column if not exists federation_id text;
alter table players add column if not exists metadata jsonb default '{}'::jsonb;

create table if not exists events (
  id text primary key,
  federation_id text references federations(id),
  name text,
  event_type text not null default 'online' check (event_type in ('online', 'otb')),
  status text not null default 'scheduled' check (status in ('scheduled', 'live', 'completed', 'archived')),
  site text,
  round_count int,
  metadata jsonb not null default '{}'::jsonb,
  starts_on date,
  ends_on date,
  created_at timestamptz not null default now()
);

alter table events add column if not exists event_type text;
alter table events add column if not exists federation_id text;
alter table events add column if not exists status text;
alter table events add column if not exists site text;
alter table events add column if not exists round_count int;
alter table events add column if not exists metadata jsonb default '{}'::jsonb;

create table if not exists analyses (
  id uuid primary key default gen_random_uuid(),
  player_id text not null references players(id),
  event_id text not null references events(id),
  federation_id text references federations(id),
  external_audit_id text unique,
  risk_tier text not null,
  confidence numeric not null,
  analyzed_move_count int not null,
  triggered_signals int not null,
  weighted_risk_score numeric,
  event_type text not null default 'online',
  regan_threshold_used numeric,
  natural_occurrence_statement text,
  natural_occurrence_probability numeric,
  model_version text not null,
  feature_schema_version text,
  report_schema_version text,
  report_version int not null default 1,
  report_locked boolean not null default false,
  report_locked_at timestamptz,
  legal_disclaimer_text text,
  human_review_required boolean not null default false,
  review_status text not null default 'pending' check (review_status in ('pending', 'under_review', 'escalated', 'closed')),
  explainability_method text,
  explainability_items jsonb,
  ml_fusion_source text,
  ml_primary_score numeric,
  ml_secondary_score numeric,
  input_hash text not null,
  explanation jsonb not null,
  signals jsonb not null,
  raw_request jsonb,
  raw_response jsonb,
  created_at timestamptz not null default now()
);

alter table analyses add column if not exists external_audit_id text;
alter table analyses add column if not exists weighted_risk_score numeric;
alter table analyses add column if not exists event_type text;
alter table analyses add column if not exists federation_id text;
alter table analyses add column if not exists regan_threshold_used numeric;
alter table analyses add column if not exists natural_occurrence_statement text;
alter table analyses add column if not exists natural_occurrence_probability numeric;
alter table analyses add column if not exists feature_schema_version text;
alter table analyses add column if not exists report_schema_version text;
alter table analyses add column if not exists report_version int not null default 1;
alter table analyses add column if not exists report_locked boolean not null default false;
alter table analyses add column if not exists report_locked_at timestamptz;
alter table analyses add column if not exists legal_disclaimer_text text;
alter table analyses add column if not exists human_review_required boolean not null default false;
alter table analyses add column if not exists review_status text default 'pending';
alter table analyses add column if not exists explainability_method text;
alter table analyses add column if not exists explainability_items jsonb;
alter table analyses add column if not exists ml_fusion_source text;
alter table analyses add column if not exists ml_primary_score numeric;
alter table analyses add column if not exists ml_secondary_score numeric;
alter table analyses add column if not exists raw_request jsonb;
alter table analyses add column if not exists raw_response jsonb;

create table if not exists games (
  id text primary key,
  event_id text not null references events(id),
  white_player_id text not null references players(id),
  black_player_id text not null references players(id),
  pgn text,
  created_at timestamptz not null default now()
);

create table if not exists move_features (
  id bigserial primary key,
  game_id text not null references games(id),
  ply int not null,
  cp_loss numeric,
  engine_top1_match boolean,
  engine_top3_match boolean,
  maia_probability numeric,
  complexity_score int,
  is_opening_book boolean not null default false,
  is_tablebase boolean not null default false,
  is_forced boolean not null default false,
  time_spent_seconds numeric,
  created_at timestamptz not null default now()
);

alter table move_features add column if not exists engine_top1_match boolean;
alter table move_features add column if not exists engine_top3_match boolean;
alter table move_features add column if not exists maia_probability numeric;

create table if not exists engine_evals (
  id bigserial primary key,
  game_id text not null references games(id),
  move_number int not null,
  top1 text,
  top3 jsonb,
  centipawn_loss numeric,
  best_eval_cp numeric,
  played_eval_cp numeric,
  think_time numeric,
  created_at timestamptz not null default now()
);

create table if not exists cases (
  id uuid primary key default gen_random_uuid(),
  federation_id text not null references federations(id),
  event_id text references events(id),
  player_id text not null references players(id),
  status text not null default 'open' check (status in ('open', 'under_review', 'escalated', 'closed')),
  severity text not null default 'moderate' check (severity in ('low', 'moderate', 'elevated', 'high_statistical_anomaly')),
  opened_by_user_id uuid references app_users(id),
  assigned_to_user_id uuid references app_users(id),
  latest_analysis_audit_id text references analyses(external_audit_id),
  summary text,
  metadata jsonb not null default '{}'::jsonb,
  opened_at timestamptz not null default now(),
  closed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists case_analyses (
  case_id uuid not null references cases(id) on delete cascade,
  analysis_external_audit_id text not null references analyses(external_audit_id) on delete cascade,
  attached_at timestamptz not null default now(),
  primary key (case_id, analysis_external_audit_id)
);

create table if not exists case_reviews (
  id uuid primary key default gen_random_uuid(),
  case_id uuid not null references cases(id) on delete cascade,
  reviewer_user_id uuid references app_users(id),
  action text not null check (action in ('note', 'request_more_data', 'recommend_monitoring', 'recommend_escalation', 'close_case')),
  rationale text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists case_signoffs (
  id uuid primary key default gen_random_uuid(),
  case_id uuid not null references cases(id) on delete cascade,
  signer_user_id uuid references app_users(id),
  signer_role text not null,
  decision text not null check (decision in ('approved', 'rejected', 'returned_for_review')),
  note text,
  created_at timestamptz not null default now()
);

create table if not exists report_versions (
  id uuid primary key default gen_random_uuid(),
  analysis_external_audit_id text not null references analyses(external_audit_id) on delete cascade,
  version_no int not null,
  generated_by_user_id uuid references app_users(id),
  locked boolean not null default false,
  locked_at timestamptz,
  disclaimer_text text,
  report_body jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (analysis_external_audit_id, version_no)
);

create table if not exists calibration_profiles (
  id uuid primary key default gen_random_uuid(),
  profile_key text not null,
  profile_version text not null,
  schema_version int,
  source_dataset text,
  qa_report jsonb,
  profile_json jsonb not null,
  is_active boolean not null default false,
  created_by_user_id uuid references app_users(id),
  created_at timestamptz not null default now(),
  unique (profile_key, profile_version)
);

create table if not exists model_artifacts (
  id uuid primary key default gen_random_uuid(),
  artifact_type text not null check (artifact_type in ('maia', 'xgboost', 'isolation_forest', 'shap_background', 'calibration_profile')),
  name text not null,
  version text not null,
  storage_path text,
  checksum_sha256 text,
  metadata jsonb not null default '{}'::jsonb,
  is_active boolean not null default false,
  created_by_user_id uuid references app_users(id),
  created_at timestamptz not null default now(),
  unique (artifact_type, name, version)
);

create table if not exists event_incidents (
  id uuid primary key default gen_random_uuid(),
  federation_id text references federations(id),
  event_id text not null references events(id) on delete cascade,
  source_system text not null,
  incident_type text not null,
  severity text not null check (severity in ('low', 'medium', 'high', 'critical')),
  summary text not null,
  payload jsonb not null default '{}'::jsonb,
  occurred_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

create table if not exists case_notes (
  id uuid primary key default gen_random_uuid(),
  case_id uuid not null references cases(id) on delete cascade,
  author text,
  note_type text,
  structured jsonb not null default '{}'::jsonb,
  text text,
  created_at timestamptz not null default now()
);

create table if not exists case_evidence (
  id uuid primary key default gen_random_uuid(),
  case_id uuid not null references cases(id) on delete cascade,
  evidence_type text not null,
  label text,
  storage_path text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists case_flags (
  id uuid primary key default gen_random_uuid(),
  case_id uuid not null references cases(id) on delete cascade,
  flag_type text not null,
  severity text not null check (severity in ('info', 'low', 'medium', 'high', 'critical')),
  message text not null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists otb_incidents (
  id uuid primary key default gen_random_uuid(),
  case_id uuid references cases(id) on delete cascade,
  event_id text,
  player_id text,
  incident_type text not null,
  severity text not null check (severity in ('info', 'low', 'medium', 'high', 'critical')),
  description text,
  occurred_at timestamptz,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists report_exports (
  id uuid primary key default gen_random_uuid(),
  case_id uuid references cases(id) on delete cascade,
  analysis_external_audit_id text references analyses(external_audit_id) on delete cascade,
  report_type text not null,
  mode text not null check (mode in ('technical', 'arbiter', 'legal')),
  format text not null check (format in ('json', 'csv', 'pdf')),
  content jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists live_sessions (
  id uuid primary key default gen_random_uuid(),
  federation_id text references federations(id),
  event_id text references events(id) on delete cascade,
  players jsonb not null default '[]'::jsonb,
  status text not null default 'active' check (status in ('active', 'paused', 'closed')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists live_moves (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references live_sessions(id) on delete cascade,
  ply int not null,
  move_uci text not null,
  time_spent numeric,
  clock_remaining numeric,
  complexity numeric,
  engine_match numeric,
  maia_prob numeric,
  tags jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists player_profiles (
  player_id text primary key references players(id) on delete cascade,
  profile jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);

create table if not exists player_history (
  id uuid primary key default gen_random_uuid(),
  player_id text not null references players(id) on delete cascade,
  event_id text references events(id),
  snapshot jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists partner_api_keys (
  id uuid primary key default gen_random_uuid(),
  key text not null,
  key_hash text,
  secret text not null,
  partner_name text not null,
  webhook_url text,
  rate_limit_per_minute int not null default 60,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists partner_jobs (
  id uuid primary key default gen_random_uuid(),
  job_id text not null,
  api_key_id uuid not null references partner_api_keys(id) on delete cascade,
  game_id text not null,
  player_id text not null,
  raw_payload jsonb not null default '{}'::jsonb,
  status text not null default 'queued',
  risk_level text,
  risk_score numeric,
  result jsonb,
  webhook_url text,
  webhook_delivered boolean not null default false,
  webhook_attempts int not null default 0,
  created_at timestamptz not null default now(),
  completed_at timestamptz
);

create table if not exists partner_sessions (
  id uuid primary key default gen_random_uuid(),
  session_id text not null,
  api_key_id uuid not null references partner_api_keys(id) on delete cascade,
  game_id text,
  player_id text,
  status text not null default 'active',
  created_at timestamptz not null default now(),
  ended_at timestamptz
);

create table if not exists partner_payloads (
  id uuid primary key default gen_random_uuid(),
  job_id text not null references partner_jobs(job_id) on delete cascade,
  api_key_id uuid not null references partner_api_keys(id) on delete cascade,
  game_id text not null,
  player_id text not null,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists device_fingerprints (
  fingerprint_hash text primary key,
  first_seen timestamptz not null default now(),
  last_seen timestamptz not null default now(),
  last_player_id text,
  seen_count int not null default 1,
  distinct_players jsonb not null default '[]'::jsonb,
  metadata jsonb not null default '{}'::jsonb
);

create table if not exists camera_events (
  id uuid primary key default gen_random_uuid(),
  job_id text not null,
  mode text not null check (mode in ('safe', 'raw')),
  events jsonb not null default '[]'::jsonb,
  consent jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists consent_logs (
  id uuid primary key default gen_random_uuid(),
  job_id text not null,
  api_key_id uuid not null references partner_api_keys(id) on delete cascade,
  consent_type text not null,
  consent_given boolean not null default false,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists otb_camera_events (
  id uuid primary key default gen_random_uuid(),
  event_id text,
  case_id uuid references cases(id) on delete cascade,
  player_id text,
  session_id text,
  camera_id text,
  storage_mode text not null check (storage_mode in ('safe', 'raw')),
  consent jsonb not null default '{}'::jsonb,
  events jsonb not null default '[]'::jsonb,
  summary jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists dgt_board_events (
  id uuid primary key default gen_random_uuid(),
  event_id text,
  session_id uuid references live_sessions(id) on delete set null,
  board_serial text,
  move_uci text,
  ply int,
  fen text,
  clock_ms int,
  raw jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_analyses_player_event on analyses(player_id, event_id, created_at desc);
create index if not exists idx_analyses_federation_created on analyses(federation_id, created_at desc);
create index if not exists idx_analyses_review_status on analyses(review_status, created_at desc);
create index if not exists idx_move_features_game_ply on move_features(game_id, ply);
create index if not exists idx_engine_evals_game_move on engine_evals(game_id, move_number);
create index if not exists idx_players_federation on players(federation_id);
create index if not exists idx_events_federation_status on events(federation_id, status, created_at desc);
create index if not exists idx_cases_federation_status on cases(federation_id, status, created_at desc);
create index if not exists idx_case_reviews_case on case_reviews(case_id, created_at desc);
create index if not exists idx_report_versions_audit on report_versions(analysis_external_audit_id, version_no desc);
create index if not exists idx_calibration_profiles_key_active on calibration_profiles(profile_key, is_active, created_at desc);
create index if not exists idx_model_artifacts_type_active on model_artifacts(artifact_type, is_active, created_at desc);
create index if not exists idx_event_incidents_event_time on event_incidents(event_id, occurred_at desc);
create index if not exists idx_case_notes_case on case_notes(case_id, created_at desc);
create index if not exists idx_case_evidence_case on case_evidence(case_id, created_at desc);
create index if not exists idx_case_flags_case on case_flags(case_id, created_at desc);
create index if not exists idx_report_exports_case on report_exports(case_id, created_at desc);
create index if not exists idx_live_sessions_event on live_sessions(event_id, created_at desc);
create index if not exists idx_live_moves_session on live_moves(session_id, ply);
create index if not exists idx_player_history_player on player_history(player_id, created_at desc);
create index if not exists idx_partner_jobs_status on partner_jobs(status, created_at desc);
create index if not exists idx_partner_sessions_active on partner_sessions(status, created_at desc);
create index if not exists idx_partner_payloads_job on partner_payloads(job_id, created_at desc);
create index if not exists idx_device_fingerprints_last on device_fingerprints(last_seen desc);
create index if not exists idx_camera_events_job on camera_events(job_id, created_at desc);
create index if not exists idx_consent_logs_job on consent_logs(job_id, created_at desc);
create index if not exists idx_otb_camera_events_event on otb_camera_events(event_id, created_at desc);
create index if not exists idx_otb_camera_events_session on otb_camera_events(session_id, created_at desc);
create index if not exists idx_dgt_board_events_event on dgt_board_events(event_id, created_at desc);
<<<<<<< HEAD

-- Migration-safe uniqueness, lookup, and compatibility indexes.
create unique index if not exists idx_analyses_external_audit_id_unique
  on analyses(external_audit_id)
  where external_audit_id is not null;

create unique index if not exists idx_partner_jobs_job_id_unique on partner_jobs(job_id);
create unique index if not exists idx_partner_sessions_session_id_unique on partner_sessions(session_id);
create unique index if not exists idx_partner_payloads_job_id_unique on partner_payloads(job_id);
create unique index if not exists idx_partner_api_keys_key_hash_unique
  on partner_api_keys(key_hash)
  where key_hash is not null;
create index if not exists idx_partner_api_keys_federation_id on partner_api_keys(federation_id, created_at desc);

create index if not exists idx_case_analyses_case_id on case_analyses(case_id, attached_at desc);
create index if not exists idx_case_analyses_audit_id on case_analyses(analysis_external_audit_id);
create index if not exists idx_cases_event_id on cases(event_id);
create index if not exists idx_cases_player_id on cases(player_id);
create index if not exists idx_partner_jobs_api_key_id on partner_jobs(api_key_id, created_at desc);
create index if not exists idx_partner_jobs_federation_id on partner_jobs(federation_id, created_at desc);
create index if not exists idx_partner_jobs_player_id on partner_jobs(player_id, created_at desc);
create index if not exists idx_partner_jobs_game_id on partner_jobs(game_id, created_at desc);
create index if not exists idx_partner_sessions_api_key_id on partner_sessions(api_key_id, created_at desc);
create index if not exists idx_partner_sessions_federation_id on partner_sessions(federation_id, created_at desc);
create index if not exists idx_partner_payloads_federation_id on partner_payloads(federation_id, created_at desc);
create index if not exists idx_camera_events_federation_id on camera_events(federation_id, created_at desc);
create index if not exists idx_consent_logs_federation_id on consent_logs(federation_id, created_at desc);
create index if not exists idx_otb_incidents_case_id on otb_incidents(case_id, created_at desc);
create index if not exists idx_otb_incidents_event_id on otb_incidents(event_id, created_at desc);
create index if not exists idx_player_profiles_updated on player_profiles(updated_at desc);

-- Additive columns used by newer backend/frontend flows.
alter table analyses add column if not exists chain_hash text;
alter table analyses add column if not exists prev_chain_hash text;
alter table analyses add column if not exists evidence_report jsonb;
alter table analyses add column if not exists behavioral_metrics jsonb;
alter table analyses add column if not exists environmental_metrics jsonb;
alter table analyses add column if not exists identity_confidence jsonb;
alter table analyses add column if not exists confidence_intervals jsonb;
alter table analyses add column if not exists ipr_estimate numeric;
alter table analyses add column if not exists pep_score numeric;
alter table analyses add column if not exists regan_z_score numeric;
alter table analyses add column if not exists report_workflow jsonb not null default '{}'::jsonb;
alter table events add column if not exists source_system text;
alter table games add column if not exists source_system text;
alter table report_exports add column if not exists content_text text;
alter table report_exports add column if not exists report_id text;
alter table partner_jobs add column if not exists error_message text;
alter table partner_sessions add column if not exists metadata jsonb not null default '{}'::jsonb;
alter table partner_api_keys add column if not exists federation_id text references federations(id);
alter table partner_jobs add column if not exists federation_id text references federations(id);
alter table partner_sessions add column if not exists federation_id text references federations(id);
alter table partner_payloads add column if not exists federation_id text references federations(id);
alter table camera_events add column if not exists federation_id text references federations(id);
alter table consent_logs add column if not exists federation_id text references federations(id);
alter table live_sessions add column if not exists metadata jsonb not null default '{}'::jsonb;
alter table live_moves add column if not exists event_type text;
alter table player_profiles add column if not exists federation_id text references federations(id);
alter table player_history add column if not exists federation_id text references federations(id);
alter table otb_incidents add column if not exists federation_id text references federations(id);
alter table otb_camera_events add column if not exists federation_id text references federations(id);
alter table dgt_board_events add column if not exists federation_id text references federations(id);
alter table case_notes add column if not exists author_user_id uuid references app_users(id);
alter table case_evidence add column if not exists uploaded_by_user_id uuid references app_users(id);
alter table case_flags add column if not exists created_by_user_id uuid references app_users(id);

update partner_jobs pj
set federation_id = pak.federation_id
from partner_api_keys pak
where pj.api_key_id = pak.id
  and pj.federation_id is null;

update partner_sessions ps
set federation_id = pak.federation_id
from partner_api_keys pak
where ps.api_key_id = pak.id
  and ps.federation_id is null;

update partner_payloads pp
set federation_id = pak.federation_id
from partner_api_keys pak
where pp.api_key_id = pak.id
  and pp.federation_id is null;

update consent_logs cl
set federation_id = pak.federation_id
from partner_api_keys pak
where cl.api_key_id = pak.id
  and cl.federation_id is null;

update camera_events ce
set federation_id = pj.federation_id
from partner_jobs pj
where ce.job_id = pj.job_id
  and ce.federation_id is null;

-- Common trigger helpers.
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

create or replace function public.current_app_user_id()
returns uuid
language sql
stable
as $$
  select auth.uid()
$$;

create or replace function public.current_role_name()
returns text
language sql
stable
as $$
  select coalesce(
    nullif(auth.jwt() -> 'app_metadata' ->> 'role', ''),
    nullif(auth.jwt() -> 'user_metadata' ->> 'role', ''),
    'authenticated'
  )
$$;

create or replace function public.current_federation_id()
returns text
language sql
stable
as $$
  select coalesce(
    nullif(auth.jwt() -> 'app_metadata' ->> 'federation_id', ''),
    nullif(auth.jwt() -> 'user_metadata' ->> 'federation_id', '')
  )
$$;

create or replace function public.is_service_role()
returns boolean
language sql
stable
as $$
  select coalesce(auth.role() = 'service_role', false)
$$;

create or replace function public.has_federation_access(target_federation_id text)
returns boolean
language sql
stable
as $$
  select
    public.is_service_role()
    or target_federation_id is null
    or exists (
      select 1
      from federation_memberships fm
      where fm.user_id = public.current_app_user_id()
        and fm.federation_id = target_federation_id
        and fm.status = 'active'
    )
$$;

create or replace function public.has_case_write_access(target_federation_id text)
returns boolean
language sql
stable
as $$
  select
    public.is_service_role()
    or exists (
      select 1
      from federation_memberships fm
      where fm.user_id = public.current_app_user_id()
        and fm.federation_id = target_federation_id
        and fm.status = 'active'
        and fm.role in ('chief_arbiter', 'federation_admin', 'system_admin', 'reviewer', 'analyst', 'arbiter')
    )
$$;

create or replace function public.has_partner_admin_access(target_federation_id text default null)
returns boolean
language sql
stable
as $$
  select
    public.is_service_role()
    or public.current_role_name() in ('chief_arbiter', 'federation_admin', 'system_admin')
    or exists (
      select 1
      from federation_memberships fm
      where fm.user_id = public.current_app_user_id()
        and (target_federation_id is null or fm.federation_id = target_federation_id)
        and fm.status = 'active'
        and fm.role in ('chief_arbiter', 'federation_admin', 'system_admin')
    )
$$;

create or replace function public.resolve_event_federation()
returns trigger
language plpgsql
as $$
declare
  resolved_federation_id text;
begin
  if new.federation_id is not null then
    return new;
  end if;

  if new.event_id is not null then
    select e.federation_id into resolved_federation_id
    from events e
    where e.id = new.event_id;
    new.federation_id := resolved_federation_id;
  end if;

  return new;
end;
$$;

create or replace function public.resolve_partner_federation_from_api_key()
returns trigger
language plpgsql
as $$
declare
  resolved_federation_id text;
begin
  if new.federation_id is not null then
    return new;
  end if;

  if new.api_key_id is not null then
    select pak.federation_id into resolved_federation_id
    from partner_api_keys pak
    where pak.id = new.api_key_id;
    new.federation_id := resolved_federation_id;
  end if;

  return new;
end;
$$;

create or replace function public.resolve_partner_federation_from_job()
returns trigger
language plpgsql
as $$
declare
  resolved_federation_id text;
begin
  if new.federation_id is not null then
    return new;
  end if;

  if new.job_id is not null then
    select pj.federation_id into resolved_federation_id
    from partner_jobs pj
    where pj.job_id = new.job_id;
    new.federation_id := resolved_federation_id;
  end if;

  return new;
end;
$$;

create or replace function public.sync_report_workflow()
returns trigger
language plpgsql
as $$
begin
  insert into report_versions (
    analysis_external_audit_id,
    version_no,
    locked,
    locked_at,
    disclaimer_text,
    report_body
  )
  values (
    new.external_audit_id,
    coalesce(new.report_version, 1),
    coalesce(new.report_locked, false),
    new.report_locked_at,
    new.legal_disclaimer_text,
    coalesce(new.raw_response, '{}'::jsonb)
  )
  on conflict (analysis_external_audit_id, version_no)
  do update set
    locked = excluded.locked,
    locked_at = excluded.locked_at,
    disclaimer_text = excluded.disclaimer_text,
    report_body = excluded.report_body;

  return new;
end;
$$;

create or replace function public.touch_device_fingerprint()
returns trigger
language plpgsql
as $$
begin
  new.last_seen := now();
  return new;
end;
$$;

create or replace function public.link_case_analysis_from_analysis()
returns trigger
language plpgsql
as $$
begin
  if new.latest_analysis_audit_id is not null then
    insert into case_analyses (case_id, analysis_external_audit_id)
    values (new.id, new.latest_analysis_audit_id)
    on conflict do nothing;
  end if;
  return new;
end;
$$;

drop trigger if exists trg_federations_updated_at on federations;
create trigger trg_federations_updated_at
before update on federations
for each row execute function public.set_updated_at();

drop trigger if exists trg_app_users_updated_at on app_users;
create trigger trg_app_users_updated_at
before update on app_users
for each row execute function public.set_updated_at();

drop trigger if exists trg_federation_memberships_updated_at on federation_memberships;
create trigger trg_federation_memberships_updated_at
before update on federation_memberships
for each row execute function public.set_updated_at();

drop trigger if exists trg_cases_updated_at on cases;
create trigger trg_cases_updated_at
before update on cases
for each row execute function public.set_updated_at();

drop trigger if exists trg_events_resolve_federation on analyses;
create trigger trg_events_resolve_federation
before insert or update on analyses
for each row execute function public.resolve_event_federation();

drop trigger if exists trg_cases_link_analysis on cases;
create trigger trg_cases_link_analysis
after insert or update of latest_analysis_audit_id on cases
for each row execute function public.link_case_analysis_from_analysis();

drop trigger if exists trg_sync_report_workflow on analyses;
create trigger trg_sync_report_workflow
after insert or update of report_version, report_locked, report_locked_at, legal_disclaimer_text, raw_response
on analyses
for each row
when (new.external_audit_id is not null)
execute function public.sync_report_workflow();

drop trigger if exists trg_live_sessions_updated_at on live_sessions;
create trigger trg_live_sessions_updated_at
before update on live_sessions
for each row execute function public.set_updated_at();

drop trigger if exists trg_live_sessions_resolve_federation on live_sessions;
create trigger trg_live_sessions_resolve_federation
before insert or update on live_sessions
for each row execute function public.resolve_event_federation();

drop trigger if exists trg_player_profiles_updated_at on player_profiles;
create trigger trg_player_profiles_updated_at
before update on player_profiles
for each row execute function public.set_updated_at();

drop trigger if exists trg_device_fingerprint_touch on device_fingerprints;
create trigger trg_device_fingerprint_touch
before update on device_fingerprints
for each row execute function public.touch_device_fingerprint();

drop trigger if exists trg_otb_incidents_resolve_federation on otb_incidents;
create trigger trg_otb_incidents_resolve_federation
before insert or update on otb_incidents
for each row execute function public.resolve_event_federation();

drop trigger if exists trg_otb_camera_events_resolve_federation on otb_camera_events;
create trigger trg_otb_camera_events_resolve_federation
before insert or update on otb_camera_events
for each row execute function public.resolve_event_federation();

drop trigger if exists trg_dgt_board_events_resolve_federation on dgt_board_events;
create trigger trg_dgt_board_events_resolve_federation
before insert or update on dgt_board_events
for each row execute function public.resolve_event_federation();

drop trigger if exists trg_partner_jobs_resolve_federation on partner_jobs;
create trigger trg_partner_jobs_resolve_federation
before insert or update on partner_jobs
for each row execute function public.resolve_partner_federation_from_api_key();

drop trigger if exists trg_partner_sessions_resolve_federation on partner_sessions;
create trigger trg_partner_sessions_resolve_federation
before insert or update on partner_sessions
for each row execute function public.resolve_partner_federation_from_api_key();

drop trigger if exists trg_partner_payloads_resolve_federation on partner_payloads;
create trigger trg_partner_payloads_resolve_federation
before insert or update on partner_payloads
for each row execute function public.resolve_partner_federation_from_api_key();

drop trigger if exists trg_consent_logs_resolve_federation on consent_logs;
create trigger trg_consent_logs_resolve_federation
before insert or update on consent_logs
for each row execute function public.resolve_partner_federation_from_api_key();

drop trigger if exists trg_camera_events_resolve_federation on camera_events;
create trigger trg_camera_events_resolve_federation
before insert or update on camera_events
for each row execute function public.resolve_partner_federation_from_job();

-- Useful operational views.
create or replace view public.partner_job_overview as
select
  pj.id,
  pj.job_id,
  pj.api_key_id,
  pj.federation_id,
  pak.partner_name,
  pj.game_id,
  pj.player_id,
  pj.status,
  pj.risk_level,
  pj.risk_score,
  pj.webhook_url,
  pj.webhook_delivered,
  pj.webhook_attempts,
  pj.created_at,
  pj.completed_at
from partner_jobs pj
join partner_api_keys pak on pak.id = pj.api_key_id;

create or replace view public.case_workspace_overview as
select
  c.id,
  c.federation_id,
  c.event_id,
  c.player_id,
  c.status,
  c.severity,
  c.summary,
  c.opened_at,
  c.updated_at,
  coalesce(note_stats.note_count, 0) as note_count,
  coalesce(flag_stats.flag_count, 0) as flag_count,
  coalesce(evidence_stats.evidence_count, 0) as evidence_count,
  coalesce(analysis_stats.analysis_count, 0) as analysis_count
from cases c
left join (
  select case_id, count(*) as note_count
  from case_notes
  group by case_id
) note_stats on note_stats.case_id = c.id
left join (
  select case_id, count(*) as flag_count
  from case_flags
  group by case_id
) flag_stats on flag_stats.case_id = c.id
left join (
  select case_id, count(*) as evidence_count
  from case_evidence
  group by case_id
) evidence_stats on evidence_stats.case_id = c.id
left join (
  select case_id, count(*) as analysis_count
  from case_analyses
  group by case_id
) analysis_stats on analysis_stats.case_id = c.id;

create or replace view public.analysis_feed_overview as
select
  a.external_audit_id,
  a.player_id,
  a.event_id,
  a.federation_id,
  a.risk_tier,
  a.weighted_risk_score,
  a.confidence,
  a.analyzed_move_count,
  a.review_status,
  a.report_locked,
  a.created_at
from analyses a
where a.external_audit_id is not null;

-- Dashboard-friendly RPC functions.
create or replace function public.get_dashboard_feed(target_federation_id text default null, row_limit integer default 100)
returns table (
  external_audit_id text,
  player_id text,
  event_id text,
  federation_id text,
  risk_tier text,
  weighted_risk_score numeric,
  confidence numeric,
  analyzed_move_count integer,
  created_at timestamptz
)
language sql
stable
as $$
  select
    a.external_audit_id,
    a.player_id,
    a.event_id,
    a.federation_id,
    a.risk_tier,
    a.weighted_risk_score,
    a.confidence,
    a.analyzed_move_count,
    a.created_at
  from analyses a
  where a.external_audit_id is not null
    and (target_federation_id is null or a.federation_id = target_federation_id)
  order by a.created_at desc
  limit greatest(1, least(coalesce(row_limit, 100), 500))
$$;

create or replace function public.get_partner_job_summary(target_api_key_id uuid default null, row_limit integer default 100)
returns table (
  job_id text,
  api_key_id uuid,
  federation_id text,
  partner_name text,
  game_id text,
  player_id text,
  status text,
  risk_level text,
  risk_score numeric,
  webhook_delivered boolean,
  webhook_attempts integer,
  created_at timestamptz,
  completed_at timestamptz
)
language sql
stable
as $$
  select
    pj.job_id,
    pj.api_key_id,
    pj.federation_id,
    pak.partner_name,
    pj.game_id,
    pj.player_id,
    pj.status,
    pj.risk_level,
    pj.risk_score,
    pj.webhook_delivered,
    pj.webhook_attempts,
    pj.created_at,
    pj.completed_at
  from partner_jobs pj
  join partner_api_keys pak on pak.id = pj.api_key_id
  where target_api_key_id is null or pj.api_key_id = target_api_key_id
  order by pj.created_at desc
  limit greatest(1, least(coalesce(row_limit, 100), 500))
$$;

-- RLS baseline.
alter table federations enable row level security;
alter table app_users enable row level security;
alter table federation_memberships enable row level security;
alter table players enable row level security;
alter table events enable row level security;
alter table analyses enable row level security;
alter table games enable row level security;
alter table move_features enable row level security;
alter table engine_evals enable row level security;
alter table cases enable row level security;
alter table case_analyses enable row level security;
alter table case_reviews enable row level security;
alter table case_signoffs enable row level security;
alter table report_versions enable row level security;
alter table calibration_profiles enable row level security;
alter table model_artifacts enable row level security;
alter table event_incidents enable row level security;
alter table case_notes enable row level security;
alter table case_evidence enable row level security;
alter table case_flags enable row level security;
alter table otb_incidents enable row level security;
alter table report_exports enable row level security;
alter table live_sessions enable row level security;
alter table live_moves enable row level security;
alter table player_profiles enable row level security;
alter table player_history enable row level security;
alter table partner_api_keys enable row level security;
alter table partner_jobs enable row level security;
alter table partner_sessions enable row level security;
alter table partner_payloads enable row level security;
alter table device_fingerprints enable row level security;
alter table camera_events enable row level security;
alter table consent_logs enable row level security;
alter table otb_camera_events enable row level security;
alter table dgt_board_events enable row level security;

do $$
begin
  if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'federations' and policyname = 'federations_select') then
    create policy federations_select on federations
      for select using (public.has_federation_access(id));
  end if;
  if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'federations' and policyname = 'federations_admin_write') then
    create policy federations_admin_write on federations
      for all using (public.has_partner_admin_access(id))
      with check (public.has_partner_admin_access(id));
  end if;
end $$;

do $$
begin
  if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'app_users' and policyname = 'app_users_self_select') then
    create policy app_users_self_select on app_users
      for select using (public.is_service_role() or id = public.current_app_user_id());
  end if;
  if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'app_users' and policyname = 'app_users_self_update') then
    create policy app_users_self_update on app_users
      for update using (public.is_service_role() or id = public.current_app_user_id())
      with check (public.is_service_role() or id = public.current_app_user_id());
  end if;
end $$;

do $$
begin
  if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'federation_memberships' and policyname = 'memberships_visible_in_federation') then
    create policy memberships_visible_in_federation on federation_memberships
      for select using (
        public.is_service_role()
        or user_id = public.current_app_user_id()
        or public.has_partner_admin_access(federation_id)
      );
  end if;
  if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'federation_memberships' and policyname = 'memberships_admin_write') then
    create policy memberships_admin_write on federation_memberships
      for all using (public.has_partner_admin_access(federation_id))
      with check (public.has_partner_admin_access(federation_id));
  end if;
end $$;

do $$
declare
  tbl text;
begin
  foreach tbl in array array[
    'players','events','analyses','cases','event_incidents','live_sessions',
    'player_profiles','player_history','otb_incidents','otb_camera_events','dgt_board_events'
  ]
  loop
    if not exists (
      select 1 from pg_policies
      where schemaname = 'public' and tablename = tbl and policyname = tbl || '_federation_select'
    ) then
      execute format(
        'create policy %I on %I for select using (public.is_service_role() or public.has_federation_access(federation_id))',
        tbl || '_federation_select',
        tbl
      );
    end if;
    if not exists (
      select 1 from pg_policies
      where schemaname = 'public' and tablename = tbl and policyname = tbl || '_federation_write'
    ) then
      execute format(
        'create policy %I on %I for all using (public.is_service_role() or public.has_case_write_access(federation_id)) with check (public.is_service_role() or public.has_case_write_access(federation_id))',
        tbl || '_federation_write',
        tbl
      );
    end if;
  end loop;
end $$;

do $$
begin
  if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'games' and policyname = 'games_visible_by_event') then
    create policy games_visible_by_event on games
      for select using (
        public.is_service_role()
        or exists (
          select 1 from events e
          where e.id = games.event_id
            and public.has_federation_access(e.federation_id)
        )
      );
  end if;
  if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'games' and policyname = 'games_write_by_event') then
    create policy games_write_by_event on games
      for all using (
        public.is_service_role()
        or exists (
          select 1 from events e
          where e.id = games.event_id
            and public.has_case_write_access(e.federation_id)
        )
      )
      with check (
        public.is_service_role()
        or exists (
          select 1 from events e
          where e.id = games.event_id
            and public.has_case_write_access(e.federation_id)
        )
      );
  end if;
end $$;

do $$
declare
  child_tbl text;
  fk_col text;
begin
  for child_tbl, fk_col in
    select * from (values
      ('move_features','game_id'),
      ('engine_evals','game_id')
    ) as t(child_tbl, fk_col)
  loop
    if not exists (
      select 1 from pg_policies
      where schemaname = 'public' and tablename = child_tbl and policyname = child_tbl || '_via_game_select'
    ) then
      execute format(
        'create policy %I on %I for select using (
          public.is_service_role()
          or exists (
            select 1
            from games g
            join events e on e.id = g.event_id
            where g.id = %I.%I
              and public.has_federation_access(e.federation_id)
          )
        )',
        child_tbl || '_via_game_select',
        child_tbl,
        child_tbl,
        fk_col
      );
    end if;
    if not exists (
      select 1 from pg_policies
      where schemaname = 'public' and tablename = child_tbl and policyname = child_tbl || '_via_game_write'
    ) then
      execute format(
        'create policy %I on %I for all using (
          public.is_service_role()
          or exists (
            select 1
            from games g
            join events e on e.id = g.event_id
            where g.id = %I.%I
              and public.has_case_write_access(e.federation_id)
          )
        )
        with check (
          public.is_service_role()
          or exists (
            select 1
            from games g
            join events e on e.id = g.event_id
            where g.id = %I.%I
              and public.has_case_write_access(e.federation_id)
          )
        )',
        child_tbl || '_via_game_write',
        child_tbl,
        child_tbl,
        fk_col,
        child_tbl,
        fk_col
      );
    end if;
  end loop;
end $$;

do $$
declare
  child_tbl text;
begin
  foreach child_tbl in array array[
    'case_analyses','case_reviews','case_signoffs','case_notes','case_evidence','case_flags','report_exports'
  ]
  loop
    if not exists (
      select 1 from pg_policies
      where schemaname = 'public' and tablename = child_tbl and policyname = child_tbl || '_via_case_select'
    ) then
      execute format(
        'create policy %I on %I for select using (
          public.is_service_role()
          or exists (
            select 1 from cases c
            where c.id = %I.case_id
              and public.has_federation_access(c.federation_id)
          )
        )',
        child_tbl || '_via_case_select',
        child_tbl,
        child_tbl
      );
    end if;
    if not exists (
      select 1 from pg_policies
      where schemaname = 'public' and tablename = child_tbl and policyname = child_tbl || '_via_case_write'
    ) then
      execute format(
        'create policy %I on %I for all using (
          public.is_service_role()
          or exists (
            select 1 from cases c
            where c.id = %I.case_id
              and public.has_case_write_access(c.federation_id)
          )
        )
        with check (
          public.is_service_role()
          or exists (
            select 1 from cases c
            where c.id = %I.case_id
              and public.has_case_write_access(c.federation_id)
          )
        )',
        child_tbl || '_via_case_write',
        child_tbl,
        child_tbl,
        child_tbl
      );
    end if;
  end loop;
end $$;

do $$
begin
  if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'report_versions' and policyname = 'report_versions_via_analysis_select') then
    create policy report_versions_via_analysis_select on report_versions
      for select using (
        public.is_service_role()
        or exists (
          select 1 from analyses a
          where a.external_audit_id = report_versions.analysis_external_audit_id
            and public.has_federation_access(a.federation_id)
        )
      );
  end if;
  if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'report_versions' and policyname = 'report_versions_via_analysis_write') then
    create policy report_versions_via_analysis_write on report_versions
      for all using (
        public.is_service_role()
        or exists (
          select 1 from analyses a
          where a.external_audit_id = report_versions.analysis_external_audit_id
            and public.has_case_write_access(a.federation_id)
        )
      )
      with check (
        public.is_service_role()
        or exists (
          select 1 from analyses a
          where a.external_audit_id = report_versions.analysis_external_audit_id
            and public.has_case_write_access(a.federation_id)
        )
      );
  end if;
end $$;

do $$
declare
  scoped_tbl text;
begin
  foreach scoped_tbl in array array[
    'partner_api_keys','partner_jobs','partner_sessions','partner_payloads','camera_events','consent_logs'
  ]
  loop
    execute format('drop policy if exists %I on %I', scoped_tbl || '_admin_only', scoped_tbl);
    if not exists (
      select 1 from pg_policies
      where schemaname = 'public' and tablename = scoped_tbl and policyname = scoped_tbl || '_federation_admin'
    ) then
      execute format(
        'create policy %I on %I for all using (public.is_service_role() or public.has_partner_admin_access(federation_id)) with check (public.is_service_role() or public.has_partner_admin_access(federation_id))',
        scoped_tbl || '_federation_admin',
        scoped_tbl
      );
    end if;
  end loop;
end $$;

do $$
declare
  tbl text;
begin
  foreach tbl in array array[
    'calibration_profiles','model_artifacts','device_fingerprints'
  ]
  loop
    if not exists (
      select 1 from pg_policies
      where schemaname = 'public' and tablename = tbl and policyname = tbl || '_admin_only'
    ) then
      execute format(
        'create policy %I on %I for all using (public.has_partner_admin_access()) with check (public.has_partner_admin_access())',
        tbl || '_admin_only',
        tbl
      );
    end if;
  end loop;
end $$;

grant usage on schema public to authenticated, anon, service_role;
grant select on public.analysis_feed_overview to authenticated, service_role;
grant select on public.case_workspace_overview to authenticated, service_role;
grant select on public.partner_job_overview to authenticated, service_role;
grant execute on function public.get_dashboard_feed(text, integer) to authenticated, service_role;
grant execute on function public.get_partner_job_summary(uuid, integer) to authenticated, service_role;
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
