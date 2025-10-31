# Premier League Betting Advice Application
# Flask backend with statistical analysis

from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import json
import statistics
from collections import defaultdict
import sqlite3
import os

app = Flask(__name__)

# Database setup
DATABASE = 'premier_league.db'

def get_db():
    """Get database connection"""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    """Initialize database with schema"""
    if not os.path.exists(DATABASE):
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        print("Database initialized!")

class BettingAnalyzer:
    """Statistical analysis engine for betting predictions"""
    
    def __init__(self):
        self.db = get_db()
    
    def get_team_stats(self, team_name, home_away='both', years=10):
        """Get historical statistics for a team"""
        query = """
            SELECT * FROM matches 
            WHERE (home_team = ? OR away_team = ?)
            AND match_date >= date('now', '-{} years')
        """.format(years)
        
        if home_away == 'home':
            query += " AND home_team = ?"
            params = (team_name, team_name, team_name)
        elif home_away == 'away':
            query += " AND away_team = ?"
            params = (team_name, team_name, team_name)
        else:
            params = (team_name, team_name)
        
        cursor = self.db.execute(query, params)
        matches = cursor.fetchall()
        
        return self._calculate_statistics(matches, team_name, home_away)
    
    def _calculate_statistics(self, matches, team_name, home_away):
        """Calculate statistical metrics from match data"""
        if not matches:
            return None
        
        stats = {
            'total_matches': len(matches),
            'goals_first_half': [],
            'goals_second_half': [],
            'total_goals': [],
            'corners_first_half': [],
            'total_corners': [],
        }
        
        for match in matches:
            is_home = match['home_team'] == team_name
            
            if home_away == 'both' or (home_away == 'home' and is_home) or (home_away == 'away' and not is_home):
                if is_home:
                    stats['goals_first_half'].append(match['home_goals_first_half'])
                    stats['goals_second_half'].append(match['home_goals_second_half'])
                    stats['total_goals'].append(match['home_goals_full_time'])
                    stats['corners_first_half'].append(match['home_corners_first_half'])
                    stats['total_corners'].append(match['home_corners_total'])
                else:
                    stats['goals_first_half'].append(match['away_goals_first_half'])
                    stats['goals_second_half'].append(match['away_goals_second_half'])
                    stats['total_goals'].append(match['away_goals_full_time'])
                    stats['corners_first_half'].append(match['away_corners_first_half'])
                    stats['total_corners'].append(match['away_corners_total'])
        
        # Calculate averages and distributions
        return {
            'matches_analyzed': len(stats['goals_first_half']),
            'avg_goals_first_half': round(statistics.mean(stats['goals_first_half']), 2),
            'avg_goals_second_half': round(statistics.mean(stats['goals_second_half']), 2),
            'avg_total_goals': round(statistics.mean(stats['total_goals']), 2),
            'avg_corners_first_half': round(statistics.mean(stats['corners_first_half']), 2),
            'avg_total_corners': round(statistics.mean(stats['total_corners']), 2),
            'goals_distribution': self._get_distribution(stats['total_goals']),
            'corners_distribution': self._get_distribution(stats['total_corners']),
        }
    
    def _get_distribution(self, values):
        """Get probability distribution of values"""
        if not values:
            return {}
        
        total = len(values)
        distribution = defaultdict(int)
        
        for value in values:
            distribution[value] += 1
        
        # Convert to probabilities
        return {k: round(v / total, 3) for k, v in sorted(distribution.items())}
    
    def predict_match(self, home_team, away_team):
        """Generate predictions for a match"""
        home_stats = self.get_team_stats(home_team, 'home')
        away_stats = self.get_team_stats(away_team, 'away')
        
        if not home_stats or not away_stats:
            return None
        
        # Calculate match predictions
        predictions = {
            'home_team': home_team,
            'away_team': away_team,
            'home_stats': home_stats,
            'away_stats': away_stats,
            'predictions': {
                'total_goals': self._predict_total_goals(home_stats, away_stats),
                'first_half_goals': self._predict_first_half_goals(home_stats, away_stats),
                'second_half_goals': self._predict_second_half_goals(home_stats, away_stats),
                'total_corners': self._predict_total_corners(home_stats, away_stats),
                'first_half_corners': self._predict_first_half_corners(home_stats, away_stats),
            }
        }
        
        return predictions
    
    def _predict_total_goals(self, home_stats, away_stats):
        """Predict total goals in match"""
        # Average of home team's home goals and away team's away goals
        expected_home = home_stats['avg_total_goals']
        expected_away = away_stats['avg_total_goals']
        expected_total = expected_home + expected_away
        
        # Generate probability distribution
        probabilities = {}
        for goals in range(0, 8):
            # Simple Poisson-like distribution
            if goals <= expected_total * 0.5:
                prob = 0.05 + (goals / expected_total) * 0.15
            elif goals <= expected_total * 1.5:
                prob = 0.25 - abs(goals - expected_total) * 0.05
            else:
                prob = max(0.02, 0.15 - (goals - expected_total) * 0.03)
            
            probabilities[f"{goals}+ goals"] = {
                'probability': round(prob, 3),
                'decimal_odds': round(1 / prob, 2) if prob > 0 else 0
            }
        
        return probabilities
    
    def _predict_first_half_goals(self, home_stats, away_stats):
        """Predict first half goals"""
        expected = (home_stats['avg_goals_first_half'] + away_stats['avg_goals_first_half']) / 2
        
        probabilities = {}
        for goals in range(0, 5):
            if goals == 0:
                prob = 0.35
            elif goals == 1:
                prob = 0.35
            elif goals == 2:
                prob = 0.20
            else:
                prob = 0.10 / (goals - 1)
            
            probabilities[f"{goals} goals"] = {
                'probability': round(prob, 3),
                'decimal_odds': round(1 / prob, 2)
            }
        
        return probabilities
    
    def _predict_second_half_goals(self, home_stats, away_stats):
        """Predict second half goals"""
        expected = (home_stats['avg_goals_second_half'] + away_stats['avg_goals_second_half']) / 2
        
        probabilities = {}
        for goals in range(0, 6):
            if goals <= 2:
                prob = 0.30 - goals * 0.05
            else:
                prob = max(0.05, 0.20 - (goals - 2) * 0.04)
            
            probabilities[f"{goals} goals"] = {
                'probability': round(prob, 3),
                'decimal_odds': round(1 / prob, 2)
            }
        
        return probabilities
    
    def _predict_total_corners(self, home_stats, away_stats):
        """Predict total corners in match"""
        expected = home_stats['avg_total_corners'] + away_stats['avg_total_corners']
        
        probabilities = {}
        ranges = [(0, 8), (9, 11), (12, 15), (16, 20)]
        probs = [0.15, 0.35, 0.35, 0.15]
        
        for (low, high), prob in zip(ranges, probs):
            probabilities[f"{low}-{high} corners"] = {
                'probability': round(prob, 3),
                'decimal_odds': round(1 / prob, 2)
            }
        
        return probabilities
    
    def _predict_first_half_corners(self, home_stats, away_stats):
        """Predict first half corners"""
        expected = (home_stats['avg_corners_first_half'] + away_stats['avg_corners_first_half']) / 2
        
        probabilities = {}
        ranges = [(0, 3), (4, 5), (6, 8), (9, 12)]
        probs = [0.25, 0.40, 0.25, 0.10]
        
        for (low, high), prob in zip(ranges, probs):
            probabilities[f"{low}-{high} corners"] = {
                'probability': round(prob, 3),
                'decimal_odds': round(1 / prob, 2)
            }
        
        return probabilities

