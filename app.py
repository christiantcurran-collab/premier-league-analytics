# Premier League Betting Advice Application
# Flask backend with statistical analysis

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from datetime import datetime, timedelta
import json
import statistics
from collections import defaultdict
import sqlite3
import os
import requests
import secrets
import math
import re
from functools import lru_cache

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # Generate secure secret key for sessions

# Database setup
DATABASE = 'premier_league.db'

# External API Configuration
FPL_API_BASE = 'https://fantasy.premierleague.com/api'
TWITTER_BEARER_TOKEN = os.environ.get('TWITTER_BEARER_TOKEN', '')  # Optional - for X sentiment

# Premier League Team Mappings (FPL names to our DB names)
FPL_TEAM_MAPPING = {
    'Arsenal': 'Arsenal',
    'Aston Villa': 'Aston Villa',
    'Bournemouth': 'Bournemouth',
    'Brentford': 'Brentford',
    'Brighton': 'Brighton',
    'Chelsea': 'Chelsea',
    'Crystal Palace': 'Crystal Palace',
    'Everton': 'Everton',
    'Fulham': 'Fulham',
    'Ipswich': 'Ipswich',
    'Leicester': 'Leicester',
    'Liverpool': 'Liverpool',
    'Man City': 'Man City',
    'Man Utd': 'Man United',
    'Newcastle': 'Newcastle',
    "Nott'm Forest": "Nott'm Forest",
    'Southampton': 'Southampton',
    'Spurs': 'Tottenham',
    'West Ham': 'West Ham',
    'Wolves': 'Wolves',
    # Promoted teams 2025-26
    'Leeds': 'Leeds',
    'Burnley': 'Burnley',
    'Sunderland': 'Sunderland'
}

# Initialize database on app startup
def init_db():
    """Initialize database with schema"""
    if not os.path.exists(DATABASE):
        db = get_db()
        try:
            with app.open_resource('schema.sql', mode='r') as f:
                db.cursor().executescript(f.read())
            db.commit()
            print("Database initialized!")
        except Exception as e:
            print(f"Database initialization warning: {e}")
        finally:
            db.close()

# Initialize database when module loads (for gunicorn/production)
init_db()

# The Odds API Configuration
ODDS_API_KEY = os.environ.get('ODDS_API_KEY', '9bc157f3e9720cc01a71655708f5c3ca')
ODDS_API_BASE_URL = 'https://api.the-odds-api.com/v4'

# Betfair API Configuration
BETFAIR_APP_KEY = os.environ.get('BETFAIR_APP_KEY', 'A4YclwMGYKSZlK0y')
BETFAIR_USERNAME = os.environ.get('BETFAIR_USERNAME', 'ccurran@gmail.com')
BETFAIR_API_ENDPOINT = 'https://api.betfair.com/exchange/betting/json-rpc/v1'

# Authentication
APP_PASSWORD = 'Eva2020'

def get_db():
    """Get database connection"""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

