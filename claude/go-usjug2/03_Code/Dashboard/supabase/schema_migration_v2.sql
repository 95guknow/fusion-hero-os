-- Fusion Hero OS — Supabase Schema v2 (Watch, Settings, Audit, Phone Link)
-- Nach schema.sql ausführen. Idempotent (IF NOT EXISTS).

-- 1) Watch Together Raum-Persistenz
create table if not exists public.watch_rooms (
  room_id text primary key,
  video_id text default '',
  position double precision not null default 0,
  playing boolean not null default false,
  title text default '',
  updated_at double precision not null default extract(epoch from now()),
  created_at double precision not null default extract(epoch from now()),
  payload jsonb default '{}'::jsonb
);

-- 2) Einstellungen pro Gerät (Cloud-Spiegel)
create table if not exists public.fusion_settings_cloud (
  device_id text primary key,
  env jsonb not null default '{}'::jsonb,
  ui jsonb not null default '{}'::jsonb,
  updated_at double precision not null default extract(epoch from now()),
  set_by text default 'api'
);

-- 3) Agent/Job-Audit (erweitert)
create table if not exists public.fusion_agent_audit (
  id bigint generated always as identity primary key,
  job_id text,
  action text not null,
  agent text,
  dom text,
  category text,
  status text default 'ok',
  query text,
  ts double precision not null default extract(epoch from now()),
  payload jsonb default '{}'::jsonb,
  created_at timestamptz not null default now()
);

-- 4) Phone Link Snapshots (Verlauf, keine SMS-Inhalte)
create table if not exists public.phone_link_snapshots (
  id bigint generated always as identity primary key,
  connected boolean not null default false,
  host_running boolean not null default false,
  conversation_count int default 0,
  message_count int default 0,
  unread_total int default 0,
  notification_count int default 0,
  ts double precision not null default extract(epoch from now()),
  payload jsonb default '{}'::jsonb,
  created_at timestamptz not null default now()
);

alter table public.watch_rooms enable row level security;
alter table public.fusion_settings_cloud enable row level security;
alter table public.fusion_agent_audit enable row level security;
alter table public.phone_link_snapshots enable row level security;

create policy "watch_rooms_anon_insert" on public.watch_rooms
  for insert to anon with check (true);
create policy "watch_rooms_anon_select" on public.watch_rooms
  for select to anon using (true);
create policy "watch_rooms_anon_update" on public.watch_rooms
  for update to anon using (true);

create policy "fusion_settings_cloud_anon_insert" on public.fusion_settings_cloud
  for insert to anon with check (true);
create policy "fusion_settings_cloud_anon_select" on public.fusion_settings_cloud
  for select to anon using (true);
create policy "fusion_settings_cloud_anon_update" on public.fusion_settings_cloud
  for update to anon using (true);

create policy "fusion_agent_audit_anon_insert" on public.fusion_agent_audit
  for insert to anon with check (true);
create policy "fusion_agent_audit_anon_select" on public.fusion_agent_audit
  for select to anon using (true);

create policy "phone_link_snapshots_anon_insert" on public.phone_link_snapshots
  for insert to anon with check (true);
create policy "phone_link_snapshots_anon_select" on public.phone_link_snapshots
  for select to anon using (true);

create index if not exists watch_rooms_updated_idx on public.watch_rooms (updated_at desc);
create index if not exists fusion_agent_audit_ts_idx on public.fusion_agent_audit (ts desc);
create index if not exists phone_link_snapshots_ts_idx on public.phone_link_snapshots (ts desc);