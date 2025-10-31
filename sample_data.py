"""
Sample data generator for Premier League betting app
Generates realistic historical match data for testing
"""

import sqlite3
import random
from datetime import datetime, timedelta

# Premier League teams
TEAMS = [
    'Manchester City', 'Arsenal', 'Liverpool', 'Manchester United',
    'Chelsea', 'Tottenham', 'Newcastle', 'Brighton',
    'Aston Villa', 'West Ham', 'Crystal Palace', 'Wolves',
    'Fulham', 'Everton', 'Brentford', 'Nottingham Forest',
    'Bournemouth', 'Luton Town', 'Sheffield United', 'Burnley'
]

def generate_match_data():
    """Generate realistic match statistics"""
    # Goals tend to follow certain patterns
    home_advantage = random.choice([True, False, False])  # Home teams win more
    
    if home_advantage:
        home_goals_ht = random.choices([0, 1, 2], weights=[40, 40, 20])[0]
        home_goals_sh = random.choices([0, 1, 2, 3], weights=[30, 40, 20, 10])[0]
        away_goals_ht = random.choices([0, 1], weights=[60, 40])[0]
        away_goals_sh = random.choices([0, 1, 2], weights=[50, 35, 15])[0]
    else:
        home_goals_ht = random.choices([0, 1, 2], weights=[50, 35, 15])[0]
        home_goals_sh = random.choices([0, 1, 2], weights=[40, 40, 20])[0]
        away_goals_ht = random.choices([0, 1, 2], weights=[45, 40, 15])[0]
        away_goals_sh = random.choices([0, 1, 2], weights=[40, 40, 20])[0]
    
    # Corners statistics
    home_corners_ht = random.randint(2, 7)
    home_corners_sh = random.randint(2, 8)
    away_corners_ht = random.randint(2, 6)
    away_corners_sh = random.randint(2, 7)
    
    return {
        'home_goals_ft': home_goals_ht + home_goals_sh,
        'away_goals_ft': away_goals_ht + away_goals_sh,
        'home_goals_ht': home_goals_ht,
        'away_goals_ht': away_goals_ht,
        'home_goals_sh': home_goals_sh,
        'away_goals_sh': away_goals_sh,
        'home_corners_total': home_corners_ht + home_corners_sh,
        'away_corners_total': away_corners_ht + away_corners_sh,
        'home_corners_ht': home_corners_ht,
        'away_corners_ht': away_corners_ht,
    }

def populate_database():
    """Populate database with 10 years of sample data"""
    conn = sqlite3.connect('premier_league.db')
    cursor = conn.cursor()
    
    print("Generating sample match data for 10 years...")
    
    # Generate data for last 10 seasons
    matches_added = 0
    for year in range(2015, 2025):
        season = f"{year}/{year+1}"
        
        # Each season has 38 gameweeks, each team plays 38 matches
        # 20 teams = 380 matches per season
        season_start = datetime(year, 8, 15)
        
        for week in range(38):
            # 10 matches per gameweek
            match_date = season_start + timedelta(weeks=week)
            
            # Shuffle teams for random matchups
            shuffled_teams = TEAMS.copy()
            random.shuffle(shuffled_teams)
            
            # Create 10 matches
            for i in range(0, min(20, len(shuffled_teams)), 2):
                if i + 1 < len(shuffled_teams):
                    home_team = shuffled_teams[i]
                    away_team = shuffled_teams[i + 1]
                    
                    match_data = generate_match_data()
                    
                    cursor.execute('''
                        INSERT INTO matches (
                            match_date, season, home_team, away_team,
                            home_goals_full_time, away_goals_full_time,
                            home_goals_first_half, away_goals_first_half,
                            home_goals_second_half, away_goals_second_half,
                            home_corners_total, away_corners_total,
                            home_corners_first_half, away_corners_first_half,
                            venue
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        match_date.strftime('%Y-%m-%d'),
                        season,
                        home_team,
                        away_team,
                        match_data['home_goals_ft'],
                        match_data['away_goals_ft'],
                        match_data['home_goals_ht'],
                        match_data['away_goals_ht'],
                        match_data['home_goals_sh'],
                        match_data['away_goals_sh'],
                        match_data['home_corners_total'],
                        match_data['away_corners_total'],
                        match_data['home_corners_ht'],
                        match_data['away_corners_ht'],
                        f"{home_team} Stadium"
                    ))
                    
                    matches_added += 1
    
    # Insert teams
    for team in TEAMS:
        cursor.execute('INSERT OR IGNORE INTO teams (name) VALUES (?)', (team,))
    
    # Add upcoming fixtures
    print("Adding upcoming fixtures...")
    next_weekend = datetime.now() + timedelta(days=(5 - datetime.now().weekday()))
    
    fixtures = [
        (next_weekend, '15:00', 'Manchester City', 'Arsenal', 'Etihad Stadium'),
        (next_weekend, '15:00', 'Liverpool', 'Chelsea', 'Anfield'),
        (next_weekend + timedelta(days=1), '16:30', 'Manchester United', 'Tottenham', 'Old Trafford'),
        (next_weekend + timedelta(days=1), '14:00', 'Newcastle', 'Brighton', 'St James Park'),
        (next_weekend, '12:30', 'Aston Villa', 'West Ham', 'Villa Park'),
        (next_weekend + timedelta(days=1), '14:00', 'Wolves', 'Crystal Palace', 'Molineux'),
    ]
    
    for fixture in fixtures:
        cursor.execute('''
            INSERT INTO fixtures (match_date, match_time, home_team, away_team, venue, season, gameweek)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            fixture[0].strftime('%Y-%m-%d'),
            fixture[1],
            fixture[2],
            fixture[3],
            fixture[4],
            '2024/2025',
            10
        ))
    
    conn.commit()
    print(f"✓ Added {matches_added} historical matches")
    print(f"✓ Added {len(TEAMS)} teams")
    print(f"✓ Added {len(fixtures)} upcoming fixtures")
    print("Database populated successfully!")
    
    conn.close()

if __name__ == '__main__':
    populate_database()