# Routes
@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/fixtures')
def get_fixtures():
    """Get upcoming fixtures"""
    # In production, this would fetch from an API
    # For now, return sample fixtures
    fixtures = [
        {
            'id': 1,
            'date': '2025-11-01',
            'time': '15:00',
            'home_team': 'Manchester City',
            'away_team': 'Arsenal',
            'venue': 'Etihad Stadium'
        },
        {
            'id': 2,
            'date': '2025-11-01',
            'time': '15:00',
            'home_team': 'Liverpool',
            'away_team': 'Chelsea',
            'venue': 'Anfield'
        },
        {
            'id': 3,
            'date': '2025-11-02',
            'time': '16:30',
            'home_team': 'Manchester United',
            'away_team': 'Tottenham',
            'venue': 'Old Trafford'
        },
        {
            'id': 4,
            'date': '2025-11-02',
            'time': '14:00',
            'home_team': 'Newcastle',
            'away_team': 'Brighton',
            'venue': 'St James Park'
        },
    ]
    
    return jsonify(fixtures)

@app.route('/api/predict', methods=['POST'])
def predict():
    """Generate predictions for a match"""
    data = request.json
    home_team = data.get('home_team')
    away_team = data.get('away_team')
    
    if not home_team or not away_team:
        return jsonify({'error': 'Missing team names'}), 400
    
    analyzer = BettingAnalyzer()
    predictions = analyzer.predict_match(home_team, away_team)
    
    if not predictions:
        return jsonify({'error': 'Insufficient data for these teams'}), 404
    
    return jsonify(predictions)

