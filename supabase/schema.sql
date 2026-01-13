-- Supabase Database Setup for A2Z DSA Progress Tracking
-- Run this SQL in your Supabase SQL Editor (Dashboard > SQL Editor)

-- =============================================================================
-- 1. Create the user_progress table
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.user_progress (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    progress JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(user_id)
);

-- =============================================================================
-- 2. Enable Row Level Security (RLS)
-- =============================================================================
ALTER TABLE public.user_progress ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- 3. Create RLS Policies
-- =============================================================================

-- Policy: Users can view only their own progress
CREATE POLICY "Users can view own progress" ON public.user_progress
    FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: Users can insert their own progress
CREATE POLICY "Users can insert own progress" ON public.user_progress
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update only their own progress
CREATE POLICY "Users can update own progress" ON public.user_progress
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Policy: Users can delete only their own progress
CREATE POLICY "Users can delete own progress" ON public.user_progress
    FOR DELETE
    USING (auth.uid() = user_id);

-- =============================================================================
-- 4. Create indexes for better performance
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_user_progress_user_id ON public.user_progress(user_id);

-- =============================================================================
-- 5. Create function to update updated_at timestamp
-- =============================================================================
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = timezone('utc'::text, now());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- 6. Create trigger for auto-updating updated_at
-- =============================================================================
DROP TRIGGER IF EXISTS on_user_progress_updated ON public.user_progress;
CREATE TRIGGER on_user_progress_updated
    BEFORE UPDATE ON public.user_progress
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

-- =============================================================================
-- Done! Your Supabase database is now configured for progress tracking.
-- =============================================================================
