"""
Import ALL Premier League data from football-data.co.uk
Downloads all available seasons and creates comprehensive summary
"""

import sqlite3
import urllib.request
import csv
from io import StringIO
import time

# Generate all season URLs from 1993/94 (Premier League start) to 2025/26
def generate_season_urls():
    """Generate URLs for all Premier League seasons"""
    urls = {}
    
    # Start from 1993 (first Premier League season) to 2025
    for year in range(1993, 2026):
        next_year = year + 1
        
        # Format: 9394 for 1993/94, 2425 for 2024/25
        if year < 2000:
            season_code = f"{str(year)[2:]}{str(next_year)[2:]}"
        else:
            season_code = f"{str(year)[2:]}{str(next_year)[2:]}"
        
        season_name = f"{year}/{next_year}"
        url = f"https://www.football-data.co.uk/mmz4281/{season_code}/E0.csv"
        urls[season_name] = url
    
    return urls

def download_csv(url):
    """Download CSV file from URL"""
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            # Use utf-8-sig to handle BOM character in CSV files
            data = response.read().decode('utf-8-sig')
            return data
    except Exception as e:
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
                    year_int = int(year)
                    if year_int > 50:
                        year = '19' + year
                    else:
                        year = '20' + year
                match_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            else:
                continue
            
            # Full time goals
            home_goals_ft = int(row.get('FTHG', 0) or 0)
            away_goals_ft = int(row.get('FTAG', 0) or 0)
            
            # Half time goals
            home_goals_ht = int(row.get('HTHG', 0) or 0)
            away_goals_ht = int(row.get('HTAG', 0) or 0)
            
            # Calculate second half goals
            home_goals_sh = home_goals_ft - home_goals_ht
            away_goals_sh = away_goals_ft - away_goals_ht
            
            # Corners (total) - may not be available in older seasons
            home_corners = int(row.get('HC', 0) or 0)
            away_corners = int(row.get('AC', 0) or 0)
            
            # Estimate first half corners
            home_corners_ht = int(home_corners * 0.4)
            away_corners_ht = int(away_corners * 0.4)
            
            # Betting odds - Bet365 (most common)
            odds_home_b365 = float(row.get('B365H', 0) or 0) if row.get('B365H') else None
            odds_draw_b365 = float(row.get('B365D', 0) or 0) if row.get('B365D') else None
            odds_away_b365 = float(row.get('B365A', 0) or 0) if row.get('B365A') else None
            
            # Market average odds (if available)
            odds_home_avg = float(row.get('AvgH', row.get('BbAvH', 0)) or 0) if row.get('AvgH') or row.get('BbAvH') else None
            odds_draw_avg = float(row.get('AvgD', row.get('BbAvD', 0)) or 0) if row.get('AvgD') or row.get('BbAvD') else None
            odds_away_avg = float(row.get('AvgA', row.get('BbAvA', 0)) or 0) if row.get('AvgA') or row.get('BbAvA') else None
            
            # Max odds (best available)
            odds_home_max = float(row.get('MaxH', row.get('BbMxH', 0)) or 0) if row.get('MaxH') or row.get('BbMxH') else None
            odds_draw_max = float(row.get('MaxD', row.get('BbMxD', 0)) or 0) if row.get('MaxD') or row.get('BbMxD') else None
            odds_away_max = float(row.get('MaxA', row.get('BbMxA', 0)) or 0) if row.get('MaxA') or row.get('BbMxA') else None
            
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
                # Betting odds
                'odds_home_b365': odds_home_b365,
                'odds_draw_b365': odds_draw_b365,
                'odds_away_b365': odds_away_b365,
                'odds_home_avg': odds_home_avg,
                'odds_draw_avg': odds_draw_avg,
                'odds_away_avg': odds_away_avg,
                'odds_home_max': odds_home_max,
                'odds_draw_max': odds_draw_max,
                'odds_away_max': odds_away_max,
            }
            
            matches.append(match)
            
        except (ValueError, KeyError) as e:
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

def import_all_data():
    """Import ALL Premier League data"""
    conn = sqlite3.connect('premier_league.db')
    cursor = conn.cursor()
    
    season_urls = generate_season_urls()
    total_matches = 0
    teams_set = set()
    successful_seasons = []
    failed_seasons = []
    
    print(f"Attempting to download {len(season_urls)} seasons...\n")
    
    for season, url in sorted(season_urls.items()):
        print(f"Downloading {season}... ", end='', flush=True)
        
        csv_data = download_csv(url)
        if not csv_data:
            print("❌ Not available")
            failed_seasons.append(season)
            continue
        
        matches = parse_csv_data(csv_data)
        if not matches:
            print("❌ No data")
            failed_seasons.append(season)
            continue
        
        # Insert matches
        season_count = 0
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
                        referee, venue,
                        odds_home_b365, odds_draw_b365, odds_away_b365,
                        odds_home_avg, odds_draw_avg, odds_away_avg,
                        odds_home_max, odds_draw_max, odds_away_max
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    f"{match['home_team']} Stadium",
                    match['odds_home_b365'],
                    match['odds_draw_b365'],
                    match['odds_away_b365'],
                    match['odds_home_avg'],
                    match['odds_draw_avg'],
                    match['odds_away_avg'],
                    match['odds_home_max'],
                    match['odds_draw_max'],
                    match['odds_away_max']
                ))
                
                teams_set.add(match['home_team'])
                teams_set.add(match['away_team'])
                season_count += 1
                
            except Exception as e:
                continue
        
        if season_count > 0:
            print(f"✓ {season_count} matches")
            total_matches += season_count
            successful_seasons.append(season)
        else:
            print("❌ Failed to insert")
            failed_seasons.append(season)
        
        conn.commit()
        time.sleep(0.1)  # Be nice to the server
    
    # Insert teams
    for team in sorted(teams_set):
        cursor.execute('INSERT OR IGNORE INTO teams (name) VALUES (?)', (team,))
    
    conn.commit()
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"✓ Successfully imported {total_matches:,} matches")
    print(f"✓ From {len(successful_seasons)} seasons")
    print(f"✓ Found {len(teams_set)} unique teams across all seasons")
    print(f"{'='*60}")
    
    if successful_seasons:
        print(f"\nSeasons imported: {successful_seasons[0]} to {successful_seasons[-1]}")
    
    if failed_seasons:
        print(f"\nFailed/unavailable seasons: {len(failed_seasons)}")
    
    print(f"\nData source: https://www.football-data.co.uk/englandm.php")
    print("\n✓ Import complete!")

if __name__ == '__main__':
    print("="*60)
    print("IMPORTING ALL PREMIER LEAGUE DATA")
    print("="*60)
    print("\nSource: football-data.co.uk")
    print("Timeframe: 1993/94 to 2025/26 (all available seasons)")
    print()
    
    clear_database()
    import_all_data()
    
    print("\n✓ Ready to restart the app with complete historical data!")