@app.route('/api/team-stats/<team_name>')
def team_stats(team_name):
    """Get detailed team statistics"""
    home_away = request.args.get('type', 'both')
    
    analyzer = BettingAnalyzer()
    stats = analyzer.get_team_stats(team_name, home_away)
    
    if not stats:
        return jsonify({'error': 'Team not found'}), 404
    
    return jsonify(stats)

@app.route('/api/team-summaries')
def team_summaries():
    """Get comprehensive statistics for all teams"""
    db = get_db()
    
    # Get all unique teams
    cursor = db.execute('SELECT DISTINCT name FROM teams ORDER BY name')
    teams = [row['name'] for row in cursor.fetchall()]
    
    summaries = []
    
    for team in teams:
        # Goals scored (home and away)
        cursor = db.execute('''
            SELECT 
                AVG(home_goals_full_time) as avg_home_scored,
                AVG(away_goals_full_time) as avg_away_conceded,
                COUNT(*) as home_matches
            FROM matches 
            WHERE home_team = ? AND match_date >= date('now', '-10 years')
        ''', (team,))
        home_stats = cursor.fetchone()
        
        cursor = db.execute('''
            SELECT 
                AVG(away_goals_full_time) as avg_away_scored,
                AVG(home_goals_full_time) as avg_home_conceded,
                COUNT(*) as away_matches
            FROM matches 
            WHERE away_team = ? AND match_date >= date('now', '-10 years')
        ''', (team,))
        away_stats = cursor.fetchone()
        
        # Corners
        cursor = db.execute('''
            SELECT 
                AVG(home_corners_total) as avg_home_corners,
                AVG(away_corners_total) as avg_away_corners_against
            FROM matches 
            WHERE home_team = ? AND match_date >= date('now', '-10 years')
        ''', (team,))
        home_corners = cursor.fetchone()
        
        cursor = db.execute('''
            SELECT 
                AVG(away_corners_total) as avg_away_corners,
                AVG(home_corners_total) as avg_home_corners_against
            FROM matches 
            WHERE away_team = ? AND match_date >= date('now', '-10 years')
        ''', (team,))
        away_corners = cursor.fetchone()
        
        total_matches = home_stats['home_matches'] + away_stats['away_matches']
        
        if total_matches > 0:
            # Calculate overall averages
            avg_scored = ((home_stats['avg_home_scored'] * home_stats['home_matches']) + 
                         (away_stats['avg_away_scored'] * away_stats['away_matches'])) / total_matches
            
            avg_conceded = ((home_stats['avg_away_conceded'] * home_stats['home_matches']) + 
                           (away_stats['avg_home_conceded'] * away_stats['away_matches'])) / total_matches
            
            avg_corners_for = ((home_corners['avg_home_corners'] * home_stats['home_matches']) + 
                              (away_corners['avg_away_corners'] * away_stats['away_matches'])) / total_matches
            
            avg_corners_against = ((home_corners['avg_away_corners_against'] * home_stats['home_matches']) + 
                                  (away_corners['avg_home_corners_against'] * away_stats['away_matches'])) / total_matches
            
            summaries.append({
                'team': team,
                'matches_played': total_matches,
                'avg_goals_scored': round(avg_scored, 2),
                'avg_goals_conceded': round(avg_conceded, 2),
                'avg_corners_for': round(avg_corners_for, 2),
                'avg_corners_against': round(avg_corners_against, 2),
                'goal_difference': round(avg_scored - avg_conceded, 2)
            })
    
    # Sort by goal difference
    summaries.sort(key=lambda x: x['goal_difference'], reverse=True)
    
    return jsonify(summaries)