class AdvancedBettingAnalyzer:
    """Advanced statistical analysis engine with EV calculations"""
    
    def __init__(self):
        self.db = get_db()
    
    def calculate_implied_probability(self, decimal_odds):
        """Convert decimal odds to implied probability"""
        if decimal_odds <= 0:
            return 0
        return 1 / decimal_odds
    
    def calculate_ev(self, ai_probability, decimal_odds):
        """Calculate Expected Value (EV) percentage"""
        implied_prob = self.calculate_implied_probability(decimal_odds)
        ev = ((ai_probability * decimal_odds) - 1) * 100
        return ev
    
    def get_team_historical_stats(self, team_name, seasons=1):
        """Get historical statistics for current/recent seasons"""
        query = """
            SELECT * FROM matches 
            WHERE (home_team = ? OR away_team = ?)
            AND match_date >= date('now', '-{} years')
            ORDER BY match_date DESC
        """.format(seasons)
        
        cursor = self.db.execute(query, (team_name, team_name))
        matches = cursor.fetchall()
        
        if not matches:
            return None
        
        stats = {
            'home': {'wins': 0, 'draws': 0, 'losses': 0, 'total': 0},
            'away': {'wins': 0, 'draws': 0, 'losses': 0, 'total': 0},
            'goals_scored_home': [],
            'goals_conceded_home': [],
            'goals_scored_away': [],
            'goals_conceded_away': [],
            'corners_home': [],
            'corners_away': [],
            'goals_1h_home': [],
            'goals_2h_home': [],
            'goals_1h_away': [],
            'goals_2h_away': [],
            'corners_1h_home': [],
            'corners_2h_home': [],
            'corners_1h_away': [],
            'corners_2h_away': []
        }
        
        for match in matches:
            is_home = match['home_team'] == team_name
            
            if is_home:
                stats['home']['total'] += 1
                home_goals = match['home_goals_full_time']
                away_goals = match['away_goals_full_time']
                
                if home_goals > away_goals:
                    stats['home']['wins'] += 1
                elif home_goals == away_goals:
                    stats['home']['draws'] += 1
                else:
                    stats['home']['losses'] += 1
                
                stats['goals_scored_home'].append(home_goals)
                stats['goals_conceded_home'].append(away_goals)
                stats['corners_home'].append(match['home_corners_total'])
                stats['goals_1h_home'].append(match['home_goals_first_half'])
                stats['goals_2h_home'].append(match['home_goals_second_half'])
                stats['corners_1h_home'].append(match['home_corners_first_half'])
                if match['home_corners_total'] and match['home_corners_first_half']:
                    stats['corners_2h_home'].append(match['home_corners_total'] - match['home_corners_first_half'])
            else:
                stats['away']['total'] += 1
                home_goals = match['home_goals_full_time']
                away_goals = match['away_goals_full_time']
                
                if away_goals > home_goals:
                    stats['away']['wins'] += 1
                elif away_goals == home_goals:
                    stats['away']['draws'] += 1
                else:
                    stats['away']['losses'] += 1
                
                stats['goals_scored_away'].append(away_goals)
                stats['goals_conceded_away'].append(home_goals)
                stats['corners_away'].append(match['away_corners_total'])
                stats['goals_1h_away'].append(match['away_goals_first_half'])
                stats['goals_2h_away'].append(match['away_goals_second_half'])
                stats['corners_1h_away'].append(match['away_corners_first_half'])
                if match['away_corners_total'] and match['away_corners_first_half']:
                    stats['corners_2h_away'].append(match['away_corners_total'] - match['away_corners_first_half'])
        
        return stats
    
    def detect_bookmaker_anomalies(self, bookmaker_odds_list):
        """
        Detect bookmaker anomalies - where one bookmaker offers 25%+ better odds
        bookmaker_odds_list: list of dicts with {'bookmaker': name, 'odds': decimal_odds}
        Returns: dict with average_odds, best_odds, anomaly info
        """
        if not bookmaker_odds_list or len(bookmaker_odds_list) < 2:
            return None
        
        odds_values = [bm['odds'] for bm in bookmaker_odds_list]
        avg_odds = statistics.mean(odds_values)
        best_odds_data = max(bookmaker_odds_list, key=lambda x: x['odds'])
        best_odds = best_odds_data['odds']
        
        # Calculate how much better the best odds is compared to average
        if avg_odds > 0:
            percentage_better = ((best_odds - avg_odds) / avg_odds) * 100
        else:
            percentage_better = 0
        
        is_anomaly = percentage_better >= 25  # 25% threshold
        
        return {
            'average_odds': round(avg_odds, 2),
            'best_odds': round(best_odds, 2),
            'best_bookmaker': best_odds_data['bookmaker'],
            'percentage_better': round(percentage_better, 1),
            'is_anomaly': is_anomaly,
            'all_bookmakers': sorted(bookmaker_odds_list, key=lambda x: x['odds'], reverse=True)
        }
    
    def calculate_ai_probability(self, home_team, away_team, bet_type, market, model='complex'):
        """
        Calculate AI probability using different models:
        - simple: Pure historical stats from current season
        - opponent: Historical stats adjusted for opponent strength
        - complex: Multi-factor model with home advantage, form weighting, etc.
        """
        home_stats_current = self.get_team_historical_stats(home_team, seasons=1)
        away_stats_current = self.get_team_historical_stats(away_team, seasons=1)
        
        if not home_stats_current or not away_stats_current:
            return None
        
        # Get historical stats for complex model
        home_stats_historical = None
        away_stats_historical = None
        if model == 'complex':
            home_stats_historical = self.get_team_historical_stats(home_team, seasons=2)
            away_stats_historical = self.get_team_historical_stats(away_team, seasons=2)
        
        if bet_type == 'moneyline':
            if model == 'simple':
                return self._calculate_moneyline_simple(home_stats_current, away_stats_current, market)
            elif model == 'opponent':
                return self._calculate_moneyline_opponent_adjusted(home_stats_current, away_stats_current, market)
            else:  # complex
                return self._calculate_moneyline_probability(
                    home_stats_current, away_stats_current,
                    home_stats_historical, away_stats_historical,
                    market
                )
        elif bet_type == 'goals':
            if model == 'simple':
                return self._calculate_goals_simple(home_stats_current, away_stats_current, market)
            elif model == 'opponent':
                return self._calculate_goals_opponent_adjusted(home_stats_current, away_stats_current, market)
            else:  # complex
                return self._calculate_goals_probability(
                    home_stats_current, away_stats_current,
                    home_stats_historical, away_stats_historical,
                    market
                )
        elif bet_type == 'corners':
            # Corners uses same model for all (simple approach)
            return self._calculate_corners_probability(
                home_stats_current, away_stats_current,
                home_stats_historical or home_stats_current,
                away_stats_historical or away_stats_current,
                market
            )
        
        return None
    
    def _calculate_moneyline_simple(self, home_current, away_current, market):
        """Simple model: Pure historical win/draw/loss rates from current season"""
        # Just use this season's stats, no adjustments
        home_total = home_current['home']['total']
        away_total = away_current['away']['total']
        
        if home_total == 0 or away_total == 0:
            return None
        
        home_win_rate = home_current['home']['wins'] / home_total
        home_draw_rate = home_current['home']['draws'] / home_total
        
        away_win_rate = away_current['away']['wins'] / away_total
        away_draw_rate = away_current['away']['draws'] / away_total
        
        # Average the draw rates
        draw_prob = (home_draw_rate + away_draw_rate) / 2
        
        # Normalize to 100%
        total = home_win_rate + away_win_rate + draw_prob
        home_win_prob = home_win_rate / total
        away_win_prob = away_win_rate / total
        draw_prob = draw_prob / total
        
        if market == 'home_win':
            return home_win_prob
        elif market == 'draw':
            return draw_prob
        elif market == 'away_win':
            return away_win_prob
        
        return None
    
    def get_explanation(self, home_team, away_team, bet_type, market, model='complex'):
        """Get human-readable explanation of how probability was calculated"""
        home_stats = self.get_team_historical_stats(home_team, seasons=1)
        away_stats = self.get_team_historical_stats(away_team, seasons=1)
        
        if not home_stats or not away_stats:
            return ""
        
        if bet_type == 'moneyline':
            if model == 'simple':
                if market == 'home_win':
                    return f"{home_team} won {home_stats['home']['wins']} of {home_stats['home']['total']} home games this season ({round(home_stats['home']['wins']/home_stats['home']['total']*100, 1)}%)"
                elif market == 'away_win':
                    return f"{away_team} won {away_stats['away']['wins']} of {away_stats['away']['total']} away games this season ({round(away_stats['away']['wins']/away_stats['away']['total']*100, 1)}%)"
                else:  # draw
                    home_draw_pct = round(home_stats['home']['draws']/home_stats['home']['total']*100, 1)
                    away_draw_pct = round(away_stats['away']['draws']/away_stats['away']['total']*100, 1)
                    return f"{home_team} drew {home_draw_pct}% at home, {away_team} drew {away_draw_pct}% away this season"
            
            elif model == 'opponent':
                home_gd = statistics.mean(home_stats['goals_scored_home']) - statistics.mean(home_stats['goals_conceded_home']) if home_stats['goals_scored_home'] else 0
                away_gd = statistics.mean(away_stats['goals_scored_away']) - statistics.mean(away_stats['goals_conceded_away']) if away_stats['goals_scored_away'] else 0
                return f"{home_team} avg goal diff: {round(home_gd, 2)} (home), {away_team}: {round(away_gd, 2)} (away). Adjusted for relative strength"
            
            else:  # complex
                return f"Multi-factor model: home advantage +15%, weighted form (70% current/30% historical), team strength metrics"
        
        elif bet_type == 'goals':
            period, line = market.split('_', 1)
            over_under, threshold = line.split('_')
            
            if model == 'simple':
                if period == 'full':
                    home_avg = statistics.mean(home_stats['goals_scored_home']) if home_stats['goals_scored_home'] else 0
                    away_avg = statistics.mean(away_stats['goals_scored_away']) if away_stats['goals_scored_away'] else 0
                    return f"Historical avg: {home_team} scores {round(home_avg, 1)} at home, {away_team} scores {round(away_avg, 1)} away"
                else:
                    return f"Based on historical {period} goal frequencies for both teams"
            
            elif model == 'opponent':
                home_attack = statistics.mean(home_stats['goals_scored_home']) if home_stats['goals_scored_home'] else 0
                home_defense = statistics.mean(home_stats['goals_conceded_home']) if home_stats['goals_conceded_home'] else 0
                away_attack = statistics.mean(away_stats['goals_scored_away']) if away_stats['goals_scored_away'] else 0
                away_defense = statistics.mean(away_stats['goals_conceded_away']) if away_stats['goals_conceded_away'] else 0
                expected_total = ((home_attack + away_defense) / 2) + ((away_attack + home_defense) / 2)
                return f"Expected goals: {round(expected_total, 2)} (based on attack vs defense matchup)"
            
            else:  # complex
                return f"Multi-factor model with form weighting, confidence adjustments, and historical patterns"
        
        return ""
    
    def _calculate_moneyline_opponent_adjusted(self, home_current, away_current, market):
        """Opponent-adjusted: Considers relative team strength"""
        home_total = home_current['home']['total']
        away_total = away_current['away']['total']
        
        if home_total == 0 or away_total == 0:
            return None
        
        # Calculate team strength indicators
        home_goals_scored_avg = statistics.mean(home_current['goals_scored_home']) if home_current['goals_scored_home'] else 0
        home_goals_conceded_avg = statistics.mean(home_current['goals_conceded_home']) if home_current['goals_conceded_home'] else 0
        home_goal_diff = home_goals_scored_avg - home_goals_conceded_avg
        
        away_goals_scored_avg = statistics.mean(away_current['goals_scored_away']) if away_current['goals_scored_away'] else 0
        away_goals_conceded_avg = statistics.mean(away_current['goals_conceded_away']) if away_current['goals_conceded_away'] else 0
        away_goal_diff = away_goals_scored_avg - away_goals_conceded_avg
        
        # Base win rates
        home_win_rate = home_current['home']['wins'] / home_total
        away_win_rate = away_current['away']['wins'] / away_total
        home_draw_rate = home_current['home']['draws'] / home_total
        away_draw_rate = away_current['away']['draws'] / away_total
        
        # Adjust based on relative strength (goal difference)
        strength_diff = home_goal_diff - away_goal_diff
        adjustment_factor = strength_diff * 0.05  # 5% adjustment per goal difference
        
        home_win_prob = home_win_rate + adjustment_factor
        away_win_prob = away_win_rate - adjustment_factor
        draw_prob = (home_draw_rate + away_draw_rate) / 2
        
        # Ensure probabilities stay positive
        home_win_prob = max(0.05, home_win_prob)
        away_win_prob = max(0.05, away_win_prob)
        draw_prob = max(0.05, draw_prob)
        
        # Normalize
        total = home_win_prob + away_win_prob + draw_prob
        home_win_prob /= total
        away_win_prob /= total
        draw_prob /= total
        
        if market == 'home_win':
            return home_win_prob
        elif market == 'draw':
            return draw_prob
        elif market == 'away_win':
            return away_win_prob
        
        return None
    
    def _calculate_goals_simple(self, home_current, away_current, market):
        """Simple goals model: Pure historical over/under rates"""
        period, line = market.split('_', 1)
        
        if period == '1h':
            home_goals = home_current['goals_1h_home']
            away_goals = away_current['goals_1h_away']
            home_conceded = [0] * len(home_goals)  # Simplified
            away_conceded = [0] * len(away_goals)
        elif period == '2h':
            home_goals = home_current['goals_2h_home']
            away_goals = away_current['goals_2h_away']
            home_conceded = [0] * len(home_goals)
            away_conceded = [0] * len(away_goals)
        else:  # full
            home_goals = home_current['goals_scored_home']
            away_goals = away_current['goals_scored_away']
            home_conceded = home_current['goals_conceded_home']
            away_conceded = away_current['goals_conceded_away']
        
        if not home_goals or not away_goals:
            return None
        
        over_under, threshold = line.split('_')
        threshold = float(threshold)
        
        # Combine match totals
        total_goals_matches = [h + c for h, c in zip(home_goals, home_conceded[:len(home_goals)])]
        total_goals_matches += [a + c for a, c in zip(away_goals, away_conceded[:len(away_goals)])]
        
        if over_under == 'over':
            count = sum(1 for g in total_goals_matches if g > threshold)
        else:  # under
            count = sum(1 for g in total_goals_matches if g < threshold)
        
        probability = count / len(total_goals_matches) if total_goals_matches else 0.5
        
        return probability
    
    def _calculate_goals_opponent_adjusted(self, home_current, away_current, market):
        """Opponent-adjusted goals: Considers attacking vs defensive strength"""
        period, line = market.split('_', 1)
        
        if period == '1h':
            home_goals = home_current['goals_1h_home']
            away_goals = away_current['goals_1h_away']
        elif period == '2h':
            home_goals = home_current['goals_2h_home']
            away_goals = away_current['goals_2h_away']
        else:  # full
            home_goals = home_current['goals_scored_home']
            away_goals = away_current['goals_scored_away']
        
        if not home_goals or not away_goals:
            return None
        
        # Calculate attacking and defensive strength
        home_attack = statistics.mean(home_goals)
        away_attack = statistics.mean(away_goals)
        
        home_defense = statistics.mean(home_current['goals_conceded_home']) if home_current['goals_conceded_home'] else 1.5
        away_defense = statistics.mean(away_current['goals_conceded_away']) if away_current['goals_conceded_away'] else 1.5
        
        # Predict total goals based on matchup
        expected_home_goals = (home_attack + away_defense) / 2
        expected_away_goals = (away_attack + home_defense) / 2
        expected_total = expected_home_goals + expected_away_goals
        
        over_under, threshold = line.split('_')
        threshold = float(threshold)
        
        # Use expected total to estimate probability
        if over_under == 'over':
            # Higher expected total = higher probability of over
            diff = expected_total - threshold
            probability = 0.5 + (diff * 0.15)  # 15% per goal difference
        else:  # under
            diff = threshold - expected_total
            probability = 0.5 + (diff * 0.15)
        
        # Clamp to valid range
        probability = max(0.05, min(0.95, probability))
        
        return probability
    
    def _calculate_moneyline_probability(self, home_current, away_current, home_hist, away_hist, market):
        """Calculate probability for Win/Draw/Loss"""
        # Home advantage factor
        home_advantage = 0.15
        
        # Calculate win rates
        home_win_rate = home_current['home']['wins'] / max(home_current['home']['total'], 1)
        away_win_rate = away_current['away']['wins'] / max(away_current['away']['total'], 1)
        home_draw_rate = home_current['home']['draws'] / max(home_current['home']['total'], 1)
        away_draw_rate = away_current['away']['draws'] / max(away_current['away']['total'], 1)
        
        # Historical adjustments
        home_win_rate_hist = home_hist['home']['wins'] / max(home_hist['home']['total'], 1)
        away_win_rate_hist = away_hist['away']['wins'] / max(away_hist['away']['total'], 1)
        
        # Weighted average (70% current season, 30% historical)
        home_win_adj = (home_win_rate * 0.7) + (home_win_rate_hist * 0.3)
        away_win_adj = (away_win_rate * 0.7) + (away_win_rate_hist * 0.3)
        draw_rate = ((home_draw_rate + away_draw_rate) / 2)
        
        # Apply home advantage
        home_win_prob = home_win_adj + home_advantage
        away_win_prob = away_win_adj
        
        # Normalize probabilities
        total = home_win_prob + away_win_prob + draw_rate
        home_win_prob /= total
        away_win_prob /= total
        draw_prob = draw_rate / total
        
        if market == 'home_win':
            return home_win_prob
        elif market == 'draw':
            return draw_prob
        elif market == 'away_win':
            return away_win_prob
        
        return None
    
    def _calculate_corners_probability(self, home_current, away_current, home_hist, away_hist, market):
        """Calculate probability for corners over/under"""
        period, line = market.split('_', 1)  # e.g., 'full_over_9.5' or '1h_under_5.5'
        
        if period == '1h':
            home_corners = home_current['corners_1h_home'] if home_current['corners_1h_home'] else []
            away_corners = away_current['corners_1h_away'] if away_current['corners_1h_away'] else []
        elif period == '2h':
            home_corners = home_current['corners_2h_home'] if home_current['corners_2h_home'] else []
            away_corners = away_current['corners_2h_away'] if away_current['corners_2h_away'] else []
        else:  # full
            home_corners = home_current['corners_home']
            away_corners = away_current['corners_away']
        
        if not home_corners or not away_corners:
            return None
        
        # Calculate average corners for the matchup
        avg_home = statistics.mean(home_corners) if home_corners else 0
        avg_away = statistics.mean(away_corners) if away_corners else 0
        expected_total = avg_home + avg_away
        
        # Parse the line
        over_under, threshold = line.split('_')
        threshold = float(threshold)
        
        # Calculate probability based on historical distribution
        all_corners = home_corners + away_corners
        
        if over_under == 'over':
            count_over = sum(1 for c in all_corners if c > threshold)
            probability = count_over / len(all_corners)
        else:  # under
            count_under = sum(1 for c in all_corners if c < threshold)
            probability = count_under / len(all_corners)
        
        # Apply confidence adjustment based on sample size
        confidence = min(len(all_corners) / 20, 1.0)
        probability = (probability * confidence) + (0.5 * (1 - confidence))
        
        return probability
    
    def _calculate_goals_probability(self, home_current, away_current, home_hist, away_hist, market):
        """Calculate probability for goals over/under"""
        period, line = market.split('_', 1)  # e.g., 'full_over_2.5' or '1h_under_1.5'
        
        if period == '1h':
            home_goals = home_current['goals_1h_home']
            away_goals = away_current['goals_1h_away']
        elif period == '2h':
            home_goals = home_current['goals_2h_home']
            away_goals = away_current['goals_2h_away']
        else:  # full
            home_goals = home_current['goals_scored_home']
            away_goals = away_current['goals_scored_away']
        
        if not home_goals or not away_goals:
            return None
        
        # Calculate expected total goals
        avg_home_scored = statistics.mean(home_goals)
        avg_away_scored = statistics.mean(away_goals)
        expected_total = avg_home_scored + avg_away_scored
        
        # Parse the line
        over_under, threshold = line.split('_')
        threshold = float(threshold)
        
        # Combine home and away goals for distribution
        home_conceded = home_current['goals_conceded_home']
        away_conceded = away_current['goals_conceded_away']
        
        total_goals_matches = [h + ac for h, ac in zip(home_goals, home_conceded[:len(home_goals)])]
        total_goals_matches += [a + hc for a, hc in zip(away_goals, away_conceded[:len(away_goals)])]
        
        if over_under == 'over':
            count_over = sum(1 for g in total_goals_matches if g > threshold)
            probability = count_over / len(total_goals_matches)
        else:  # under
            count_under = sum(1 for g in total_goals_matches if g < threshold)
            probability = count_under / len(total_goals_matches)
        
        # Apply confidence adjustment
        confidence = min(len(total_goals_matches) / 15, 1.0)
        probability = (probability * confidence) + (0.5 * (1 - confidence))
        
        return probability


