# Database Schema Design

## PostgreSQL Schema for PickEm Pro

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    steam_id VARCHAR(20) UNIQUE NOT NULL,
    username VARCHAR(100) NOT NULL,
    avatar_url TEXT,
    viewer_pass_tokens INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    preferences JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_users_steam_id ON users(steam_id);
CREATE INDEX idx_users_last_login ON users(last_login);
```

### Matches Table
```sql
CREATE TABLE matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(50) UNIQUE NOT NULL,
    team_a VARCHAR(100) NOT NULL,
    team_b VARCHAR(100) NOT NULL,
    team_a_logo_url TEXT,
    team_b_logo_url TEXT,
    stage VARCHAR(20) NOT NULL CHECK (stage IN ('swiss', 'playoffs')),
    round_number INTEGER NOT NULL,
    scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) DEFAULT 'upcoming' CHECK (status IN ('upcoming', 'live', 'completed', 'cancelled')),
    result VARCHAR(10) CHECK (result IN ('team_a', 'team_b', 'draw')),
    is_safe BOOLEAN DEFAULT false,
    confidence_threshold FLOAT DEFAULT 0.75,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_matches_stage ON matches(stage);
CREATE INDEX idx_matches_status ON matches(status);
CREATE INDEX idx_matches_scheduled_time ON matches(scheduled_time);
CREATE INDEX idx_matches_external_id ON matches(external_id);
```

### Odds Table
```sql
CREATE TABLE odds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id UUID NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    source VARCHAR(50) NOT NULL,
    team_a_win_prob FLOAT NOT NULL CHECK (team_a_win_prob >= 0 AND team_a_win_prob <= 1),
    team_b_win_prob FLOAT NOT NULL CHECK (team_b_win_prob >= 0 AND team_b_win_prob <= 1),
    implied_win_rate FLOAT GENERATED ALWAYS AS (GREATEST(team_a_win_prob, team_b_win_prob)) STORED,
    raw_data JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_odds_match_id ON odds(match_id);
CREATE INDEX idx_odds_source ON odds(source);
CREATE INDEX idx_odds_timestamp ON odds(timestamp);
CREATE INDEX idx_odds_implied_win_rate ON odds(implied_win_rate);

-- Constraint to ensure probabilities sum to approximately 1
ALTER TABLE odds ADD CONSTRAINT check_prob_sum 
CHECK (ABS(team_a_win_prob + team_b_win_prob - 1.0) < 0.01);
```

### Picks Table
```sql
CREATE TABLE picks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    match_id UUID NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    selected_team VARCHAR(10) NOT NULL CHECK (selected_team IN ('team_a', 'team_b')),
    confidence FLOAT DEFAULT 0.5 CHECK (confidence >= 0 AND confidence <= 1),
    is_locked BOOLEAN DEFAULT false,
    pick_type VARCHAR(20) DEFAULT 'manual' CHECK (pick_type IN ('manual', 'optimized', 'template')),
    template_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, match_id)
);

CREATE INDEX idx_picks_user_id ON picks(user_id);
CREATE INDEX idx_picks_match_id ON picks(match_id);
CREATE INDEX idx_picks_is_locked ON picks(is_locked);
CREATE INDEX idx_picks_pick_type ON picks(pick_type);
```

### Optimization Jobs Table
```sql
CREATE TABLE optimization_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    safe_picks JSONB NOT NULL DEFAULT '[]',
    unsafe_picks JSONB NOT NULL DEFAULT '[]',
    constraints JSONB NOT NULL DEFAULT '{}',
    result JSONB,
    error_message TEXT,
    execution_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_optimization_jobs_user_id ON optimization_jobs(user_id);
CREATE INDEX idx_optimization_jobs_status ON optimization_jobs(status);
CREATE INDEX idx_optimization_jobs_created_at ON optimization_jobs(created_at);
```

### Templates Table
```sql
CREATE TABLE templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    author_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    picks JSONB NOT NULL DEFAULT '[]',
    performance_stats JSONB DEFAULT '{}',
    is_public BOOLEAN DEFAULT false,
    is_featured BOOLEAN DEFAULT false,
    usage_count INTEGER DEFAULT 0,
    rating FLOAT DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_templates_author_id ON templates(author_id);
CREATE INDEX idx_templates_is_public ON templates(is_public);
CREATE INDEX idx_templates_is_featured ON templates(is_featured);
CREATE INDEX idx_templates_rating ON templates(rating);
CREATE INDEX idx_templates_usage_count ON templates(usage_count);
```

### Results Table
```sql
CREATE TABLE results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    match_id UUID NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    predicted_team VARCHAR(10) NOT NULL,
    actual_result VARCHAR(10),
    is_correct BOOLEAN,
    points_earned INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, match_id)
);

