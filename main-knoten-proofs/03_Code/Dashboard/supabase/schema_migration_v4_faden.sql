-- Fusion Hero OS — Faden-Threads (Stärke-Stufen) v4
-- Nach schema_migration_v3_realtime.sql ausführen. Idempotent.

create table if not exists public.fusion_faden_threads (
  thread_id text primary key,
  device_id text not null default 'fusion-pc',
  strength text not null default 'mittel',
  label text default '',
  source text default '',
  layer int not null default 0,
  lambda_contract double precision not null default 0.74,
  fixpoint_id text default '',
  state jsonb not null default '{}'::jsonb,
  created_at double precision not null default extract(epoch from now()),
  updated_at double precision not null default extract(epoch from now()),
  expires_at double precision,
  payload jsonb default '{}'::jsonb
);

alter table public.fusion_faden_threads enable row level security;

create policy "fusion_faden_threads_anon_insert" on public.fusion_faden_threads
  for insert to anon with check (true);
create policy "fusion_faden_threads_anon_select" on public.fusion_faden_threads
  for select to anon using (true);
create policy "fusion_faden_threads_anon_update" on public.fusion_faden_threads
  for update to anon using (true);

do $$
begin
  alter publication supabase_realtime add table public.fusion_faden_threads;
exception
  when duplicate_object then null;
end $$;