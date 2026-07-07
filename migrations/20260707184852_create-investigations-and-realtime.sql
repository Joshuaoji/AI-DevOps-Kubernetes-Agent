-- Investigation history + realtime channel for progress updates.

-- 1. Investigation history table (one row per completed investigation).
CREATE TABLE IF NOT EXISTS public.investigations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
  root_cause TEXT,
  namespace TEXT,
  confidence INTEGER,
  status TEXT NOT NULL DEFAULT 'completed',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.investigations ENABLE ROW LEVEL SECURITY;

-- Users can only see and create their own investigation history.
CREATE POLICY "users_insert_own_investigations" ON public.investigations
  FOR INSERT TO authenticated
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "users_read_own_investigations" ON public.investigations
  FOR SELECT TO authenticated
  USING (user_id = auth.uid());

GRANT USAGE ON SCHEMA public TO authenticated;
GRANT SELECT, INSERT ON public.investigations TO authenticated;

CREATE INDEX IF NOT EXISTS investigations_user_created_idx
  ON public.investigations (user_id, created_at DESC);

-- 2. Realtime channel pattern for live investigation progress.
--    Channels are named investigation:<runId> (runId is a random per-run UUID),
--    so progress feeds are scoped to a single investigation run.
INSERT INTO realtime.channels (pattern, description, enabled)
VALUES ('investigation:%', 'Live investigation progress updates', true)
ON CONFLICT (pattern) DO UPDATE
SET description = EXCLUDED.description,
    enabled = EXCLUDED.enabled;
