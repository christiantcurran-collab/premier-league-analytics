-- Premier League Historical Match Data Schema

CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_date DATE NOT NULL,
    season TEXT NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    
    -- Full time scores
    home_goals_full_time INTEGER NOT NULL,
    away_goals_full_time INTEGER NOT NULL,
    
    -- Half time scores
    home_goals_first_half INTEGER NOT NULL,
    away_goals_first_half INTEGER NOT NULL,
    home_goals_second_half INTEGER NOT NULL,
    away_goals_second_half INTEGER NOT NULL,
    
    -- Corner statistics
    home_corners_total INTEGER NOT NULL,
    away_corners_total INTEGER NOT NULL,
    home_corners_first_half INTEGER NOT NULL,
    away_corners_first_half INTEGER NOT NULL,
    
    -- Additional stats
    venue TEXT,
    attendance INTEGER,
    referee TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_home_team ON matches(home_team);
CREATE INDEX IF NOT EXISTS idx_away_team ON matches(away_team);
CREATE INDEX IF NOT EXISTS idx_match_date ON matches(match_date);
CREATE INDEX IF NOT EXISTS idx_season ON matches(season);

-- Teams table
CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    stadium TEXT,
    city TEXT,
    founded INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fixtures table
CREATE TABLE IF NOT EXISTS fixtures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_date DATE NOT NULL,
    match_time TIME,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    venue TEXT,
    gameweek INTEGER,
    season TEXT NOT NULL,
    status TEXT DEFAULT 'scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fixture_date ON fixtures(match_date);
CREATE INDEX IF NOT EXISTS idx_fixture_status ON fixtures(status);

