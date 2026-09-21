-- Manual RLS validation pack for Sentinel Supabase schema.
-- Run this in a staging or local Postgres/Supabase SQL editor after applying schema.sql.
-- Sections are isolated with transactions so you can run all at once and roll back.

begin;

-- Seed minimal fixture data.
insert into federations (id, name)
values
  ('fed_alpha', 'Federation Alpha'),
  ('fed_beta', 'Federation Beta')
on conflict (id) do update set name = excluded.name;

insert into app_users (id, email, display_name)
values
  ('00000000-0000-0000-0000-000000000101', 'chief@alpha.test', 'Alpha Chief'),
  ('00000000-0000-0000-0000-000000000102', 'arbiter@alpha.test', 'Alpha Arbiter'),
  ('00000000-0000-0000-0000-000000000103', 'arbiter@beta.test', 'Beta Arbiter')
on conflict (id) do update set
  email = excluded.email,
  display_name = excluded.display_name;

insert into federation_memberships (federation_id, user_id, role, status, can_lock_reports, can_sign_cases)
values
  ('fed_alpha', '00000000-0000-0000-0000-000000000101', 'chief_arbiter', 'active', true, true),
  ('fed_alpha', '00000000-0000-0000-0000-000000000102', 'arbiter', 'active', false, false),
  ('fed_beta', '00000000-0000-0000-0000-000000000103', 'arbiter', 'active', false, false)
on conflict (federation_id, user_id, role) do update set
  status = excluded.status,
  can_lock_reports = excluded.can_lock_reports,
  can_sign_cases = excluded.can_sign_cases;

insert into players (id, display_name, federation_id)
values
  ('player_alpha', 'Player Alpha', 'fed_alpha'),
  ('player_beta', 'Player Beta', 'fed_beta')
on conflict (id) do update set
  display_name = excluded.display_name,
  federation_id = excluded.federation_id;

insert into events (id, federation_id, name, event_type, status)
values
  ('fed_alpha::event_1', 'fed_alpha', 'Alpha Open', 'online', 'live'),
  ('fed_beta::event_1', 'fed_beta', 'Beta Open', 'online', 'live')
on conflict (id) do update set
  federation_id = excluded.federation_id,
  name = excluded.name,
  event_type = excluded.event_type,
  status = excluded.status;

insert into analyses (
  external_audit_id,
  player_id,
  event_id,
  federation_id,
  risk_tier,
  confidence,
  analyzed_move_count,
  triggered_signals,
  weighted_risk_score,
  event_type,
  model_version,
  input_hash,
  explanation,
  signals,
  raw_request,
  raw_response
)
values
  (
    'audit_alpha_1',
    'player_alpha',
    'fed_alpha::event_1',
    'fed_alpha',
    'moderate',
    0.72,
    36,
    2,
    0.68,
    'online',
    'demo',
    'hash_alpha_1',
    '["alpha explanation"]'::jsonb,
    '[{"signal":"regan"}]'::jsonb,
    '{"player_id":"player_alpha"}'::jsonb,
    '{"report_version":1}'::jsonb
  ),
  (
    'audit_beta_1',
    'player_beta',
    'fed_beta::event_1',
    'fed_beta',
    'moderate',
    0.63,
    31,
    1,
    0.59,
    'online',
    'demo',
    'hash_beta_1',
    '["beta explanation"]'::jsonb,
    '[{"signal":"timing"}]'::jsonb,
    '{"player_id":"player_beta"}'::jsonb,
    '{"report_version":1}'::jsonb
  )
on conflict (external_audit_id) do update set
  federation_id = excluded.federation_id,
  weighted_risk_score = excluded.weighted_risk_score,
  raw_response = excluded.raw_response;

insert into cases (id, federation_id, event_id, player_id, status, severity, summary, latest_analysis_audit_id)
values
  ('10000000-0000-0000-0000-000000000001', 'fed_alpha', 'fed_alpha::event_1', 'player_alpha', 'open', 'moderate', 'Alpha case', 'audit_alpha_1')
on conflict (id) do update set
  federation_id = excluded.federation_id,
  event_id = excluded.event_id,
  player_id = excluded.player_id,
  latest_analysis_audit_id = excluded.latest_analysis_audit_id;

insert into partner_api_keys (id, key, key_hash, secret, partner_name, federation_id, webhook_url, active)
values
  (
    '20000000-0000-0000-0000-000000000001',
    'enc_key_alpha',
    'hash_key_alpha',
    'enc_secret_alpha',
    'Alpha Partner',
    'fed_alpha',
    'https://partner.alpha.test/webhook',
    true
  )
on conflict (id) do update set
  partner_name = excluded.partner_name,
  federation_id = excluded.federation_id,
  webhook_url = excluded.webhook_url,
  active = excluded.active;

