"""
Import real Premier League data from football-data.co.uk
Downloads CSV files for 2023/24 and 2024/25 seasons
"""

import sqlite3
import urllib.request
import csv
from io import StringIO

# URLs for Premier League data
DATA_URLS = {
    '2023/2024': 'https://www.football-data.co.uk/mmz4281/2324/E0.csv',
    '2024/2025': 'https://www.football-data.co.uk/mmz4281/2425/E0.csv'
}

def download_csv(url):
    """Download CSV file from URL"""
    print(f"Downloading: {url}")
    try:
        with urllib.request.urlopen(url) as response:
            data = response.read().decode('utf-8')
            return data
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None

def parse_csv_data(csv_data):
    """Parse CSV data into match records"""
    matches = []
    csv_file = StringIO(csv_data)
    reader = csv.DictReader(csv_file)
    
    for row in reader:
        try:
            # Skip if essential data is missing
            if not row.get('Date') or not row.get('HomeTeam') or not row.get('AwayTeam'):
                continue
            
            # Parse date (format: DD/MM/YY or DD/MM/YYYY)
            date_parts = row['Date'].split('/')
            if len(date_parts) == 3:
                day, month, year = date_parts
                # Handle 2-digit year
                if len(year) == 2:
                    year = '20' + year
                match_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            else:
                continue
            
            # Full time goals
            home_goals_ft = int(row.get('FTHG', 0))
            away_goals_ft = int(row.get('FTAG', 0))
            
            # Half time goals
            home_goals_ht = int(row.get('HTHG', 0))
            away_goals_ht = int(row.get('HTAG', 0))
            
            # Calculate second half goals
            home_goals_sh = home_goals_ft - home_goals_ht
            away_goals_sh = away_goals_ft - away_goals_ht
            
            # Corners (total)
            home_corners = int(row.get('HC', 0))
            away_corners = int(row.get('AC', 0))
            
            # Estimate first half corners (about 40% of total corners happen in first half)
            # This is an estimation as the CSV doesn't have half-time corner data
            home_corners_ht = int(home_corners * 0.4)
            away_corners_ht = int(away_corners * 0.4)
            
            match = {
                'date': match_date,
                'home_team': row['HomeTeam'],
                'away_team': row['AwayTeam'],
                'home_goals_ft': home_goals_ft,
                'away_goals_ft': away_goals_ft,
                'home_goals_ht': home_goals_ht,
                'away_goals_ht': away_goals_ht,
                'home_goals_sh': home_goals_sh,
                'away_goals_sh': away_goals_sh,
                'home_corners_total': home_corners,
                'away_corners_total': away_corners,
                'home_corners_ht': home_corners_ht,
                'away_corners_ht': away_corners_ht,
                'referee': row.get('Referee', ''),
            }
            
            matches.append(match)
            
        except (ValueError, KeyError) as e:
            # Skip rows with bad data
            continue
    
    return matches

def clear_database():
    """Clear existing match data"""
    conn = sqlite3.connect('premier_league.db')
    cursor = conn.cursor()
    
    print("Clearing old data...")
    cursor.execute('DELETE FROM matches')
    cursor.execute('DELETE FROM fixtures')
    cursor.execute('DELETE FROM teams')
    
    conn.commit()
    conn.close()
    print("✓ Database cleared")

def import_data():
    """Import real Premier League data"""
    conn = sqlite3.connect('premier_league.db')
    cursor = conn.cursor()
    
    total_matches = 0
    teams_set = set()
    
    for season, url in DATA_URLS.items():
        print(f"\nProcessing {season} season...")
        
        # Download CSV
        csv_data = download_csv(url)
        if not csv_data:
            print(f"⚠️ Failed to download {season} data")
            continue
        
        # Parse matches
        matches = parse_csv_data(csv_data)
        print(f"Found {len(matches)} matches")
        
        # Insert matches
        for match in matches:
            try:
                cursor.execute('''
                    INSERT INTO matches (
                        match_date, season, home_team, away_team,
                        home_goals_full_time, away_goals_full_time,
                        home_goals_first_half, away_goals_first_half,
                        home_goals_second_half, away_goals_second_half,
                        home_corners_total, away_corners_total,
                        home_corners_first_half, away_corners_first_half,
                        referee, venue
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    match['date'],
                    season,
                    match['home_team'],
                    match['away_team'],
                    match['home_goals_ft'],
                    match['away_goals_ft'],
                    match['home_goals_ht'],
                    match['away_goals_ht'],
                    match['home_goals_sh'],
                    match['away_goals_sh'],
                    match['home_corners_total'],
                    match['away_corners_total'],
                    match['home_corners_ht'],
                    match['away_corners_ht'],
                    match['referee'],
                    f"{match['home_team']} Stadium"
                ))
                
                teams_set.add(match['home_team'])
                teams_set.add(match['away_team'])
                total_matches += 1
                
            except Exception as e:
                print(f"Error inserting match: {e}")
                continue
        
        print(f"✓ Imported {len(matches)} matches from {season}")
    
    # Insert teams
    for team in sorted(teams_set):
        cursor.execute('INSERT OR IGNORE INTO teams (name) VALUES (?)', (team,))
    
    conn.commit()
    conn.close()
    
    print(f"\n{'='*50}")
    print(f"✓ Successfully imported {total_matches} real matches")
    print(f"✓ Found {len(teams_set)} unique teams")
    print(f"{'='*50}")
    print("\nTeams in database:")
    for team in sorted(teams_set):
        print(f"  - {team}")
    print(f"\nData source: https://www.football-data.co.uk")

if __name__ == '__main__':
    print("="*50)
    print("IMPORTING REAL PREMIER LEAGUE DATA")
    print("="*50)
    print("\nSource: football-data.co.uk")
    print("Seasons: 2023/24 and 2024/25")
    print()
    
    # Clear old fake data
    clear_database()
    
    # Import real data
    import_data()
    
    print("\n✓ Import complete! Restart the app to see real statistics.")

