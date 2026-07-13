-- Fusion Hero OS — Supabase Schema
-- Projekt: swmmoxhdzarmoupyssqe
-- Dashboard: https://supabase.com/dashboard/project/swmmoxhdzarmoupyssqe
-- SQL Editor → New query → Run

create table if not exists public.fusion_events (
  id bigint generated always as identity primary key,
  event_id text,
  event_type text not null default 'info',
  message text,
  severity text,
  layer int,
  ts double precision not null default extract(epoch from now()),
  payload jsonb default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.fusion_metrics (
  id bigint generated always as identity primary key,
  cpu_pct double precision,
  ram_pct double precision,
  events_count int,
  subs_count int,
  ops_per_sec double precision,
  ts double precision not null default extract(epoch from now()),
  payload jsonb default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.fusion_jobs (
  id bigint generated always as identity primary key,
  job_id text,
  query text,
  category text,
  dom text,
  status text default 'received',
  ts double precision not null default extract(epoch from now()),
  payload jsonb default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.heroic_llama_configs (
  id bigint generated always as identity primary key,
  algorithm text,
  model_path text,
  generation jsonb default '{}'::jsonb,
  metrics jsonb default '{}'::jsonb,
  ts double precision not null default extract(epoch from now()),
  created_at timestamptz not null default now()
);

alter table public.fusion_events enable row level security;
alter table public.fusion_metrics enable row level security;
alter table public.fusion_jobs enable row level security;
alter table public.heroic_llama_configs enable row level security;

create policy "fusion_events_anon_insert" on public.fusion_events
  for insert to anon with check (true);
create policy "fusion_events_anon_select" on public.fusion_events
  for select to anon using (true);

create policy "fusion_metrics_anon_insert" on public.fusion_metrics
  for insert to anon with check (true);
create policy "fusion_metrics_anon_select" on public.fusion_metrics
  for select to anon using (true);

create policy "fusion_jobs_anon_insert" on public.fusion_jobs
  for insert to anon with check (true);
create policy "fusion_jobs_anon_select" on public.fusion_jobs
  for select to anon using (true);

create policy "heroic_llama_configs_anon_insert" on public.heroic_llama_configs
  for insert to anon with check (true);
create policy "heroic_llama_configs_anon_select" on public.heroic_llama_configs
  for select to anon using (true);

create index if not exists fusion_events_ts_idx on public.fusion_events (ts desc);
create index if not exists fusion_metrics_ts_idx on public.fusion_metrics (ts desc);
create index if not exists fusion_jobs_ts_idx on public.fusion_jobs (ts desc);