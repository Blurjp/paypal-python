-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Briefings table
CREATE TABLE IF NOT EXISTS briefings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    summary_text TEXT NOT NULL,
    original_content TEXT,
    audio_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),
    source_type VARCHAR(50), -- 'text', 'pdf', 'notion', 'url'
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Listeners table (tracks who listened to what)
CREATE TABLE IF NOT EXISTS listeners (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    briefing_id UUID NOT NULL REFERENCES briefings(id) ON DELETE CASCADE,
    user_id VARCHAR(100) NOT NULL, -- Slack user ID
    user_name VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'listened', 'completed'
    listened_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(briefing_id, user_id)
);

-- Slack channels table (track where briefings are posted)
CREATE TABLE IF NOT EXISTS slack_channels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    channel_id VARCHAR(100) NOT NULL UNIQUE,
    channel_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Briefing posts table (track Slack message IDs for each briefing)
CREATE TABLE IF NOT EXISTS briefing_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    briefing_id UUID NOT NULL REFERENCES briefings(id) ON DELETE CASCADE,
    channel_id VARCHAR(100) NOT NULL,
    message_ts VARCHAR(100) NOT NULL, -- Slack message timestamp
    posted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(briefing_id, channel_id)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_briefings_created_at ON briefings(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_listeners_briefing_id ON listeners(briefing_id);
CREATE INDEX IF NOT EXISTS idx_listeners_user_id ON listeners(user_id);
CREATE INDEX IF NOT EXISTS idx_listeners_status ON listeners(status);
CREATE INDEX IF NOT EXISTS idx_briefing_posts_briefing_id ON briefing_posts(briefing_id);

-- Analytics view: completion stats per briefing
CREATE OR REPLACE VIEW briefing_stats AS
SELECT
    b.id as briefing_id,
    b.title,
    b.created_at,
    COUNT(l.id) as total_recipients,
    COUNT(CASE WHEN l.status = 'listened' OR l.status = 'completed' THEN 1 END) as listeners_count,
    COUNT(CASE WHEN l.status = 'completed' THEN 1 END) as completed_count,
    COUNT(CASE WHEN l.status = 'pending' THEN 1 END) as pending_count,
    ROUND(
        100.0 * COUNT(CASE WHEN l.status = 'completed' THEN 1 END) / NULLIF(COUNT(l.id), 0),
        2
    ) as completion_rate
FROM briefings b
LEFT JOIN listeners l ON b.id = l.briefing_id
GROUP BY b.id, b.title, b.created_at;