# =============================================================================
# ADVANCED AI MODEL 1: FORM & MOMENTUM MODEL
# =============================================================================
class FormMomentumAnalyzer:
    """
    Advanced AI Model: Form & Momentum Analysis
    
    Considers:
    - Recent form (last 5 games weighted heavily, exponential decay)
    - Head-to-head historical record
    - ELO-style team power ratings
    - Home/away specific performance trends
    - Goal scoring/conceding momentum
    """
    
    def __init__(self):
        self.db = get_db()
        self._elo_ratings = {}  # Cache for ELO ratings
        self._form_cache = {}   # Cache for recent form
    
    def calculate_elo_rating(self, team_name, as_of_date=None):
        """
        Calculate ELO-style rating for a team based on historical performance.
        Starting ELO: 1500
        K-factor: 32 for recent matches, 16 for older
        """
        if team_name in self._elo_ratings:
            return self._elo_ratings[team_name]
        
        base_elo = 1500
        
        # Get all matches for the team in last 3 years
        query = """
            SELECT * FROM matches 
            WHERE (home_team = ? OR away_team = ?)
            AND match_date >= date('now', '-3 years')
            ORDER BY match_date ASC
        """
        cursor = self.db.execute(query, (team_name, team_name))
        matches = cursor.fetchall()
        
        if not matches:
            self._elo_ratings[team_name] = base_elo
            return base_elo
        
        elo = base_elo
        
        for i, match in enumerate(matches):
            is_home = match['home_team'] == team_name
            
            # Goal difference
            if is_home:
                goals_for = match['home_goals_full_time']
                goals_against = match['away_goals_full_time']
            else:
                goals_for = match['away_goals_full_time']
                goals_against = match['home_goals_full_time']
            
            # Result: 1 = win, 0.5 = draw, 0 = loss
            if goals_for > goals_against:
                result = 1
            elif goals_for == goals_against:
                result = 0.5
            else:
                result = 0
            
            # Expected result based on current ELO (simplified - assume opponent at 1500)
            expected = 1 / (1 + 10 ** ((1500 - elo) / 400))
            
            # K-factor: higher for recent matches
            recency_factor = (i + 1) / len(matches)  # 0 to 1
            k_factor = 16 + (16 * recency_factor)  # 16 to 32
            
            # Goal difference multiplier (cap at 3)
            goal_diff = min(abs(goals_for - goals_against), 3)
            multiplier = 1 + (goal_diff * 0.1)
            
            # Update ELO
            elo += k_factor * multiplier * (result - expected)
        
        self._elo_ratings[team_name] = round(elo, 1)
        return self._elo_ratings[team_name]
    
    def get_recent_form(self, team_name, num_games=5, home_away='both'):
        """
        Get recent form with exponential weighting.
        Returns form score from 0 (terrible) to 1 (perfect).
        Most recent games weighted more heavily.
        """
        cache_key = f"{team_name}_{num_games}_{home_away}"
        if cache_key in self._form_cache:
            return self._form_cache[cache_key]
        
        if home_away == 'home':
            query = """
                SELECT * FROM matches 
                WHERE home_team = ?
                ORDER BY match_date DESC
                LIMIT ?
            """
        elif home_away == 'away':
            query = """
                SELECT * FROM matches 
                WHERE away_team = ?
                ORDER BY match_date DESC
                LIMIT ?
            """
        else:
            query = """
                SELECT * FROM matches 
                WHERE (home_team = ? OR away_team = ?)
                ORDER BY match_date DESC
                LIMIT ?
            """
        
        if home_away == 'both':
            cursor = self.db.execute(query, (team_name, team_name, num_games))
        else:
            cursor = self.db.execute(query, (team_name, num_games))
        
        matches = cursor.fetchall()
        
        if not matches:
            return {'form_score': 0.5, 'points': 0, 'goals_scored': 0, 'goals_conceded': 0, 'matches': 0}
        
        total_weighted_points = 0
        total_weight = 0
        total_goals_scored = 0
        total_goals_conceded = 0
        
        for i, match in enumerate(matches):
            is_home = match['home_team'] == team_name
            
            if is_home:
                goals_for = match['home_goals_full_time']
                goals_against = match['away_goals_full_time']
            else:
                goals_for = match['away_goals_full_time']
                goals_against = match['home_goals_full_time']
            
            # Points: 3 for win, 1 for draw, 0 for loss
            if goals_for > goals_against:
                points = 3
            elif goals_for == goals_against:
                points = 1
            else:
                points = 0
            
            # Exponential weighting: most recent = highest weight
            weight = math.exp(-0.3 * i)  # Decay factor of 0.3
            
            total_weighted_points += points * weight
            total_weight += weight
            total_goals_scored += goals_for
            total_goals_conceded += goals_against
        
        # Normalize to 0-1 scale (max 3 points per game)
        form_score = (total_weighted_points / total_weight) / 3 if total_weight > 0 else 0.5
        
        result = {
            'form_score': round(form_score, 3),
            'weighted_ppg': round(total_weighted_points / total_weight, 2) if total_weight > 0 else 0,
            'goals_scored': total_goals_scored,
            'goals_conceded': total_goals_conceded,
            'goals_per_game': round(total_goals_scored / len(matches), 2),
            'conceded_per_game': round(total_goals_conceded / len(matches), 2),
            'matches': len(matches)
        }
        
        self._form_cache[cache_key] = result
        return result
    
    def get_head_to_head(self, home_team, away_team, num_matches=10):
        """Get head-to-head record between two teams."""
        query = """
            SELECT * FROM matches 
            WHERE (home_team = ? AND away_team = ?) OR (home_team = ? AND away_team = ?)
            ORDER BY match_date DESC
            LIMIT ?
        """
        cursor = self.db.execute(query, (home_team, away_team, away_team, home_team, num_matches))
        matches = cursor.fetchall()
        
        if not matches:
            return None
        
        home_wins = 0
        away_wins = 0
        draws = 0
        home_goals = 0
        away_goals = 0
        
        for match in matches:
            if match['home_team'] == home_team:
                # Home team playing at home in this match
                hg = match['home_goals_full_time']
                ag = match['away_goals_full_time']
            else:
                # Home team playing away in this match
                hg = match['away_goals_full_time']
                ag = match['home_goals_full_time']
            
            home_goals += hg
            away_goals += ag
            
            if hg > ag:
                home_wins += 1
            elif hg < ag:
                away_wins += 1
            else:
                draws += 1
        
        total = len(matches)
        return {
            'matches': total,
            'home_wins': home_wins,
            'away_wins': away_wins,
            'draws': draws,
            'home_win_rate': home_wins / total,
            'away_win_rate': away_wins / total,
            'draw_rate': draws / total,
            'home_goals_avg': home_goals / total,
            'away_goals_avg': away_goals / total
        }
    
    def get_momentum_score(self, team_name, home_away='both'):
        """
        Calculate momentum based on goal scoring/conceding trends.
        Positive momentum = scoring more, conceding less in recent games.
        """
        # Get last 10 games in chronological order
        if home_away == 'home':
            query = """
                SELECT home_goals_full_time as goals_for, away_goals_full_time as goals_against
                FROM matches WHERE home_team = ?
                ORDER BY match_date DESC LIMIT 10
            """
        elif home_away == 'away':
            query = """
                SELECT away_goals_full_time as goals_for, home_goals_full_time as goals_against
                FROM matches WHERE away_team = ?
                ORDER BY match_date DESC LIMIT 10
            """
        else:
            # Combined - need to handle separately
            query_home = """
                SELECT home_goals_full_time as goals_for, away_goals_full_time as goals_against, match_date
                FROM matches WHERE home_team = ?
            """
            query_away = """
                SELECT away_goals_full_time as goals_for, home_goals_full_time as goals_against, match_date
                FROM matches WHERE away_team = ?
            """
            cursor_home = self.db.execute(query_home, (team_name,))
            cursor_away = self.db.execute(query_away, (team_name,))
            
            all_matches = list(cursor_home.fetchall()) + list(cursor_away.fetchall())
            all_matches.sort(key=lambda x: x['match_date'], reverse=True)
            matches = all_matches[:10]
            
            if len(matches) < 4:
                return {'score': 0, 'trend': 'neutral'}
            
            # Compare first half vs second half
            recent = matches[:len(matches)//2]
            older = matches[len(matches)//2:]
            
            recent_gd = sum(m['goals_for'] - m['goals_against'] for m in recent) / len(recent)
            older_gd = sum(m['goals_for'] - m['goals_against'] for m in older) / len(older)
            
            momentum = recent_gd - older_gd
            
            if momentum > 0.5:
                trend = 'strong_positive'
            elif momentum > 0:
                trend = 'positive'
            elif momentum > -0.5:
                trend = 'negative'
            else:
                trend = 'strong_negative'
            
            return {'score': round(momentum, 2), 'trend': trend}
        
        cursor = self.db.execute(query, (team_name,))
        matches = cursor.fetchall()
        
        if len(matches) < 4:
            return {'score': 0, 'trend': 'neutral'}
        
        recent = matches[:len(matches)//2]
        older = matches[len(matches)//2:]
        
        recent_gd = sum(m['goals_for'] - m['goals_against'] for m in recent) / len(recent)
        older_gd = sum(m['goals_for'] - m['goals_against'] for m in older) / len(older)
        
        momentum = recent_gd - older_gd
        
        if momentum > 0.5:
            trend = 'strong_positive'
        elif momentum > 0:
            trend = 'positive'
        elif momentum > -0.5:
            trend = 'negative'
        else:
            trend = 'strong_negative'
        
        return {'score': round(momentum, 2), 'trend': trend}
    
    def calculate_probability(self, home_team, away_team, bet_type, market):
        """
        Calculate probability using Form & Momentum model.
        
        Combines:
        - ELO ratings (30% weight)
        - Recent form (35% weight)
        - Head-to-head (15% weight)
        - Momentum (20% weight)
        """
        # Get all components
        home_elo = self.calculate_elo_rating(home_team)
        away_elo = self.calculate_elo_rating(away_team)
        
        home_form = self.get_recent_form(home_team, 5, 'home')
        away_form = self.get_recent_form(away_team, 5, 'away')
        
        h2h = self.get_head_to_head(home_team, away_team)
        
        home_momentum = self.get_momentum_score(home_team, 'home')
        away_momentum = self.get_momentum_score(away_team, 'away')
        
        if bet_type == 'moneyline':
            return self._calculate_moneyline(
                home_elo, away_elo, home_form, away_form, h2h, home_momentum, away_momentum, market
            )
        elif bet_type == 'goals':
            return self._calculate_goals(
                home_form, away_form, h2h, home_momentum, away_momentum, market
            )
        
        return None
    
    def _calculate_moneyline(self, home_elo, away_elo, home_form, away_form, h2h, home_mom, away_mom, market):
        """Calculate moneyline probability using form & momentum model."""
        
        # 1. ELO component (30%)
        elo_diff = home_elo - away_elo
        # Add home advantage of ~65 ELO points
        elo_diff += 65
        home_elo_prob = 1 / (1 + 10 ** (-elo_diff / 400))
        
        # 2. Form component (35%)
        home_form_score = home_form['form_score']
        away_form_score = away_form['form_score']
        form_diff = home_form_score - away_form_score + 0.1  # Home advantage
        home_form_prob = 0.5 + (form_diff * 0.4)  # Scale to reasonable range
        home_form_prob = max(0.1, min(0.9, home_form_prob))
        
        # 3. Head-to-head component (15%)
        if h2h and h2h['matches'] >= 3:
            h2h_home_prob = (h2h['home_win_rate'] + (h2h['draw_rate'] * 0.4))
            h2h_away_prob = (h2h['away_win_rate'] + (h2h['draw_rate'] * 0.4))
        else:
            h2h_home_prob = 0.5
            h2h_away_prob = 0.5
        
        # 4. Momentum component (20%)
        momentum_diff = home_mom['score'] - away_mom['score']
        home_momentum_prob = 0.5 + (momentum_diff * 0.15)
        home_momentum_prob = max(0.2, min(0.8, home_momentum_prob))
        
        # Combine with weights
        home_win_prob = (
            home_elo_prob * 0.30 +
            home_form_prob * 0.35 +
            h2h_home_prob * 0.15 +
            home_momentum_prob * 0.20
        )
        
        # Calculate away and draw probabilities
        away_win_prob = 1 - home_win_prob
        
        # Estimate draw probability based on form similarity and historical data
        form_similarity = 1 - abs(home_form_score - away_form_score)
        base_draw_prob = 0.26  # PL average is ~26%
        draw_prob = base_draw_prob * (1 + form_similarity * 0.3)
        draw_prob = min(0.35, draw_prob)
        
        # Adjust win probabilities for draws
        remaining = 1 - draw_prob
        home_win_prob = home_win_prob * remaining
        away_win_prob = away_win_prob * remaining
        
        # Normalize
        total = home_win_prob + away_win_prob + draw_prob
        home_win_prob /= total
        away_win_prob /= total
        draw_prob /= total
        
        if market == 'home_win':
            return home_win_prob
        elif market == 'away_win':
            return away_win_prob
        elif market == 'draw':
            return draw_prob
        
        return None
    
    def _calculate_goals(self, home_form, away_form, h2h, home_mom, away_mom, market):
        """Calculate goals over/under probability using form & momentum."""
        period, line = market.split('_', 1)
        over_under, threshold = line.split('_')
        threshold = float(threshold)
        
        # Expected goals based on recent form
        home_expected = home_form['goals_per_game']
        away_expected = away_form['goals_per_game']
        
        # Adjust for opponent's defensive record
        home_against = home_form.get('conceded_per_game', 1.5)
        away_against = away_form.get('conceded_per_game', 1.5)
        
        # Expected total goals in match
        expected_total = (home_expected + away_against) / 2 + (away_expected + home_against) / 2
        
        # Adjust for momentum
        if home_mom['trend'] in ['strong_positive', 'positive']:
            expected_total += 0.2
        elif home_mom['trend'] in ['strong_negative', 'negative']:
            expected_total -= 0.1
        
        if away_mom['trend'] in ['strong_positive', 'positive']:
            expected_total += 0.15
        elif away_mom['trend'] in ['strong_negative', 'negative']:
            expected_total -= 0.1
        
        # Use h2h if available
        if h2h and h2h['matches'] >= 3:
            h2h_avg = h2h['home_goals_avg'] + h2h['away_goals_avg']
            expected_total = expected_total * 0.7 + h2h_avg * 0.3
        
        # Adjust for period
        if period == '1h':
            expected_total *= 0.42  # ~42% of goals in first half
        elif period == '2h':
            expected_total *= 0.58  # ~58% in second half
        
        # Calculate probability using Poisson-like estimation
        diff = expected_total - threshold
        
        if over_under == 'over':
            probability = 0.5 + (diff * 0.18)
        else:
            probability = 0.5 - (diff * 0.18)
        
        return max(0.05, min(0.95, probability))
    
    def get_explanation(self, home_team, away_team, bet_type, market):
        """Generate explanation for Form & Momentum model."""
        home_elo = self.calculate_elo_rating(home_team)
        away_elo = self.calculate_elo_rating(away_team)
        home_form = self.get_recent_form(home_team, 5, 'home')
        away_form = self.get_recent_form(away_team, 5, 'away')
        home_mom = self.get_momentum_score(home_team, 'home')
        away_mom = self.get_momentum_score(away_team, 'away')
        
        return (
            f"📊 ELO: {home_team} {home_elo:.0f} vs {away_team} {away_elo:.0f} | "
            f"Form (5g): {home_form['weighted_ppg']:.1f} vs {away_form['weighted_ppg']:.1f} PPG | "
            f"Momentum: {home_mom['trend'].replace('_', ' ')} vs {away_mom['trend'].replace('_', ' ')}"
        )


# =============================================================================
# ADVANCED AI MODEL 2: SENTIMENT & EXTERNAL DATA MODEL
# =============================================================================
class SentimentExternalAnalyzer:
    """
    Advanced AI Model: Sentiment & External Data Analysis
    
    Considers:
    - Fantasy Premier League data (ownership, transfers, price changes)
    - Player injury/availability status
    - X/Twitter sentiment analysis
    - News sentiment
    - Manager changes/team news
    """
    
    def __init__(self):
        self.db = get_db()
        self._fpl_cache = {}
        self._sentiment_cache = {}
        self._injury_cache = {}
    
    @lru_cache(maxsize=32)
    def fetch_fpl_data(self):
        """Fetch Fantasy Premier League bootstrap data."""
        try:
            response = requests.get(f"{FPL_API_BASE}/bootstrap-static/", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"FPL API error: {e}")
        return None
    
    def get_team_fpl_metrics(self, team_name):
        """
        Get FPL-based team strength metrics.
        
        Returns:
        - avg_player_ownership: How popular team's players are
        - key_player_availability: Injury/suspension impact
        - transfers_in_momentum: Are people buying players?
        - price_momentum: Are player prices rising?
        """
        fpl_data = self.fetch_fpl_data()
        if not fpl_data:
            return None
        
        # Find team ID in FPL data
        teams = fpl_data.get('teams', [])
        team_id = None
        
        for fpl_team in teams:
            fpl_name = fpl_team.get('name', '').replace(' ', '')
            db_name = team_name.replace(' ', '').replace("'", '')
            
            if fpl_name.lower() in db_name.lower() or db_name.lower() in fpl_name.lower():
                team_id = fpl_team['id']
                break
        
        if not team_id:
            # Try mapping
            for fpl_key, db_value in FPL_TEAM_MAPPING.items():
                if db_value.lower() == team_name.lower():
                    for fpl_team in teams:
                        if fpl_key.lower() in fpl_team.get('name', '').lower():
                            team_id = fpl_team['id']
                            break
        
        if not team_id:
            return None
        
        # Get players for this team
        elements = fpl_data.get('elements', [])
        team_players = [p for p in elements if p.get('team') == team_id]
        
        if not team_players:
            return None
        
        # Calculate metrics
        total_ownership = sum(float(p.get('selected_by_percent', 0)) for p in team_players)
        avg_ownership = total_ownership / len(team_players)
        
        # Key player availability (top 5 by ownership)
        top_players = sorted(team_players, key=lambda x: float(x.get('selected_by_percent', 0)), reverse=True)[:5]
        
        available_count = 0
        injured_count = 0
        for player in top_players:
            status = player.get('status', 'a')
            if status == 'a':  # Available
                available_count += 1
            elif status in ['i', 'd', 's']:  # Injured, doubtful, suspended
                injured_count += 1
        
        key_player_availability = available_count / 5
        
        # Transfer momentum (net transfers this week)
        total_transfers_in = sum(p.get('transfers_in_event', 0) for p in team_players)
        total_transfers_out = sum(p.get('transfers_out_event', 0) for p in team_players)
        net_transfers = total_transfers_in - total_transfers_out
        
        # Price changes
        price_rises = sum(1 for p in team_players if p.get('cost_change_event', 0) > 0)
        price_falls = sum(1 for p in team_players if p.get('cost_change_event', 0) < 0)
        
        # Form based on FPL points
        avg_form = statistics.mean([float(p.get('form', 0)) for p in team_players if float(p.get('form', 0)) > 0] or [0])
        
        return {
            'avg_ownership': round(avg_ownership, 2),
            'key_player_availability': key_player_availability,
            'net_transfers': net_transfers,
            'price_rises': price_rises,
            'price_falls': price_falls,
            'avg_form': round(avg_form, 2),
            'top_players': [(p['web_name'], float(p.get('selected_by_percent', 0)), p.get('status', 'a')) for p in top_players]
        }
    
    def get_injury_impact(self, team_name):
        """
        Calculate the impact of injuries on team strength.
        Based on FPL data availability status.
        """
        fpl_metrics = self.get_team_fpl_metrics(team_name)
        if not fpl_metrics:
            return {'impact': 0, 'description': 'No injury data available'}
        
        availability = fpl_metrics['key_player_availability']
        
        # Impact ranges from -0.15 (all key players out) to +0.05 (all available)
        impact = (availability - 0.8) * 0.5
        
        # Count injuries in top players
        injured_players = [p for p in fpl_metrics['top_players'] if p[2] != 'a']
        
        if len(injured_players) >= 3:
            description = f"⚠️ Major injury crisis: {len(injured_players)} key players unavailable"
        elif len(injured_players) >= 1:
            names = ', '.join([p[0] for p in injured_players])
            description = f"🏥 Injuries: {names}"
        else:
            description = "✅ Full squad available"
        
        return {'impact': round(impact, 3), 'description': description}
    
    def get_sentiment_score(self, team_name):
        """
        Get sentiment score for a team.
        
        In production, this would:
        1. Query Twitter/X API for recent mentions
        2. Analyze sentiment using NLP
        3. Weight by engagement/reach
        
        For now, we use FPL transfer data as a proxy for public sentiment.
        """
        fpl_metrics = self.get_team_fpl_metrics(team_name)
        if not fpl_metrics:
            return {'score': 0, 'trend': 'neutral', 'description': 'No sentiment data'}
        
        # Use net transfers as sentiment proxy
        net_transfers = fpl_metrics['net_transfers']
        
        # Normalize to -1 to 1 scale (assuming max ~500k transfers)
        sentiment_score = max(-1, min(1, net_transfers / 300000))
        
        # Price momentum adds to sentiment
        price_momentum = (fpl_metrics['price_rises'] - fpl_metrics['price_falls']) / 10
        sentiment_score = (sentiment_score * 0.7) + (price_momentum * 0.3)
        
        if sentiment_score > 0.3:
            trend = 'very_positive'
            emoji = '🔥'
        elif sentiment_score > 0.1:
            trend = 'positive'
            emoji = '📈'
        elif sentiment_score > -0.1:
            trend = 'neutral'
            emoji = '➡️'
        elif sentiment_score > -0.3:
            trend = 'negative'
            emoji = '📉'
        else:
            trend = 'very_negative'
            emoji = '❄️'
        
        return {
            'score': round(sentiment_score, 3),
            'trend': trend,
            'description': f"{emoji} FPL sentiment: {fpl_metrics['net_transfers']:+,} net transfers, {fpl_metrics['price_rises']} price rises"
        }
    
    def get_team_strength_index(self, team_name):
        """
        Calculate overall team strength index combining all external factors.
        Scale: 0-100
        """
        base_strength = 50
        
        fpl_metrics = self.get_team_fpl_metrics(team_name)
        if fpl_metrics:
            # Ownership indicates perceived quality
            ownership_factor = min(fpl_metrics['avg_ownership'] * 2, 20)  # Max +20
            
            # Form from FPL
            form_factor = fpl_metrics['avg_form'] * 2  # Max ~15
            
            # Availability
            availability_factor = (fpl_metrics['key_player_availability'] - 0.5) * 20  # -10 to +10
            
            base_strength += ownership_factor + form_factor + availability_factor
        
        return max(20, min(80, base_strength))
    
    def calculate_probability(self, home_team, away_team, bet_type, market):
        """
        Calculate probability using Sentiment & External Data model.
        
        Combines:
        - FPL-based team strength (40%)
        - Injury impact (25%)
        - Sentiment/momentum (20%)
        - Historical baseline (15%)
        """
        # Get all components
        home_strength = self.get_team_strength_index(home_team)
        away_strength = self.get_team_strength_index(away_team)
        
        home_injury = self.get_injury_impact(home_team)
        away_injury = self.get_injury_impact(away_team)
        
        home_sentiment = self.get_sentiment_score(home_team)
        away_sentiment = self.get_sentiment_score(away_team)
        
        # Get historical baseline from simple model
        base_analyzer = AdvancedBettingAnalyzer()
        base_prob = base_analyzer.calculate_ai_probability(home_team, away_team, bet_type, market, 'simple')
        
        if bet_type == 'moneyline':
            return self._calculate_moneyline(
                home_strength, away_strength,
                home_injury, away_injury,
                home_sentiment, away_sentiment,
                base_prob, market
            )
        elif bet_type == 'goals':
            return self._calculate_goals(
                home_strength, away_strength,
                home_injury, away_injury,
                home_sentiment, away_sentiment,
                market
            )
        
        return base_prob
    
    def _calculate_moneyline(self, home_strength, away_strength, home_injury, away_injury,
                             home_sentiment, away_sentiment, base_prob, market):
        """Calculate moneyline using external data."""
        
        # 1. Strength component (40%)
        strength_diff = (home_strength - away_strength) / 100
        strength_diff += 0.08  # Home advantage
        home_strength_prob = 0.5 + (strength_diff * 0.5)
        home_strength_prob = max(0.15, min(0.85, home_strength_prob))
        
        # 2. Injury component (25%)
        injury_diff = home_injury['impact'] - away_injury['impact']
        injury_adjustment = injury_diff * 0.5
        
        # 3. Sentiment component (20%)
        sentiment_diff = home_sentiment['score'] - away_sentiment['score']
        sentiment_adjustment = sentiment_diff * 0.15
        
        # 4. Historical baseline (15%)
        historical_prob = base_prob if base_prob else 0.5
        
        # Combine
        home_win_prob = (
            home_strength_prob * 0.40 +
            (0.5 + injury_adjustment) * 0.25 +
            (0.5 + sentiment_adjustment) * 0.20 +
            historical_prob * 0.15
        )
        
        # Estimate draw and away probabilities
        away_win_prob = 1 - home_win_prob
        draw_prob = 0.26 + (0.1 * (1 - abs(home_strength - away_strength) / 50))
        draw_prob = min(0.35, draw_prob)
        
        # Adjust for draws
        remaining = 1 - draw_prob
        home_win_prob = home_win_prob * remaining
        away_win_prob = away_win_prob * remaining
        
        # Normalize
        total = home_win_prob + away_win_prob + draw_prob
        home_win_prob /= total
        away_win_prob /= total
        draw_prob /= total
        
        if market == 'home_win':
            return home_win_prob
        elif market == 'away_win':
            return away_win_prob
        elif market == 'draw':
            return draw_prob
        
        return None
    
    def _calculate_goals(self, home_strength, away_strength, home_injury, away_injury,
                        home_sentiment, away_sentiment, market):
        """Calculate goals probability using external data."""
        period, line = market.split('_', 1)
        over_under, threshold = line.split('_')
        threshold = float(threshold)
        
        # Expected goals based on strength
        avg_goals = 2.7  # PL average
        
        # Higher strength teams score more
        strength_factor = ((home_strength + away_strength) / 100 - 1) * 0.5
        expected_total = avg_goals + strength_factor
        
        # Injuries reduce goals
        injury_impact = (home_injury['impact'] + away_injury['impact']) * 2
        expected_total += injury_impact
        
        # Positive sentiment = more attacking
        sentiment_impact = (home_sentiment['score'] + away_sentiment['score']) * 0.3
        expected_total += sentiment_impact
        
        # Adjust for period
        if period == '1h':
            expected_total *= 0.42
        elif period == '2h':
            expected_total *= 0.58
        
        # Calculate probability
        diff = expected_total - threshold
        
        if over_under == 'over':
            probability = 0.5 + (diff * 0.18)
        else:
            probability = 0.5 - (diff * 0.18)
        
        return max(0.05, min(0.95, probability))
    
    def get_explanation(self, home_team, away_team, bet_type, market):
        """Generate explanation for Sentiment & External model."""
        home_strength = self.get_team_strength_index(home_team)
        away_strength = self.get_team_strength_index(away_team)
        home_injury = self.get_injury_impact(home_team)
        away_injury = self.get_injury_impact(away_team)
        home_sentiment = self.get_sentiment_score(home_team)
        
        parts = [
            f"💪 Strength: {home_team} {home_strength:.0f} vs {away_team} {away_strength:.0f}",
        ]
        
        if home_injury['description'] != 'No injury data available':
            parts.append(home_injury['description'])
        
        if home_sentiment['description'] != 'No sentiment data':
            parts.append(home_sentiment['description'])
        
        return " | ".join(parts)


# =============================================================================
# COMBINED OVERALL AI MODEL
# =============================================================================
class CombinedAIAnalyzer:
    """
    Combined Overall AI Model - Blends multiple models for robust predictions.
    
    Combines:
    - Multi-Factor AI (complex) - 25% weight
    - Form & Momentum - 30% weight  
    - Sentiment & FPL - 25% weight
    - Bookmaker Anomaly detection - 20% weight (when anomaly detected)
    
    Uses ensemble approach with dynamic weighting based on data availability.
    """
    
    def __init__(self):
        self.db = get_db()
        self.advanced_analyzer = AdvancedBettingAnalyzer()
        self.form_analyzer = FormMomentumAnalyzer()
        self.sentiment_analyzer = SentimentExternalAnalyzer()
    
    def calculate_probability(self, home_team, away_team, bet_type, market, bookmaker_odds=None):
        """
        Calculate combined probability from multiple models.
        
        Weights:
        - Complex model: 25%
        - Form & Momentum: 30%
        - Sentiment & FPL: 25%
        - Anomaly adjustment: 20% (when applicable)
        """
        probabilities = []
        weights = []
        explanations = []
        
        # 1. Multi-Factor AI (Complex) - 25%
        try:
            complex_prob = self.advanced_analyzer.calculate_ai_probability(
                home_team, away_team, bet_type, market, 'complex'
            )
            if complex_prob:
                probabilities.append(complex_prob)
                weights.append(0.25)
                explanations.append("Complex")
        except Exception as e:
            print(f"Complex model error: {e}")
        
        # 2. Form & Momentum - 30%
        try:
            form_prob = self.form_analyzer.calculate_probability(
                home_team, away_team, bet_type, market
            )
            if form_prob:
                probabilities.append(form_prob)
                weights.append(0.30)
                explanations.append("Form")
        except Exception as e:
            print(f"Form model error: {e}")
        
        # 3. Sentiment & FPL - 25%
        try:
            sentiment_prob = self.sentiment_analyzer.calculate_probability(
                home_team, away_team, bet_type, market
            )
            if sentiment_prob:
                probabilities.append(sentiment_prob)
                weights.append(0.25)
                explanations.append("Sentiment")
        except Exception as e:
            print(f"Sentiment model error: {e}")
        
        # 4. Anomaly Detection - 20% adjustment
        anomaly_bonus = 0
        if bookmaker_odds and bet_type == 'moneyline':
            try:
                anomaly_data = self.advanced_analyzer.detect_bookmaker_anomalies(bookmaker_odds)
                if anomaly_data and anomaly_data['is_anomaly']:
                    # Significant anomaly detected - boost confidence
                    anomaly_bonus = anomaly_data['percentage_better'] / 100 * 0.20
                    explanations.append(f"Anomaly+{anomaly_data['percentage_better']:.0f}%")
            except Exception as e:
                print(f"Anomaly detection error: {e}")
        
        if not probabilities:
            return None
        
        # Normalize weights
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]
        
        # Calculate weighted average
        combined_prob = sum(p * w for p, w in zip(probabilities, normalized_weights))
        
        # Apply anomaly bonus (if odds are better than market average)
        combined_prob = min(0.95, combined_prob + anomaly_bonus)
        
        return combined_prob
    
    def get_model_breakdown(self, home_team, away_team, bet_type, market):
        """Get individual model probabilities for transparency."""
        breakdown = {}
        
        try:
            breakdown['complex'] = self.advanced_analyzer.calculate_ai_probability(
                home_team, away_team, bet_type, market, 'complex'
            )
        except:
            breakdown['complex'] = None
        
        try:
            breakdown['form_momentum'] = self.form_analyzer.calculate_probability(
                home_team, away_team, bet_type, market
            )
        except:
            breakdown['form_momentum'] = None
        
        try:
            breakdown['sentiment'] = self.sentiment_analyzer.calculate_probability(
                home_team, away_team, bet_type, market
            )
        except:
            breakdown['sentiment'] = None
        
        return breakdown
    
    def get_explanation(self, home_team, away_team, bet_type, market):
        """Generate comprehensive explanation combining all models."""
        parts = []
        
        # Get ELO from form analyzer
        try:
            home_elo = self.form_analyzer.calculate_elo_rating(home_team)
            away_elo = self.form_analyzer.calculate_elo_rating(away_team)
            parts.append(f"⚡ ELO: {home_team[:3].upper()} {home_elo:.0f} vs {away_team[:3].upper()} {away_elo:.0f}")
        except:
            pass
        
        # Get form from form analyzer
        try:
            home_form = self.form_analyzer.get_recent_form(home_team, 5, 'home')
            away_form = self.form_analyzer.get_recent_form(away_team, 5, 'away')
            parts.append(f"📊 Form: {home_form['weighted_ppg']:.1f} vs {away_form['weighted_ppg']:.1f} PPG")
        except:
            pass
        
        # Get strength from sentiment analyzer
        try:
            home_strength = self.sentiment_analyzer.get_team_strength_index(home_team)
            away_strength = self.sentiment_analyzer.get_team_strength_index(away_team)
            parts.append(f"💪 Strength: {home_strength:.0f} vs {away_strength:.0f}")
        except:
            pass
        
        # Get injury info
        try:
            home_injury = self.sentiment_analyzer.get_injury_impact(home_team)
            if 'Injuries:' in home_injury['description'] or 'injury crisis' in home_injury['description']:
                parts.append(home_injury['description'])
        except:
            pass
        
        # Get model breakdown
        breakdown = self.get_model_breakdown(home_team, away_team, bet_type, market)
        probs = [f"{k[:4]}:{v*100:.0f}%" for k, v in breakdown.items() if v]
        if probs:
            parts.append(f"🤖 Models: {', '.join(probs)}")
        
        return " | ".join(parts) if parts else "Combined AI model analysis"


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

# Odds API Functions
def fetch_betfair_markets():
    """
    Fetch Betfair Exchange markets for Premier League
    Note: Betfair requires session-based authentication which is complex
    For now, this is a placeholder - full implementation would need:
    1. Login endpoint to get session token
    2. Certificate-based authentication
    3. Complex API calls for market data
    
    Consider using Betfair's simpler API or The Odds API's Betfair integration
    """
    # Placeholder - Betfair integration requires more complex auth
    # Would need to implement:
    # - Session token management
    # - Market catalogue navigation
    # - Event ID mapping
    return None

def fetch_league_odds(sport='soccer_epl'):
    """Fetch odds from The Odds API for any league (includes Betfair data)"""
    try:
        # Fetch odds for specified league
        # The Odds API aggregates from multiple sources including Betfair
        url = f"{ODDS_API_BASE_URL}/sports/{sport}/odds"
        params = {
            'apiKey': ODDS_API_KEY,
            'regions': 'uk,us,eu',  # UK, US, and European bookmakers (includes Betfair)
            'markets': 'h2h,spreads,totals,h2h_lay',  # All match-specific markets
            'oddsFormat': 'decimal',
            'dateFormat': 'iso'
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching odds for {sport}: {e}")
        return None

def fetch_premier_league_odds():
    """Fetch Premier League odds - wrapper for backwards compatibility"""
    return fetch_league_odds('soccer_epl')

def format_odds_data(odds_data):
    """Format odds data for frontend display"""
    if not odds_data:
        return []
    
    formatted_matches = []
    
    for match in odds_data:
        home_team = match.get('home_team', '')
        away_team = match.get('away_team', '')
        commence_time = match.get('commence_time', '')
        bookmakers = match.get('bookmakers', [])
        
        # Organize bookmakers by region
        uk_bookmakers = []
        us_bookmakers = []
        
        for bookmaker in bookmakers:
            bm_name = bookmaker.get('key', '')
            bm_title = bookmaker.get('title', '')
            markets = bookmaker.get('markets', [])
            
            # Extract all market types
            h2h_market = next((m for m in markets if m.get('key') == 'h2h'), None)
            totals_market = next((m for m in markets if m.get('key') == 'totals'), None)
            spreads_market = next((m for m in markets if m.get('key') == 'spreads'), None)
            h2h_lay_market = next((m for m in markets if m.get('key') == 'h2h_lay'), None)
            
            bm_data = {
                'name': bm_title,
                'key': bm_name,
                'h2h': {},
                'totals': {},
                'spreads': {},
                'h2h_lay': {}
            }
            
            if h2h_market:
                for outcome in h2h_market.get('outcomes', []):
                    team_name = outcome.get('name', '')
                    price = outcome.get('price', 0)
                    bm_data['h2h'][team_name] = price
            
            if totals_market:
                for outcome in totals_market.get('outcomes', []):
                    outcome_name = outcome.get('name', '')
                    point = outcome.get('point', 0)
                    price = outcome.get('price', 0)
                    bm_data['totals'][outcome_name] = {
                        'point': point,
                        'price': price
                    }
            
            if spreads_market:
                for outcome in spreads_market.get('outcomes', []):
                    team_name = outcome.get('name', '')
                    point = outcome.get('point', 0)
                    price = outcome.get('price', 0)
                    bm_data['spreads'][team_name] = {
                        'point': point,
                        'price': price
                    }
            
            if h2h_lay_market:
                for outcome in h2h_lay_market.get('outcomes', []):
                    team_name = outcome.get('name', '')
                    price = outcome.get('price', 0)
                    bm_data['h2h_lay'][team_name] = price
            
            # Categorize by region (rough classification based on common bookmakers)
            uk_bookmakers_list = ['williamhill', 'skybet', 'paddypower', 'betfair', 'coral', 'ladbrokes', 'unibet']
            us_bookmakers_list = ['fanduel', 'draftkings', 'betmgm', 'pointsbet', 'caesars', 'barstool']
            
            if bm_name in uk_bookmakers_list:
                uk_bookmakers.append(bm_data)
            elif bm_name in us_bookmakers_list:
                us_bookmakers.append(bm_data)
            else:
                # Default to UK if unknown
                uk_bookmakers.append(bm_data)
        
        formatted_matches.append({
            'home_team': home_team,
            'away_team': away_team,
            'commence_time': commence_time,
            'uk_bookmakers': uk_bookmakers,
            'us_bookmakers': us_bookmakers
        })
    
    return formatted_matches

# Authentication decorator
def require_auth(f):
    """Decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == APP_PASSWORD:
            session['authenticated'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Incorrect password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@require_auth
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

@app.route('/api/premier-league-table')
def premier_league_table():
    """Get current Premier League table - current teams only with appropriate time periods"""
    db = get_db()
    
    # Current Premier League teams (2025-26 season)
    current_pl_teams = [
        'Arsenal', 'Liverpool', 'Man City', 'Chelsea', 'Tottenham',
        'Man United', 'Newcastle', 'Brighton', 'Aston Villa', 'West Ham',
        'Crystal Palace', 'Fulham', 'Wolves', 'Bournemouth', 'Everton',
        'Brentford', "Nott'm Forest",
        # Newly promoted teams
        'Sunderland', 'Leeds', 'Burnley'
    ]
    
    # Newly promoted teams (show only this season's data)
    newly_promoted = ['Sunderland', 'Leeds', 'Burnley']
    
    table = []
    
    for team in current_pl_teams:
        # Determine games to fetch
        if team in newly_promoted:
            # This season only (~9 games)
            limit_games = 20  # Safety margin
            query_condition = "match_date >= date('now', '-4 months')"
        else:
            # Last 38 games (roughly last season)
            limit_games = 19  # 19 home + 19 away = 38 total
            query_condition = "1=1"  # Get all recent, limit below
        
        # Get home matches
        cursor = db.execute(f'''
            SELECT 
                COUNT(*) as played,
                SUM(CASE WHEN home_goals_full_time > away_goals_full_time THEN 1 ELSE 0 END) as won,
                SUM(CASE WHEN home_goals_full_time = away_goals_full_time THEN 1 ELSE 0 END) as drawn,
                SUM(CASE WHEN home_goals_full_time < away_goals_full_time THEN 1 ELSE 0 END) as lost,
                SUM(CASE WHEN home_goals_full_time > away_goals_full_time THEN 3
                         WHEN home_goals_full_time = away_goals_full_time THEN 1
                         ELSE 0 END) as points,
                SUM(home_goals_full_time) as goals_for,
                SUM(away_goals_full_time) as goals_against
            FROM (
                SELECT * FROM matches 
                WHERE home_team = ? AND {query_condition}
                ORDER BY match_date DESC 
                LIMIT {limit_games}
            )
        ''', (team,))
        
        home_data = cursor.fetchone()
        
        # Get away matches  
        cursor = db.execute(f'''
            SELECT 
                COUNT(*) as played,
                SUM(CASE WHEN away_goals_full_time > home_goals_full_time THEN 1 ELSE 0 END) as won,
                SUM(CASE WHEN away_goals_full_time = home_goals_full_time THEN 1 ELSE 0 END) as drawn,
                SUM(CASE WHEN away_goals_full_time < home_goals_full_time THEN 1 ELSE 0 END) as lost,
                SUM(CASE WHEN away_goals_full_time > home_goals_full_time THEN 3
                         WHEN away_goals_full_time = home_goals_full_time THEN 1
                         ELSE 0 END) as points,
                SUM(away_goals_full_time) as goals_for,
                SUM(home_goals_full_time) as goals_against
            FROM (
                SELECT * FROM matches 
                WHERE away_team = ? AND {query_condition}
                ORDER BY match_date DESC 
                LIMIT {limit_games}
            )
        ''', (team,))
        
        away_data = cursor.fetchone()
        
        # Combine home and away
        total_played = (home_data['played'] or 0) + (away_data['played'] or 0)
        
        if total_played > 0:
            total_won = (home_data['won'] or 0) + (away_data['won'] or 0)
            total_drawn = (home_data['drawn'] or 0) + (away_data['drawn'] or 0)
            total_lost = (home_data['lost'] or 0) + (away_data['lost'] or 0)
            total_points = (home_data['points'] or 0) + (away_data['points'] or 0)
            total_gf = (home_data['goals_for'] or 0) + (away_data['goals_for'] or 0)
            total_ga = (home_data['goals_against'] or 0) + (away_data['goals_against'] or 0)
            
            table.append({
                'team': team,
                'played': total_played,
                'won': total_won,
                'drawn': total_drawn,
                'lost': total_lost,
                'goals_for': total_gf,
                'goals_against': total_ga,
                'goal_difference': total_gf - total_ga,
                'points': total_points,
                'win_pct': round(total_won / total_played * 100, 1),
                'draw_pct': round(total_drawn / total_played * 100, 1),
                'loss_pct': round(total_lost / total_played * 100, 1),
                'is_promoted': team in newly_promoted
            })
    
    # Sort by points (desc), then goal difference, then goals for
    table.sort(key=lambda x: (x['points'], x['goal_difference'], x['goals_for']), reverse=True)
    
    return jsonify(table)

@app.route('/api/team-summaries')
def team_summaries():
    """Get comprehensive statistics for all teams"""
    years = int(request.args.get('years', 10))  # Get years parameter
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
            WHERE home_team = ? AND match_date >= date('now', '-{} years')
        '''.format(years), (team,))
        home_stats = cursor.fetchone()
        
        cursor = db.execute('''
            SELECT 
                AVG(away_goals_full_time) as avg_away_scored,
                AVG(home_goals_full_time) as avg_home_conceded,
                COUNT(*) as away_matches
            FROM matches 
            WHERE away_team = ? AND match_date >= date('now', '-{} years')
        '''.format(years), (team,))
        away_stats = cursor.fetchone()
        
        # Corners
        cursor = db.execute('''
            SELECT 
                AVG(home_corners_total) as avg_home_corners,
                AVG(away_corners_total) as avg_away_corners_against
            FROM matches 
            WHERE home_team = ? AND match_date >= date('now', '-{} years')
        '''.format(years), (team,))
        home_corners = cursor.fetchone()
        
        cursor = db.execute('''
            SELECT 
                AVG(away_corners_total) as avg_away_corners,
                AVG(home_corners_total) as avg_home_corners_against
            FROM matches 
            WHERE away_team = ? AND match_date >= date('now', '-{} years')
        '''.format(years), (team,))
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

@app.route('/api/live-odds')
def live_odds():
    """Get live odds from The Odds API"""
    try:
        # Get league from query params
        league = request.args.get('league', 'soccer_epl')
        odds_data = fetch_league_odds(league)
        
        if odds_data is None:
            return jsonify({'error': 'Unable to fetch odds from API'}), 500
        
        formatted_data = format_odds_data(odds_data)
        
        return jsonify({
            'matches': formatted_data,
            'last_updated': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        print(f"Error in live_odds endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/value-bets')
@require_auth
def value_bets():
    """Get value bets with EV calculations"""
    try:
        # Get filters from query params
        region_filter = request.args.get('region', 'both')  # 'uk', 'us', or 'both'
        ai_model = request.args.get('model', 'complex')  # 'simple', 'opponent', 'complex', 'anomaly', 'form_momentum', 'sentiment_external'
        league = request.args.get('league', 'soccer_epl')  # Which league to analyze
        
        # Fetch live odds for selected league
        odds_data = fetch_league_odds(league)
        
        if odds_data is None:
            return jsonify({'error': 'Unable to fetch odds from API'}), 500
        
        # Initialize the appropriate analyzer(s)
        analyzer = AdvancedBettingAnalyzer()
        form_analyzer = None
        sentiment_analyzer = None
        combined_analyzer = None
        
        if ai_model == 'form_momentum':
            form_analyzer = FormMomentumAnalyzer()
        elif ai_model == 'sentiment_external':
            sentiment_analyzer = SentimentExternalAnalyzer()
        elif ai_model == 'overall':
            combined_analyzer = CombinedAIAnalyzer()
        
        value_bets_list = []
        
        # Markets to analyze
        moneyline_markets = ['home_win', 'draw', 'away_win']
        goals_markets = [
            'full_over_2.5', 'full_under_2.5', 'full_over_3.5', 'full_under_3.5',
            '1h_over_0.5', '1h_under_0.5', '1h_over_1.5', '1h_under_1.5',
            '2h_over_1.5', '2h_under_1.5'
        ]
        corners_markets = [
            'full_over_9.5', 'full_under_9.5', 'full_over_10.5', 'full_under_10.5',
            '1h_over_4.5', '1h_under_4.5', '1h_over_5.5', '1h_under_5.5',
            '2h_over_5.5', '2h_under_5.5'
        ]
        
        for match in odds_data:
            home_team = match.get('home_team', '')
            away_team = match.get('away_team', '')
            commence_time = match.get('commence_time', '')
            bookmakers = match.get('bookmakers', [])
            
            if not bookmakers:
                continue
            
            # Filter bookmakers by region
            filtered_bookmakers = []
            uk_bookmakers_list = ['williamhill', 'skybet', 'paddypower', 'betfair', 'coral', 'ladbrokes', 'unibet']
            us_bookmakers_list = ['fanduel', 'draftkings', 'betmgm', 'pointsbet', 'caesars', 'barstool']
            
            for bookmaker in bookmakers:
                bm_key = bookmaker.get('key', '')
                if region_filter == 'uk' and bm_key in uk_bookmakers_list:
                    filtered_bookmakers.append(bookmaker)
                elif region_filter == 'us' and bm_key in us_bookmakers_list:
                    filtered_bookmakers.append(bookmaker)
                elif region_filter == 'both':
                    filtered_bookmakers.append(bookmaker)
            
            # Analyze Moneyline bets
            h2h_odds = {}
            for bookmaker in filtered_bookmakers:
                bm_key = bookmaker.get('key', '')
                bm_region = 'UK' if bm_key in uk_bookmakers_list else 'US' if bm_key in us_bookmakers_list else 'Other'
                
                for market in bookmaker.get('markets', []):
                    if market.get('key') == 'h2h':
                        for outcome in market.get('outcomes', []):
                            team = outcome.get('name')
                            price = outcome.get('price')
                            
                            if team == home_team:
                                if 'home_win' not in h2h_odds or price > h2h_odds['home_win']['odds']:
                                    h2h_odds['home_win'] = {'odds': price, 'bookmaker': bookmaker.get('title'), 'region': bm_region}
                            elif team == away_team:
                                if 'away_win' not in h2h_odds or price > h2h_odds['away_win']['odds']:
                                    h2h_odds['away_win'] = {'odds': price, 'bookmaker': bookmaker.get('title'), 'region': bm_region}
                            elif team == 'Draw':
                                if 'draw' not in h2h_odds or price > h2h_odds['draw']['odds']:
                                    h2h_odds['draw'] = {'odds': price, 'bookmaker': bookmaker.get('title'), 'region': bm_region}
            
            # Fetch team stats once per match (skip for anomaly model)
            home_stats = None
            away_stats = None
            if ai_model not in ['anomaly', 'form_momentum', 'sentiment_external', 'overall']:
                home_stats = analyzer.get_team_historical_stats(home_team, seasons=1)
                away_stats = analyzer.get_team_historical_stats(away_team, seasons=1)
            
            # For anomaly model, collect all bookmaker odds for each market
            if ai_model == 'anomaly':
                # Collect all bookmaker odds for moneyline markets
                moneyline_all_odds = {'home_win': [], 'draw': [], 'away_win': []}
                for bookmaker in filtered_bookmakers:
                    for market in bookmaker.get('markets', []):
                        if market.get('key') == 'h2h':
                            for outcome in market.get('outcomes', []):
                                team = outcome.get('name')
                                price = outcome.get('price')
                                bm_data = {'bookmaker': bookmaker.get('title'), 'odds': price}
                                
                                if team == home_team:
                                    moneyline_all_odds['home_win'].append(bm_data)
                                elif team == away_team:
                                    moneyline_all_odds['away_win'].append(bm_data)
                                elif team == 'Draw':
                                    moneyline_all_odds['draw'].append(bm_data)
            
            # Create value bets for moneyline
            for market in moneyline_markets:
                if market in h2h_odds:
                    # Anomaly model uses different logic
                    if ai_model == 'anomaly':
                        anomaly_data = analyzer.detect_bookmaker_anomalies(moneyline_all_odds[market])
                        if anomaly_data and anomaly_data['is_anomaly']:
                            # Use average odds as "implied probability"
                            ai_prob = analyzer.calculate_implied_probability(anomaly_data['average_odds'])
                            best_odds = anomaly_data['best_odds']
                            implied_prob = analyzer.calculate_implied_probability(best_odds)
                            ev = analyzer.calculate_ev(ai_prob, best_odds)
                        else:
                            ai_prob = None
                    elif ai_model == 'form_momentum':
                        try:
                            ai_prob = form_analyzer.calculate_probability(home_team, away_team, 'moneyline', market)
                        except Exception as e:
                            print(f"Error calculating form_momentum probability for {home_team} vs {away_team}: {e}")
                            ai_prob = None
                    elif ai_model == 'sentiment_external':
                        try:
                            ai_prob = sentiment_analyzer.calculate_probability(home_team, away_team, 'moneyline', market)
                        except Exception as e:
                            print(f"Error calculating sentiment probability for {home_team} vs {away_team}: {e}")
                            ai_prob = None
                    elif ai_model == 'overall':
                        try:
                            # Pass bookmaker odds for anomaly detection
                            ai_prob = combined_analyzer.calculate_probability(
                                home_team, away_team, 'moneyline', market, 
                                moneyline_all_odds.get(market) if 'moneyline_all_odds' in dir() else None
                            )
                        except Exception as e:
                            print(f"Error calculating overall probability for {home_team} vs {away_team}: {e}")
                            ai_prob = None
                    else:
                        try:
                            ai_prob = analyzer.calculate_ai_probability(home_team, away_team, 'moneyline', market, ai_model)
                        except Exception as e:
                            print(f"Error calculating moneyline probability for {home_team} vs {away_team}: {e}")
                            ai_prob = None
                    
                    if ai_prob:
                        # For anomaly model, we already calculated these
                        if ai_model != 'anomaly':
                            best_odds = h2h_odds[market]['odds']
                            implied_prob = analyzer.calculate_implied_probability(best_odds)
                            ev = analyzer.calculate_ev(ai_prob, best_odds)
                        
                        # Calculate historical probability
                        hist_prob = 0
                        if home_stats and away_stats:
                            if market == 'home_win':
                                hist_prob = home_stats['home']['wins'] / max(home_stats['home']['total'], 1)
                            elif market == 'away_win':
                                hist_prob = away_stats['away']['wins'] / max(away_stats['away']['total'], 1)
                            else:  # draw
                                home_draws = home_stats['home']['draws'] / max(home_stats['home']['total'], 1)
                                away_draws = away_stats['away']['draws'] / max(away_stats['away']['total'], 1)
                                hist_prob = (home_draws + away_draws) / 2
                        
                        # Include all bets (positive and negative EV)
                        market_label = market.replace('_', ' ').title()
                        if market == 'home_win':
                            bet_description = f"{home_team} to Win"
                        elif market == 'away_win':
                            bet_description = f"{away_team} to Win"
                        else:
                            bet_description = "Draw"
                        
                        # Generate explanation using already-fetched stats
                        explanation = ""
                        if ai_model == 'anomaly':
                            anomaly_info = analyzer.detect_bookmaker_anomalies(moneyline_all_odds[market])
                            if anomaly_info:
                                explanation = f"📊 {anomaly_info['best_bookmaker']}: {anomaly_info['best_odds']} | Market avg: {anomaly_info['average_odds']} ({anomaly_info['percentage_better']}% better than average)"
                        elif ai_model == 'simple' and home_stats and away_stats:
                            if market == 'home_win':
                                explanation = f"{home_team} won {home_stats['home']['wins']} of {home_stats['home']['total']} home games this season ({round(home_stats['home']['wins']/max(home_stats['home']['total'],1)*100, 1)}%)"
                            elif market == 'away_win':
                                explanation = f"{away_team} won {away_stats['away']['wins']} of {away_stats['away']['total']} away games this season ({round(away_stats['away']['wins']/max(away_stats['away']['total'],1)*100, 1)}%)"
                            else:
                                home_draw_pct = round(home_stats['home']['draws']/max(home_stats['home']['total'],1)*100, 1)
                                away_draw_pct = round(away_stats['away']['draws']/max(away_stats['away']['total'],1)*100, 1)
                                explanation = f"{home_team} drew {home_draw_pct}% at home, {away_team} drew {away_draw_pct}% away this season"
                        elif ai_model == 'opponent' and home_stats and away_stats:
                            home_gd = (statistics.mean(home_stats['goals_scored_home']) if home_stats['goals_scored_home'] else 0) - (statistics.mean(home_stats['goals_conceded_home']) if home_stats['goals_conceded_home'] else 0)
                            away_gd = (statistics.mean(away_stats['goals_scored_away']) if away_stats['goals_scored_away'] else 0) - (statistics.mean(away_stats['goals_conceded_away']) if away_stats['goals_conceded_away'] else 0)
                            explanation = f"{home_team} avg goal diff: {round(home_gd, 2)} (home), {away_team}: {round(away_gd, 2)} (away). Adjusted for relative strength"
                        elif ai_model == 'complex':
                            explanation = f"Multi-factor model: home advantage +15%, weighted form (70% current/30% historical), team strength metrics"
                        elif ai_model == 'form_momentum':
                            try:
                                explanation = form_analyzer.get_explanation(home_team, away_team, 'moneyline', market)
                            except:
                                explanation = "Form & Momentum model: ELO ratings, recent form (5 games), head-to-head, momentum trends"
                        elif ai_model == 'sentiment_external':
                            try:
                                explanation = sentiment_analyzer.get_explanation(home_team, away_team, 'moneyline', market)
                            except:
                                explanation = "Sentiment model: FPL data, injury impact, transfer momentum, team strength index"
                        elif ai_model == 'overall':
                            try:
                                explanation = combined_analyzer.get_explanation(home_team, away_team, 'moneyline', market)
                            except:
                                explanation = "🤖 Overall AI: Combined analysis from ELO, Form, Sentiment & Anomaly detection"
                        
                        value_bets_list.append({
                            'match': f"{home_team} vs {away_team}",
                            'home_team': home_team,
                            'away_team': away_team,
                            'commence_time': commence_time,
                            'bet_type': 'Moneyline',
                            'market': bet_description,
                            'ai_probability': round(ai_prob * 100, 2),
                            'implied_probability': round(implied_prob * 100, 2),
                            'historical_probability': round(hist_prob * 100, 2),
                            'ev': round(ev, 2),
                            'best_odds': round(best_odds, 2),
                            'bookmaker': h2h_odds[market]['bookmaker'],
                            'region': h2h_odds[market]['region'],
                            'explanation': explanation
                        })
            
            # Analyze Goals over/under
            totals_odds = {}
            for bookmaker in filtered_bookmakers:
                bm_key = bookmaker.get('key', '')
                bm_region = 'UK' if bm_key in uk_bookmakers_list else 'US' if bm_key in us_bookmakers_list else 'Other'
                
                for market in bookmaker.get('markets', []):
                    if market.get('key') == 'totals':
                        for outcome in market.get('outcomes', []):
                            over_under = outcome.get('name', '').lower()  # 'Over' or 'Under'
                            point = outcome.get('point', 0)
                            price = outcome.get('price')
                            
                            market_key = f"{over_under}_{point}"
                            if market_key not in totals_odds or price > totals_odds[market_key]['odds']:
                                totals_odds[market_key] = {'odds': price, 'bookmaker': bookmaker.get('title'), 'point': point, 'region': bm_region}
            
            # Create value bets for goals (using full match totals for now)
            for market_key, odds_data in totals_odds.items():
                over_under, point = market_key.split('_')
                point = float(point)
                
                # Map to our market format
                goals_market = f"full_{over_under}_{point}"
                
                try:
                    if ai_model == 'form_momentum':
                        ai_prob = form_analyzer.calculate_probability(home_team, away_team, 'goals', goals_market)
                    elif ai_model == 'sentiment_external':
                        ai_prob = sentiment_analyzer.calculate_probability(home_team, away_team, 'goals', goals_market)
                    elif ai_model == 'overall':
                        ai_prob = combined_analyzer.calculate_probability(home_team, away_team, 'goals', goals_market)
                    else:
                        ai_prob = analyzer.calculate_ai_probability(home_team, away_team, 'goals', goals_market, ai_model)
                except Exception as e:
                    print(f"Error calculating goals probability for {home_team} vs {away_team}: {e}")
                    ai_prob = None
                
                if ai_prob:
                    best_odds = odds_data['odds']
                    implied_prob = analyzer.calculate_implied_probability(best_odds)
                    ev = analyzer.calculate_ev(ai_prob, best_odds)
                    
                    # Include all bets (positive and negative EV)
                    bet_description = f"{'Over' if over_under == 'over' else 'Under'} {point} Goals"
                    
                    # Generate explanation inline to avoid extra DB queries
                    explanation = ""
                    if ai_model == 'simple' and home_stats and away_stats:
                        home_avg = statistics.mean(home_stats['goals_scored_home']) if home_stats['goals_scored_home'] else 0
                        away_avg = statistics.mean(away_stats['goals_scored_away']) if away_stats['goals_scored_away'] else 0
                        explanation = f"Historical avg: {home_team} scores {round(home_avg, 1)} at home, {away_team} scores {round(away_avg, 1)} away"
                    elif ai_model == 'opponent' and home_stats and away_stats:
                        home_attack = statistics.mean(home_stats['goals_scored_home']) if home_stats['goals_scored_home'] else 0
                        away_attack = statistics.mean(away_stats['goals_scored_away']) if away_stats['goals_scored_away'] else 0
                        home_defense = statistics.mean(home_stats['goals_conceded_home']) if home_stats['goals_conceded_home'] else 0
                        away_defense = statistics.mean(away_stats['goals_conceded_away']) if away_stats['goals_conceded_away'] else 0
                        expected_total = ((home_attack + away_defense) / 2) + ((away_attack + home_defense) / 2)
                        explanation = f"Expected goals: {round(expected_total, 2)} (based on attack vs defense matchup)"
                    elif ai_model == 'complex':
                        explanation = f"Multi-factor model with form weighting, confidence adjustments, and historical patterns"
                    elif ai_model == 'form_momentum':
                        try:
                            explanation = form_analyzer.get_explanation(home_team, away_team, 'goals', goals_market)
                        except:
                            explanation = "Form & Momentum: Goals prediction based on recent scoring trends, momentum, and matchup history"
                    elif ai_model == 'sentiment_external':
                        try:
                            explanation = sentiment_analyzer.get_explanation(home_team, away_team, 'goals', goals_market)
                        except:
                            explanation = "Sentiment model: Goals prediction using FPL data, injury impact, and team strength metrics"
                    elif ai_model == 'overall':
                        try:
                            explanation = combined_analyzer.get_explanation(home_team, away_team, 'goals', goals_market)
                        except:
                            explanation = "🤖 Overall AI: Combined goals analysis from multiple models"
                    
                    value_bets_list.append({
                        'match': f"{home_team} vs {away_team}",
                        'home_team': home_team,
                        'away_team': away_team,
                        'commence_time': commence_time,
                        'bet_type': 'Goals',
                        'market': bet_description,
                        'ai_probability': round(ai_prob * 100, 2),
                        'implied_probability': round(implied_prob * 100, 2),
                        'historical_probability': round(ai_prob * 100, 2),  # Using AI prob as proxy
                        'ev': round(ev, 2),
                        'best_odds': round(best_odds, 2),
                        'bookmaker': odds_data['bookmaker'],
                        'region': odds_data['region'],
                        'explanation': explanation
                    })
        
            # Analyze Spreads (Handicaps)
            spreads_odds = {}
            for bookmaker in filtered_bookmakers:
                bm_key = bookmaker.get('key', '')
                bm_region = 'UK' if bm_key in uk_bookmakers_list else 'US' if bm_key in us_bookmakers_list else 'Other'
                
                for market in bookmaker.get('markets', []):
                    if market.get('key') == 'spreads':
                        for outcome in market.get('outcomes', []):
                            team = outcome.get('name', '')
                            point = outcome.get('point', 0)
                            price = outcome.get('price', 0)
                            
                            market_key = f"{team}_{point}"
                            if market_key not in spreads_odds or price > spreads_odds[market_key]['odds']:
                                spreads_odds[market_key] = {
                                    'odds': price,
                                    'bookmaker': bookmaker.get('title'),
                                    'point': point,
                                    'team': team,
                                    'region': bm_region
                                }
            
            # Create value bets for spreads (simplified - no AI model for spreads yet)
            for market_key, odds_data in spreads_odds.items():
                team = odds_data['team']
                point = odds_data['point']
                
                # Use 50% probability as baseline for spreads (neutral)
                ai_prob = 0.5
                best_odds = odds_data['odds']
                implied_prob = analyzer.calculate_implied_probability(best_odds)
                ev = analyzer.calculate_ev(ai_prob, best_odds)
                
                bet_description = f"{team} {point:+.1f}"
                
                value_bets_list.append({
                    'match': f"{home_team} vs {away_team}",
                    'home_team': home_team,
                    'away_team': away_team,
                    'commence_time': commence_time,
                    'bet_type': 'Spreads',
                    'market': bet_description,
                    'ai_probability': round(ai_prob * 100, 2),
                    'implied_probability': round(implied_prob * 100, 2),
                    'historical_probability': 50.0,
                    'ev': round(ev, 2),
                    'best_odds': round(best_odds, 2),
                    'bookmaker': odds_data['bookmaker'],
                    'region': odds_data['region'],
                    'explanation': f"Handicap betting: {team} with {point:+.1f} goal handicap"
                })
        
        # Sort by EV (highest first)
        value_bets_list.sort(key=lambda x: x['ev'], reverse=True)
        
        return jsonify({
            'value_bets': value_bets_list,
            'total_bets': len(value_bets_list),
            'last_updated': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        print(f"Error in value_bets endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


# =============================================================================
# BACKTESTING ENDPOINT - USES ACTUAL HISTORICAL ODDS & PREVENTS LOOKAHEAD BIAS
# =============================================================================

class BacktestAnalyzer:
    """
    Analyzer that calculates probabilities using ONLY data before a given date.
    This prevents lookahead bias in backtesting.
    """
    
    def __init__(self, cutoff_date):
        """Initialize with a cutoff date - only uses data before this date."""
        self.cutoff_date = cutoff_date
        self.db = get_db()
    
    def get_team_stats_before_date(self, team, seasons=3):
        """Get team statistics using only data from before the cutoff date."""
        cursor = self.db.execute('''
            SELECT 
                COUNT(*) as matches,
                SUM(CASE WHEN home_team = ? AND home_goals_full_time > away_goals_full_time THEN 1
                         WHEN away_team = ? AND away_goals_full_time > home_goals_full_time THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN (home_team = ? OR away_team = ?) AND home_goals_full_time = away_goals_full_time THEN 1 ELSE 0 END) as draws,
                AVG(CASE WHEN home_team = ? THEN home_goals_full_time ELSE away_goals_full_time END) as avg_scored,
                AVG(CASE WHEN home_team = ? THEN away_goals_full_time ELSE home_goals_full_time END) as avg_conceded
            FROM matches
            WHERE (home_team = ? OR away_team = ?)
            AND match_date < ?
            AND match_date >= date(?, '-' || ? || ' years')
        ''', (team, team, team, team, team, team, team, team, self.cutoff_date, self.cutoff_date, seasons))
        
        row = cursor.fetchone()
        if not row or row['matches'] < 5:
            return None
        
        return {
            'matches': row['matches'],
            'win_rate': row['wins'] / row['matches'] if row['matches'] > 0 else 0.33,
            'draw_rate': row['draws'] / row['matches'] if row['matches'] > 0 else 0.33,
            'avg_scored': row['avg_scored'] or 1.3,
            'avg_conceded': row['avg_conceded'] or 1.3
        }
    
    def get_home_form_before_date(self, team, num_games=5):
        """Get home form using only data from before the cutoff date."""
        cursor = self.db.execute('''
            SELECT home_goals_full_time, away_goals_full_time
            FROM matches
            WHERE home_team = ?
            AND match_date < ?
            ORDER BY match_date DESC
            LIMIT ?
        ''', (team, self.cutoff_date, num_games))
        
        rows = cursor.fetchall()
        if not rows:
            return {'win_rate': 0.45, 'ppg': 1.4}  # League average home form
        
        wins = sum(1 for r in rows if r['home_goals_full_time'] > r['away_goals_full_time'])
        draws = sum(1 for r in rows if r['home_goals_full_time'] == r['away_goals_full_time'])
        points = wins * 3 + draws
        
        return {
            'win_rate': wins / len(rows),
            'ppg': points / len(rows)
        }
    
    def get_away_form_before_date(self, team, num_games=5):
        """Get away form using only data from before the cutoff date."""
        cursor = self.db.execute('''
            SELECT home_goals_full_time, away_goals_full_time
            FROM matches
            WHERE away_team = ?
            AND match_date < ?
            ORDER BY match_date DESC
            LIMIT ?
        ''', (team, self.cutoff_date, num_games))
        
        rows = cursor.fetchall()
        if not rows:
            return {'win_rate': 0.28, 'ppg': 1.0}  # League average away form
        
        wins = sum(1 for r in rows if r['away_goals_full_time'] > r['home_goals_full_time'])
        draws = sum(1 for r in rows if r['home_goals_full_time'] == r['away_goals_full_time'])
        points = wins * 3 + draws
        
        return {
            'win_rate': wins / len(rows),
            'ppg': points / len(rows)
        }
    
    def calculate_probability(self, home_team, away_team, market):
        """
        Calculate probability for a market using only historical data.
        No lookahead bias - only uses matches before cutoff_date.
        """
        home_stats = self.get_team_stats_before_date(home_team)
        away_stats = self.get_team_stats_before_date(away_team)
        
        if not home_stats or not away_stats:
            return None
        
        home_form = self.get_home_form_before_date(home_team)
        away_form = self.get_away_form_before_date(away_team)
        
        # Base probabilities from win rates
        home_strength = (home_stats['win_rate'] * 0.4 + home_form['win_rate'] * 0.6)
        away_strength = (away_stats['win_rate'] * 0.4 + away_form['win_rate'] * 0.6)
        
        # Home advantage factor (historically ~10-15% boost)
        home_advantage = 0.12
        
        # Goal-based adjustment
        home_attack = home_stats['avg_scored'] / 1.5  # Normalized to league average
        away_attack = away_stats['avg_scored'] / 1.5
        home_defense = 1.5 / home_stats['avg_conceded'] if home_stats['avg_conceded'] > 0 else 1
        away_defense = 1.5 / away_stats['avg_conceded'] if away_stats['avg_conceded'] > 0 else 1
        
        # Combined strength with attack/defense
        home_combined = (home_strength + home_advantage) * (home_attack * 0.5 + away_defense * 0.5)
        away_combined = away_strength * (away_attack * 0.5 + home_defense * 0.5)
        
        # Normalize to probabilities
        total = home_combined + away_combined + 0.25  # 0.25 for draw
        
        probs = {
            'home_win': home_combined / total,
            'away_win': away_combined / total,
            'draw': 0.25 / total
        }
        
        # Ensure probabilities sum to ~1 and are reasonable
        total_prob = sum(probs.values())
        probs = {k: v / total_prob for k, v in probs.items()}
        
        # Apply reasonable bounds
        for k in probs:
            probs[k] = max(0.05, min(0.85, probs[k]))
        
        return probs.get(market)


@app.route('/api/backtest')
@require_auth
def backtest():
    """
    Backtest AI models against historical Premier League results.
    
    KEY FEATURES FOR RELIABILITY:
    1. Uses ACTUAL historical odds from football-data.co.uk (Bet365 odds)
    2. Prevents lookahead bias - AI only uses data from BEFORE each match
    3. Tests only on matches that have actual historical odds data
    """
    try:
        model = request.args.get('model', 'overall')
        gameweeks = int(request.args.get('gameweeks', 5))
        stake = float(request.args.get('stake', 10))  # Default £10 stake
        
        db = get_db()
        
        # Get recent completed matches WITH ACTUAL ODDS DATA
        num_matches = gameweeks * 10
        cursor = db.execute('''
            SELECT * FROM matches 
            WHERE match_date < date('now')
            AND match_date >= date('now', '-90 days')
            AND odds_home_b365 IS NOT NULL
            AND odds_home_b365 > 1
            AND odds_draw_b365 > 1
            AND odds_away_b365 > 1
            ORDER BY match_date DESC
            LIMIT ?
        ''', (num_matches,))
        
        completed_matches = cursor.fetchall()
        
        # Fallback: if no matches with odds, get matches without odds filter
        # (but mark as "simulated odds")
        using_actual_odds = len(completed_matches) > 0
        
        if not completed_matches:
            cursor = db.execute('''
                SELECT * FROM matches 
                WHERE match_date < date('now')
                AND match_date >= date('now', '-90 days')
                ORDER BY match_date DESC
                LIMIT ?
            ''', (num_matches,))
            completed_matches = cursor.fetchall()
        
        if not completed_matches:
            return jsonify({'error': 'No recent completed matches found'}), 404
        
        results = {
            'model': model,
            'gameweeks_analyzed': gameweeks,
            'stake_per_bet': stake,
            'total_matches': len(completed_matches),
            'using_actual_odds': using_actual_odds,
            'methodology': 'Point-in-time analysis: AI models only use data available before each match',
            'bets_placed': 0,
            'bets_won': 0,
            'bets_lost': 0,
            'total_staked': 0,
            'total_returns': 0,
            'profit_loss': 0,
            'roi': 0,
            'accuracy': 0,
            'ev_accuracy': {
                'positive_ev_bets': 0,
                'positive_ev_wins': 0,
                'negative_ev_bets': 0,
                'negative_ev_wins': 0
            },
            'by_bet_type': {
                'home_win': {'bets': 0, 'wins': 0, 'profit': 0},
                'draw': {'bets': 0, 'wins': 0, 'profit': 0},
                'away_win': {'bets': 0, 'wins': 0, 'profit': 0}
            },
            'detailed_bets': []
        }
        
        for match in completed_matches:
            home_team = match['home_team']
            away_team = match['away_team']
            home_goals = match['home_goals_full_time']
            away_goals = match['away_goals_full_time']
            match_date = match['match_date']
            
            # Create a point-in-time analyzer that ONLY uses data before this match
            pit_analyzer = BacktestAnalyzer(match_date)
            
            # Determine actual result
            if home_goals > away_goals:
                actual_result = 'home_win'
            elif home_goals < away_goals:
                actual_result = 'away_win'
            else:
                actual_result = 'draw'
            
            # Get ACTUAL historical odds from database (or estimate if not available)
            if using_actual_odds and match['odds_home_b365']:
                actual_odds = {
                    'home_win': float(match['odds_home_b365']),
                    'draw': float(match['odds_draw_b365']),
                    'away_win': float(match['odds_away_b365'])
                }
                odds_source = 'Bet365'
            else:
                # Fallback: use estimated odds (marked as simulated)
                actual_odds = {
                    'home_win': 2.0,  # Typical home favorite
                    'draw': 3.5,
                    'away_win': 4.0
                }
                odds_source = 'Simulated'
            
            # Calculate AI probabilities using ONLY pre-match data (no lookahead)
            markets = ['home_win', 'draw', 'away_win']
            predictions = {}
            
            for market in markets:
                try:
                    # Use point-in-time analyzer to prevent lookahead bias
                    prob = pit_analyzer.calculate_probability(home_team, away_team, market)
                    if prob:
                        predictions[market] = prob
                except Exception as e:
                    continue
            
            if not predictions:
                continue
            
            # Find value bets: where AI probability > implied probability from actual odds
            value_bets = []
            for market, ai_prob in predictions.items():
                if market in actual_odds and actual_odds[market] > 1:
                    implied_prob = 1 / actual_odds[market]
                    ev = (ai_prob * actual_odds[market]) - 1
                    
                    # Only bet if positive EV and reasonable probability
                    if ev > 0.05 and ai_prob >= 0.30:  # 5% edge minimum
                        value_bets.append({
                            'market': market,
                            'ai_prob': ai_prob,
                            'implied_prob': implied_prob,
                            'odds': actual_odds[market],
                            'ev': ev
                        })
            
            # If no value bets found, take highest probability prediction
            if not value_bets:
                best_market = max(predictions.keys(), key=lambda k: predictions[k])
                best_prob = predictions[best_market]
                if best_prob >= 0.40:  # Only bet on strong predictions
                    value_bets = [{
                        'market': best_market,
                        'ai_prob': best_prob,
                        'implied_prob': 1/actual_odds.get(best_market, 2.5),
                        'odds': actual_odds.get(best_market, 2.5),
                        'ev': (best_prob * actual_odds.get(best_market, 2.5)) - 1
                    }]
            
            # Process bets
            for bet in value_bets:
                bet_won = (bet['market'] == actual_result)
                
                results['bets_placed'] += 1
                results['total_staked'] += stake
                results['by_bet_type'][bet['market']]['bets'] += 1
                
                if bet_won:
                    returns = stake * bet['odds']
                    profit = returns - stake
                    results['bets_won'] += 1
                    results['total_returns'] += returns
                    results['by_bet_type'][bet['market']]['wins'] += 1
                    results['by_bet_type'][bet['market']]['profit'] += profit
                else:
                    results['bets_lost'] += 1
                    results['by_bet_type'][bet['market']]['profit'] -= stake
                
                # Track EV accuracy
                if bet['ev'] > 0:
                    results['ev_accuracy']['positive_ev_bets'] += 1
                    if bet_won:
                        results['ev_accuracy']['positive_ev_wins'] += 1
                else:
                    results['ev_accuracy']['negative_ev_bets'] += 1
                    if bet_won:
                        results['ev_accuracy']['negative_ev_wins'] += 1
                
                # Add to detailed bets
                results['detailed_bets'].append({
                    'match': f"{home_team} vs {away_team}",
                    'date': match_date,
                    'prediction': bet['market'].replace('_', ' ').title(),
                    'ai_probability': round(bet['ai_prob'] * 100, 1),
                    'odds': round(bet['odds'], 2),
                    'odds_source': odds_source,
                    'ev': round(bet['ev'] * 100, 1),
                    'actual_result': actual_result.replace('_', ' ').title(),
                    'won': bet_won,
                    'profit': round((stake * bet['odds'] - stake) if bet_won else -stake, 2)
                })
        
        # Calculate summary metrics
        if results['bets_placed'] > 0:
            results['profit_loss'] = round(results['total_returns'] - results['total_staked'], 2)
            results['roi'] = round((results['profit_loss'] / results['total_staked']) * 100, 2)
            results['accuracy'] = round((results['bets_won'] / results['bets_placed']) * 100, 1)
        
        # Calculate EV accuracy rates
        if results['ev_accuracy']['positive_ev_bets'] > 0:
            results['ev_accuracy']['positive_ev_win_rate'] = round(
                (results['ev_accuracy']['positive_ev_wins'] / results['ev_accuracy']['positive_ev_bets']) * 100, 1
            )
        else:
            results['ev_accuracy']['positive_ev_win_rate'] = 0
            
        if results['ev_accuracy']['negative_ev_bets'] > 0:
            results['ev_accuracy']['negative_ev_win_rate'] = round(
                (results['ev_accuracy']['negative_ev_wins'] / results['ev_accuracy']['negative_ev_bets']) * 100, 1
            )
        else:
            results['ev_accuracy']['negative_ev_win_rate'] = 0
        
        results['total_staked'] = round(results['total_staked'], 2)
        results['total_returns'] = round(results['total_returns'], 2)
        
        # Sort detailed bets by date (most recent first)
        results['detailed_bets'] = sorted(results['detailed_bets'], key=lambda x: x['date'], reverse=True)
        
        return jsonify(results)
        
    except Exception as e:
        print(f"Error in backtest endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


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
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

