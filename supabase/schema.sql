-- ============================================================
-- Swachh PU Abhiyaan — Supabase Database Schema
-- Run this SQL in the Supabase SQL Editor to create all tables
-- ============================================================

-- ========================
-- 1. PROFILES TABLE (base)
-- ========================
CREATE TABLE IF NOT EXISTS profiles (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    role        TEXT NOT NULL CHECK (role IN ('student', 'worker', 'admin')),
    phone       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index for fast lookup by user_id (auth user → profile)
CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_profiles_role ON profiles(role);

-- ================================
-- 2. STUDENT PROFILES TABLE
-- ================================
CREATE TABLE IF NOT EXISTS student_profiles (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id  UUID NOT NULL UNIQUE REFERENCES profiles(id) ON DELETE CASCADE,
    roll_no     TEXT NOT NULL,
    address     TEXT,
    hostel      TEXT
);

CREATE INDEX IF NOT EXISTS idx_student_profiles_profile_id ON student_profiles(profile_id);

-- ================================
-- 3. WORKER PROFILES TABLE
-- ================================
CREATE TABLE IF NOT EXISTS worker_profiles (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id  UUID NOT NULL UNIQUE REFERENCES profiles(id) ON DELETE CASCADE,
    employee_id TEXT,
    zone        TEXT
);

CREATE INDEX IF NOT EXISTS idx_worker_profiles_profile_id ON worker_profiles(profile_id);

-- ================================
-- 4. TASKS TABLE (core)
-- ================================
CREATE TABLE IF NOT EXISTS tasks (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    photo_url   TEXT NOT NULL,
    latitude    FLOAT8 NOT NULL,
    longitude   FLOAT8 NOT NULL,
    audio_url   TEXT,
    description TEXT NOT NULL,
    profile_id  UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    assigned_to UUID REFERENCES profiles(id) ON DELETE SET NULL,
    status      TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'assigned', 'completed', 'rejected')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tasks_profile_id ON tasks(profile_id);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);

-- ================================
-- 5. AUTO-UPDATE updated_at TRIGGER
-- ================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ================================
-- 6. ROW LEVEL SECURITY (RLS)
-- ================================

-- Enable RLS on all tables
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE worker_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

-- PROFILES: Users can read all profiles, but only update their own
CREATE POLICY "Anyone can read profiles"
    ON profiles FOR SELECT
    USING (true);

CREATE POLICY "Users can update own profile"
    ON profiles FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Service role can insert profiles"
    ON profiles FOR INSERT
    WITH CHECK (true);

-- STUDENT_PROFILES: Linked to profile ownership
CREATE POLICY "Anyone can read student profiles"
    ON student_profiles FOR SELECT
    USING (true);

CREATE POLICY "Service role can insert student profiles"
    ON student_profiles FOR INSERT
    WITH CHECK (true);

CREATE POLICY "Users can update own student profile"
    ON student_profiles FOR UPDATE
    USING (
        profile_id IN (
            SELECT id FROM profiles WHERE user_id = auth.uid()
        )
    );

-- WORKER_PROFILES: Linked to profile ownership
CREATE POLICY "Anyone can read worker profiles"
    ON worker_profiles FOR SELECT
    USING (true);

CREATE POLICY "Service role can insert worker profiles"
    ON worker_profiles FOR INSERT
    WITH CHECK (true);

CREATE POLICY "Users can update own worker profile"
    ON worker_profiles FOR UPDATE
    USING (
        profile_id IN (
            SELECT id FROM profiles WHERE user_id = auth.uid()
        )
    );

-- TASKS: Students can read own tasks, workers can read assigned tasks, admins can read all
CREATE POLICY "Users can read own created tasks"
    ON tasks FOR SELECT
    USING (
        auth.uid() IN (
            SELECT user_id FROM profiles WHERE id = tasks.profile_id
        )
    );

CREATE POLICY "Workers can read assigned tasks"
    ON tasks FOR SELECT
    USING (
        auth.uid() IN (
            SELECT user_id FROM profiles WHERE id = tasks.assigned_to
        )
    );

CREATE POLICY "Admins can read all tasks"
    ON tasks FOR SELECT
    USING (
        auth.uid() IN (
            SELECT user_id FROM profiles WHERE role = 'admin'
        )
    );

CREATE POLICY "Authenticated users can create tasks"
    ON tasks FOR INSERT
    WITH CHECK (true);

CREATE POLICY "Admins can update any task"
    ON tasks FOR UPDATE
    USING (
        auth.uid() IN (
            SELECT user_id FROM profiles WHERE role = 'admin'
        )
    );

CREATE POLICY "Workers can update assigned tasks"
    ON tasks FOR UPDATE
    USING (
        auth.uid() IN (
            SELECT user_id FROM profiles WHERE id = tasks.assigned_to
        )
    );

-- ================================
-- 7. STORAGE BUCKETS
-- ================================
-- Run these in Supabase SQL Editor or create via Dashboard → Storage

INSERT INTO storage.buckets (id, name, public)
VALUES ('task-photos', 'task-photos', true)
ON CONFLICT (id) DO NOTHING;

INSERT INTO storage.buckets (id, name, public)
VALUES ('task-audio', 'task-audio', true)
ON CONFLICT (id) DO NOTHING;

-- Storage policies: authenticated users can upload
CREATE POLICY "Authenticated users can upload photos"
    ON storage.objects FOR INSERT
    WITH CHECK (
        bucket_id = 'task-photos'
        AND auth.role() = 'authenticated'
    );

CREATE POLICY "Anyone can view photos"
    ON storage.objects FOR SELECT
    USING (bucket_id = 'task-photos');

CREATE POLICY "Authenticated users can upload audio"
    ON storage.objects FOR INSERT
    WITH CHECK (
        bucket_id = 'task-audio'
        AND auth.role() = 'authenticated'
    );

CREATE POLICY "Anyone can view audio"
    ON storage.objects FOR SELECT
    USING (bucket_id = 'task-audio');