insert into partner_jobs (job_id, api_key_id, game_id, player_id, raw_payload, status, webhook_url)
values
  (
    'job_alpha_1',
    '20000000-0000-0000-0000-000000000001',
    'game_alpha_1',
    'player_alpha',
    '{"pgn":"1. e4 e5"}'::jsonb,
    'queued',
    'https://partner.alpha.test/webhook'
  )
on conflict (job_id) do update set
  status = excluded.status,
  raw_payload = excluded.raw_payload;

insert into partner_payloads (job_id, api_key_id, game_id, player_id, payload)
values
  (
    'job_alpha_1',
    '20000000-0000-0000-0000-000000000001',
    'game_alpha_1',
    'player_alpha',
    '{"submitted_by":"validation"}'::jsonb
  )
on conflict (job_id) do update set
  payload = excluded.payload;

savepoint seeded;

-- Service role: should see and write across all federations and partner tables.
set local role service_role;
select set_config(
  'request.jwt.claims',
  '{"sub":"00000000-0000-0000-0000-000000000999","role":"service_role","app_metadata":{"role":"system_admin"}}',
  true
);

select 'service_role analyses count' as check_name, count(*) as observed
from analyses;

select 'service_role partner jobs count' as check_name, count(*) as observed
from partner_jobs;

insert into case_notes (case_id, author, note_type, text)
values ('10000000-0000-0000-0000-000000000001', 'service-role', 'ops', 'service role write ok');

rollback to savepoint seeded;

-- Authenticated federation member in fed_alpha: should see only fed_alpha data.
set local role authenticated;
select set_config(
  'request.jwt.claims',
  '{"sub":"00000000-0000-0000-0000-000000000102","role":"authenticated","app_metadata":{"role":"arbiter","federation_id":"fed_alpha"}}',
  true
);

select 'alpha member visible analyses' as check_name, array_agg(external_audit_id order by external_audit_id) as observed
from analyses;

select 'alpha member visible cases' as check_name, array_agg(id order by id) as observed
from cases;

select 'alpha member dashboard feed' as check_name, array_agg(external_audit_id order by external_audit_id) as observed
from public.get_dashboard_feed('fed_alpha', 20);

insert into case_notes (case_id, author, note_type, text, author_user_id)
values (
  '10000000-0000-0000-0000-000000000001',
  'alpha arbiter',
  'investigation',
  'alpha arbiter write ok',
  '00000000-0000-0000-0000-000000000102'
);

-- This should fail for a normal arbiter because partner tables are admin-only.
-- Expect: new row violates row-level security policy.
do $$
begin
  insert into partner_jobs (job_id, api_key_id, game_id, player_id, raw_payload, status)
  values (
    'job_should_fail_alpha_member',
    '20000000-0000-0000-0000-000000000001',
    'game_alpha_2',
    'player_alpha',
    '{"attempt":"member"}'::jsonb,
    'queued'
  );
  raise exception 'Expected RLS denial for non-admin partner job insert, but insert succeeded';
exception
  when insufficient_privilege then
    raise notice 'Expected denial confirmed for alpha arbiter partner_jobs insert';
end $$;

rollback to savepoint seeded;

-- Authenticated user from another federation: should not see fed_alpha rows.
set local role authenticated;
select set_config(
  'request.jwt.claims',
  '{"sub":"00000000-0000-0000-0000-000000000103","role":"authenticated","app_metadata":{"role":"arbiter","federation_id":"fed_beta"}}',
  true
);

select 'beta member visible analyses' as check_name, array_agg(external_audit_id order by external_audit_id) as observed
from analyses;

select 'beta member visible cases' as check_name, array_agg(id order by id) as observed
from cases;

-- This should fail because the beta user should not be able to write into a fed_alpha case.
do $$
begin
  insert into case_notes (case_id, author, note_type, text, author_user_id)
  values (
    '10000000-0000-0000-0000-000000000001',
    'beta arbiter',
    'investigation',
    'beta should be denied',
    '00000000-0000-0000-0000-000000000103'
  );
  raise exception 'Expected cross-federation case note denial, but insert succeeded';
exception
  when insufficient_privilege then
    raise notice 'Expected denial confirmed for beta arbiter case_notes insert';
end $$;

rollback to savepoint seeded;

-- Federation chief/admin: should be able to access partner admin surfaces.
set local role authenticated;
select set_config(
  'request.jwt.claims',
  '{"sub":"00000000-0000-0000-0000-000000000101","role":"authenticated","app_metadata":{"role":"chief_arbiter","federation_id":"fed_alpha"}}',
  true
);

select 'chief visible partner jobs' as check_name, array_agg(job_id order by job_id) as observed
from partner_jobs;

select 'chief partner summary rpc' as check_name, array_agg(job_id order by job_id) as observed
from public.get_partner_job_summary(null, 20);

insert into partner_jobs (job_id, api_key_id, game_id, player_id, raw_payload, status)
values (
  'job_alpha_admin_ok',
  '20000000-0000-0000-0000-000000000001',
  'game_alpha_3',
  'player_alpha',
  '{"attempt":"chief"}'::jsonb,
  'queued'
);

rollback;