CREATE INDEX idx_results_user_id ON results(user_id);
CREATE INDEX idx_results_match_id ON results(match_id);
CREATE INDEX idx_results_is_correct ON results(is_correct);
```

### User Sessions Table
```sql
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_agent TEXT,
    ip_address INET
);

CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_session_token ON user_sessions(session_token);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);
```

### Audit Log Table
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource_type ON audit_logs(resource_type);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
```

## Views for Common Queries

### Current User Progress View
```sql
CREATE VIEW user_progress AS
SELECT 
    u.id as user_id,
    u.username,
    COUNT(r.id) as total_picks,
    COUNT(CASE WHEN r.is_correct = true THEN 1 END) as correct_picks,
    COUNT(CASE WHEN r.is_correct = false THEN 1 END) as incorrect_picks,
    SUM(r.points_earned) as total_points,
    ROUND(
        COUNT(CASE WHEN r.is_correct = true THEN 1 END)::FLOAT / 
        NULLIF(COUNT(r.id), 0) * 100, 2
    ) as accuracy_percentage
FROM users u
LEFT JOIN results r ON u.id = r.user_id
GROUP BY u.id, u.username;
```

### Latest Odds View
```sql
CREATE VIEW latest_odds AS
SELECT DISTINCT ON (match_id, source)
    match_id,
    source,
    team_a_win_prob,
    team_b_win_prob,
    implied_win_rate,
    timestamp
FROM odds
WHERE is_active = true
ORDER BY match_id, source, timestamp DESC;
```

### Match Summary View
```sql
CREATE VIEW match_summary AS
SELECT 
    m.*,
    lo.team_a_win_prob,
    lo.team_b_win_prob,
    lo.implied_win_rate,
    COUNT(p.id) as total_picks,
    COUNT(CASE WHEN p.selected_team = 'team_a' THEN 1 END) as team_a_picks,
    COUNT(CASE WHEN p.selected_team = 'team_b' THEN 1 END) as team_b_picks
FROM matches m
LEFT JOIN latest_odds lo ON m.id = lo.match_id AND lo.source = 'consensus'
LEFT JOIN picks p ON m.id = p.match_id
GROUP BY m.id, lo.team_a_win_prob, lo.team_b_win_prob, lo.implied_win_rate;
```

## Triggers and Functions

### Update Timestamps
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_matches_updated_at BEFORE UPDATE ON matches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_picks_updated_at BEFORE UPDATE ON picks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_templates_updated_at BEFORE UPDATE ON templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Auto-calculate Results
```sql
CREATE OR REPLACE FUNCTION calculate_pick_result()
RETURNS TRIGGER AS $$
BEGIN
    -- When a match result is updated, calculate all pick results
    IF NEW.result IS NOT NULL AND NEW.result != OLD.result THEN
        UPDATE results 
        SET 
            actual_result = NEW.result,
            is_correct = (predicted_team = NEW.result),
            points_earned = CASE WHEN predicted_team = NEW.result THEN 1 ELSE 0 END
        WHERE match_id = NEW.id;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER calculate_results_on_match_update 
    AFTER UPDATE ON matches
    FOR EACH ROW EXECUTE FUNCTION calculate_pick_result();
```

## Indexes for Performance

### Composite Indexes
```sql
CREATE INDEX idx_picks_user_match ON picks(user_id, match_id);
CREATE INDEX idx_odds_match_timestamp ON odds(match_id, timestamp DESC);
CREATE INDEX idx_results_user_correct ON results(user_id, is_correct);
CREATE INDEX idx_matches_stage_status ON matches(stage, status);
```

### Partial Indexes
```sql
CREATE INDEX idx_active_odds ON odds(match_id, timestamp) WHERE is_active = true;
CREATE INDEX idx_public_templates ON templates(rating DESC, usage_count DESC) WHERE is_public = true;
CREATE INDEX idx_pending_jobs ON optimization_jobs(created_at) WHERE status = 'pending';
```

## Data Retention Policies

### Cleanup Old Sessions
```sql
-- Delete expired sessions (run daily)
DELETE FROM user_sessions WHERE expires_at < NOW() - INTERVAL '7 days';
```

### Archive Old Audit Logs
```sql
-- Archive audit logs older than 1 year
CREATE TABLE audit_logs_archive (LIKE audit_logs INCLUDING ALL);

INSERT INTO audit_logs_archive 
SELECT * FROM audit_logs 
WHERE created_at < NOW() - INTERVAL '1 year';

DELETE FROM audit_logs 
WHERE created_at < NOW() - INTERVAL '1 year';
```

## Initial Data Setup

### Default Constraints
```sql
INSERT INTO optimization_jobs (id, user_id, constraints) VALUES 
('00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', 
 '{"max_3_0": 1, "max_0_3": 1, "advance_picks": 7, "total_picks": 9}');
```