@app.route('/api/team-cdf/<team_name>')
def team_cdf(team_name):
    """Get CDF data for goals, corners, and cards for a specific team"""
    db = get_db()
    period = request.args.get('period', 'full')  # 'first_half', 'second_half', 'full'
    years = int(request.args.get('years', 10))  # Number of years to analyze
    
    # Determine which columns to query based on period
    if period == 'first_half':
        goals_scored_col = 'home_goals_first_half'
        goals_conceded_col = 'away_goals_first_half'
        corners_col = 'home_corners_first_half'
    elif period == 'second_half':
        goals_scored_col = 'home_goals_second_half'
        goals_conceded_col = 'away_goals_second_half'
        corners_col = 'home_corners_total - home_corners_first_half'
    else:  # full
        goals_scored_col = 'home_goals_full_time'
        goals_conceded_col = 'away_goals_full_time'
        corners_col = 'home_corners_total'
    
    # Get goals scored distribution (home matches)
    cursor = db.execute(f'''
        SELECT {goals_scored_col} as value, COUNT(*) as frequency
        FROM matches
        WHERE home_team = ? AND match_date >= date('now', '-{years} years')
        GROUP BY value
        ORDER BY value
    ''', (team_name,))
    home_goals_scored = [dict(row) for row in cursor.fetchall()]
    
    # Get goals scored distribution (away matches)
    cursor = db.execute(f'''
        SELECT {goals_conceded_col.replace('home', 'away').replace('away_goals_conceded', 'away_goals')} as value, COUNT(*) as frequency
        FROM matches
        WHERE away_team = ? AND match_date >= date('now', '-{years} years')
        GROUP BY value
        ORDER BY value
    ''', (team_name,))
    away_goals_scored = [dict(row) for row in cursor.fetchall()]
    
    # Get goals conceded distribution (home matches)
    cursor = db.execute(f'''
        SELECT {goals_conceded_col} as value, COUNT(*) as frequency
        FROM matches
        WHERE home_team = ? AND match_date >= date('now', '-{years} years')
        GROUP BY value
        ORDER BY value
    ''', (team_name,))
    home_goals_conceded = [dict(row) for row in cursor.fetchall()]
    
    # Get goals conceded distribution (away matches)
    cursor = db.execute(f'''
        SELECT {goals_scored_col.replace('home', 'away').replace('away_goals_scored', 'home_goals')} as value, COUNT(*) as frequency
        FROM matches
        WHERE away_team = ? AND match_date >= date('now', '-{years} years')
        GROUP BY value
        ORDER BY value
    ''', (team_name,))
    away_goals_conceded = [dict(row) for row in cursor.fetchall()]
    
    # Get corners distribution (home matches)
    cursor = db.execute(f'''
        SELECT {corners_col} as value, COUNT(*) as frequency
        FROM matches
        WHERE home_team = ? AND match_date >= date('now', '-{years} years')
        GROUP BY value
        ORDER BY value
    ''', (team_name,))
    home_corners = [dict(row) for row in cursor.fetchall()]
    
    # Get corners distribution (away matches)
    cursor = db.execute(f'''
        SELECT {corners_col.replace('home', 'away')} as value, COUNT(*) as frequency
        FROM matches
        WHERE away_team = ? AND match_date >= date('now', '-{years} years')
        GROUP BY value
        ORDER BY value
    ''', (team_name,))
    away_corners = [dict(row) for row in cursor.fetchall()]
    
    # Calculate CDFs
    def calculate_cdf(data):
        if not data:
            return []
        total = sum(item['frequency'] for item in data)
        cumulative = 0
        cdf = []
        for item in data:
            cumulative += item['frequency']
            cdf.append({
                'value': item['value'],
                'probability': round(cumulative / total, 4)
            })
        return cdf
    
    # Combine home and away data
    def combine_distributions(home_data, away_data):
        combined = {}
        for item in home_data:
            combined[item['value']] = combined.get(item['value'], 0) + item['frequency']
        for item in away_data:
            combined[item['value']] = combined.get(item['value'], 0) + item['frequency']
        
        result = [{'value': k, 'frequency': v} for k, v in sorted(combined.items())]
        return result
    
    goals_scored_combined = combine_distributions(home_goals_scored, away_goals_scored)
    goals_conceded_combined = combine_distributions(home_goals_conceded, away_goals_conceded)
    corners_combined = combine_distributions(home_corners, away_corners)
    
    return jsonify({
        'team': team_name,
        'period': period,
        'goals_scored_cdf': calculate_cdf(goals_scored_combined),
        'goals_conceded_cdf': calculate_cdf(goals_conceded_combined),
        'corners_cdf': calculate_cdf(corners_combined)
    })

