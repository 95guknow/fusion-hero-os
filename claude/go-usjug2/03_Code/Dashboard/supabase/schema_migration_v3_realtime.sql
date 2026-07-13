-- Fusion Hero OS — Watch Together Realtime (Supabase Publication)
-- Nach schema_migration_v2.sql ausführen. Idempotent.

-- watch_rooms in die Supabase Realtime Publication aufnehmen
do $$
begin
  alter publication supabase_realtime add table public.watch_rooms;
exception
  when duplicate_object then null;
end $$;