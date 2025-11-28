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
    
    -- Half time scores (may be NULL for older seasons)
    home_goals_first_half INTEGER DEFAULT 0,
    away_goals_first_half INTEGER DEFAULT 0,
    home_goals_second_half INTEGER DEFAULT 0,
    away_goals_second_half INTEGER DEFAULT 0,
    
    -- Corner statistics (may be NULL for older seasons)
    home_corners_total INTEGER DEFAULT 0,
    away_corners_total INTEGER DEFAULT 0,
    home_corners_first_half INTEGER DEFAULT 0,
    away_corners_first_half INTEGER DEFAULT 0,
    
    -- Additional stats
    venue TEXT,
    attendance INTEGER,
    referee TEXT,
    
    -- Historical Betting Odds (from football-data.co.uk)
    -- Bet365 odds
    odds_home_b365 REAL,
    odds_draw_b365 REAL,
    odds_away_b365 REAL,
    
    -- Market average/closing odds
    odds_home_avg REAL,
    odds_draw_avg REAL,
    odds_away_avg REAL,
    
    -- Max odds available
    odds_home_max REAL,
    odds_draw_max REAL,
    odds_away_max REAL,
    
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