@app.route('/api/data-summary')
def data_summary():
    """Get comprehensive summary of all historical data"""
    db = get_db()
    
    # Overall statistics
    cursor = db.execute('''
        SELECT 
            COUNT(*) as total_matches,
            COUNT(DISTINCT season) as total_seasons,
            MIN(match_date) as earliest_match,
            MAX(match_date) as latest_match,
            AVG(home_goals_full_time + away_goals_full_time) as avg_goals_per_match,
            AVG(home_corners_total + away_corners_total) as avg_corners_per_match
        FROM matches
    ''')
    overall = dict(cursor.fetchone())
    
    # Total unique teams
    cursor = db.execute('SELECT COUNT(DISTINCT name) as total_teams FROM teams')
    overall['total_teams'] = cursor.fetchone()['total_teams']
    
    # Season by season statistics
    cursor = db.execute('''
        SELECT 
            season,
            COUNT(*) as matches,
            AVG(home_goals_full_time + away_goals_full_time) as avg_goals,
            AVG(home_corners_total + away_corners_total) as avg_corners,
            SUM(home_goals_full_time + away_goals_full_time) as total_goals
        FROM matches
        GROUP BY season
        ORDER BY season
    ''')
    seasons = []
    for row in cursor.fetchall():
        seasons.append({
            'season': row['season'],
            'matches': row['matches'],
            'avg_goals': round(row['avg_goals'], 2),
            'avg_corners': round(row['avg_corners'], 2),
            'total_goals': row['total_goals']
        })
    
    # Top scoring teams (all time)
    cursor = db.execute('''
        SELECT 
            team,
            COUNT(*) as matches,
            ROUND(AVG(goals_scored), 2) as avg_goals_scored,
            SUM(goals_scored) as total_goals_scored
        FROM (
            SELECT home_team as team, home_goals_full_time as goals_scored FROM matches
            UNION ALL
            SELECT away_team as team, away_goals_full_time as goals_scored FROM matches
        )
        GROUP BY team
        HAVING COUNT(*) >= 100
        ORDER BY avg_goals_scored DESC
        LIMIT 10
    ''')
    top_scoring = [dict(row) for row in cursor.fetchall()]
    
    # Top defensive teams (all time)
    cursor = db.execute('''
        SELECT 
            team,
            COUNT(*) as matches,
            ROUND(AVG(goals_conceded), 2) as avg_goals_conceded,
            SUM(goals_conceded) as total_goals_conceded
        FROM (
            SELECT home_team as team, away_goals_full_time as goals_conceded FROM matches
            UNION ALL
            SELECT away_team as team, home_goals_full_time as goals_conceded FROM matches
        )
        GROUP BY team
        HAVING COUNT(*) >= 100
        ORDER BY avg_goals_conceded ASC
        LIMIT 10
    ''')
    top_defensive = [dict(row) for row in cursor.fetchall()]
    
    # Goal distribution
    cursor = db.execute('''
        SELECT 
            (home_goals_full_time + away_goals_full_time) as total_goals,
            COUNT(*) as frequency,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM matches), 2) as percentage
        FROM matches
        GROUP BY total_goals
        ORDER BY total_goals
    ''')
    goal_distribution = [dict(row) for row in cursor.fetchall()]
    
    # Home vs Away statistics
    cursor = db.execute('''
        SELECT 
            SUM(CASE WHEN home_goals_full_time > away_goals_full_time THEN 1 ELSE 0 END) as home_wins,
            SUM(CASE WHEN home_goals_full_time = away_goals_full_time THEN 1 ELSE 0 END) as draws,
            SUM(CASE WHEN home_goals_full_time < away_goals_full_time THEN 1 ELSE 0 END) as away_wins,
            AVG(home_goals_full_time) as avg_home_goals,
            AVG(away_goals_full_time) as avg_away_goals,
            AVG(home_corners_total) as avg_home_corners,
            AVG(away_corners_total) as avg_away_corners
        FROM matches
    ''')
    home_away = dict(cursor.fetchone())
    home_away['home_win_percentage'] = round(home_away['home_wins'] * 100 / overall['total_matches'], 2)
    home_away['draw_percentage'] = round(home_away['draws'] * 100 / overall['total_matches'], 2)
    home_away['away_win_percentage'] = round(home_away['away_wins'] * 100 / overall['total_matches'], 2)
    home_away['avg_home_goals'] = round(home_away['avg_home_goals'], 2)
    home_away['avg_away_goals'] = round(home_away['avg_away_goals'], 2)
    home_away['avg_home_corners'] = round(home_away['avg_home_corners'], 2)
    home_away['avg_away_corners'] = round(home_away['avg_away_corners'], 2)
    
    return jsonify({
        'overall': overall,
        'seasons': seasons,
        'top_scoring': top_scoring,
        'top_defensive': top_defensive,
        'goal_distribution': goal_distribution,
        'home_away_stats': home_away
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)

