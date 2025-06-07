import requests
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class OddsData:
    """Structure for odds data from external sources"""
    match_id: str
    team_a: str
    team_b: str
    team_a_odds: float
    team_b_odds: float
    source: str
    timestamp: datetime
    raw_data: Dict

class OddsIngestionService:
    """Service for ingesting odds from multiple sources"""
    
    def __init__(self):
        self.sources = {
            'hltv_elo': self._fetch_hltv_elo,
            'bookmaker_consensus': self._fetch_bookmaker_consensus,
            'community_picks': self._fetch_community_picks,
            'mock_data': self._fetch_mock_data  # For development/testing
        }
        self.cache = {}
        self.cache_duration = timedelta(minutes=15)
    
    def fetch_all_odds(self, match_ids: List[str] = None) -> Dict[str, List[OddsData]]:
        """
        Fetch odds from all configured sources
        
        Args:
            match_ids: Optional list of specific match IDs to fetch
            
        Returns:
            Dictionary mapping source names to lists of odds data
        """
        all_odds = {}
        
        for source_name, fetch_func in self.sources.items():
            try:
                logger.info(f"Fetching odds from {source_name}")
                odds_data = fetch_func(match_ids)
                all_odds[source_name] = odds_data
                
                # Cache the results
                cache_key = f"{source_name}_{int(time.time() // 900)}"  # 15-minute buckets
                self.cache[cache_key] = {
                    'data': odds_data,
                    'timestamp': datetime.utcnow()
                }
                
            except Exception as e:
                logger.error(f"Failed to fetch odds from {source_name}: {str(e)}")
                all_odds[source_name] = []
        
        return all_odds
    
    def get_cached_odds(self, source: str) -> Optional[List[OddsData]]:
        """Get cached odds data if available and fresh"""
        cache_key = f"{source}_{int(time.time() // 900)}"
        
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.utcnow() - cached['timestamp'] < self.cache_duration:
                return cached['data']
        
        return None
    
    def _fetch_hltv_elo(self, match_ids: List[str] = None) -> List[OddsData]:
        """
        Fetch ELO-based odds from HLTV or similar source
        
        Note: This is a placeholder implementation. In production, you would:
        1. Use HLTV's API or scrape their rankings
        2. Calculate ELO-based win probabilities
        3. Handle rate limiting and authentication
        """
        
        # Mock HLTV ELO data
        mock_elo_ratings = {
            'G2': 1850,
            'FaZe': 1820,
            'NAVI': 1800,
            'Astralis': 1750,
            'Vitality': 1730,
            'Liquid': 1700,
            'NIP': 1650,
            'Heroic': 1620,
            'FURIA': 1600
        }
        
        odds_data = []
        
        # Generate mock matches for demonstration
        mock_matches = [
            {'id': 'match_1', 'team_a': 'G2', 'team_b': 'FaZe'},
            {'id': 'match_2', 'team_a': 'NAVI', 'team_b': 'Astralis'},
            {'id': 'match_3', 'team_a': 'Vitality', 'team_b': 'Liquid'},
            {'id': 'match_4', 'team_a': 'NIP', 'team_b': 'Heroic'},
            {'id': 'match_5', 'team_a': 'FURIA', 'team_b': 'G2'}
        ]
        
        for match in mock_matches:
            if match_ids and match['id'] not in match_ids:
                continue
                
            team_a_elo = mock_elo_ratings.get(match['team_a'], 1500)
            team_b_elo = mock_elo_ratings.get(match['team_b'], 1500)
            
            # Calculate win probability using ELO formula
            team_a_win_prob = 1 / (1 + 10 ** ((team_b_elo - team_a_elo) / 400))
            team_b_win_prob = 1 - team_a_win_prob
            
            odds_data.append(OddsData(
                match_id=match['id'],
                team_a=match['team_a'],
                team_b=match['team_b'],
                team_a_odds=team_a_win_prob,
                team_b_odds=team_b_win_prob,
                source='hltv_elo',
                timestamp=datetime.utcnow(),
                raw_data={
                    'team_a_elo': team_a_elo,
                    'team_b_elo': team_b_elo,
                    'elo_difference': team_a_elo - team_b_elo
                }
            ))
        
        return odds_data
    
    def _fetch_bookmaker_consensus(self, match_ids: List[str] = None) -> List[OddsData]:
        """
        Fetch consensus odds from multiple bookmakers
        
        Note: This would integrate with odds comparison APIs like:
        - OddsAPI
        - BetExplorer
        - Pinnacle API
        """
        
        # Mock bookmaker data
        mock_bookmaker_odds = [
            {
                'match_id': 'match_1',
                'team_a': 'G2',
                'team_b': 'FaZe',
                'bookmakers': [
                    {'name': 'Pinnacle', 'team_a_decimal': 1.85, 'team_b_decimal': 1.95},
                    {'name': 'Bet365', 'team_a_decimal': 1.80, 'team_b_decimal': 2.00},
                    {'name': 'Betway', 'team_a_decimal': 1.88, 'team_b_decimal': 1.92}
                ]
            },
            {
                'match_id': 'match_2',
                'team_a': 'NAVI',
                'team_b': 'Astralis',
                'bookmakers': [
                    {'name': 'Pinnacle', 'team_a_decimal': 1.65, 'team_b_decimal': 2.25},
                    {'name': 'Bet365', 'team_a_decimal': 1.70, 'team_b_decimal': 2.15},
                    {'name': 'Betway', 'team_a_decimal': 1.68, 'team_b_decimal': 2.20}
                ]
            }
        ]
        
        odds_data = []
        
        for match_data in mock_bookmaker_odds:
            if match_ids and match_data['match_id'] not in match_ids:
                continue
            
            # Calculate consensus odds (average)
            team_a_decimals = [bm['team_a_decimal'] for bm in match_data['bookmakers']]
            team_b_decimals = [bm['team_b_decimal'] for bm in match_data['bookmakers']]
            
            avg_team_a_decimal = sum(team_a_decimals) / len(team_a_decimals)
            avg_team_b_decimal = sum(team_b_decimals) / len(team_b_decimals)
            
            # Convert to probabilities
            team_a_prob = 1 / avg_team_a_decimal
            team_b_prob = 1 / avg_team_b_decimal
            
            # Normalize to remove margin
            total_prob = team_a_prob + team_b_prob
            team_a_win_prob = team_a_prob / total_prob
            team_b_win_prob = team_b_prob / total_prob
            
            odds_data.append(OddsData(
                match_id=match_data['match_id'],
                team_a=match_data['team_a'],
                team_b=match_data['team_b'],
                team_a_odds=team_a_win_prob,
                team_b_odds=team_b_win_prob,
                source='bookmaker_consensus',
                timestamp=datetime.utcnow(),
                raw_data={
                    'bookmakers': match_data['bookmakers'],
                    'consensus_decimal_a': avg_team_a_decimal,
                    'consensus_decimal_b': avg_team_b_decimal
                }
            ))
        
        return odds_data
    
    def _fetch_community_picks(self, match_ids: List[str] = None) -> List[OddsData]:
        """
        Fetch community pick percentages from Steam or community sites
        
        Note: This would integrate with:
        - Steam Web API for Pick'Em statistics
        - Community sites like HLTV pick percentages
        - Reddit/Discord polling data
        """
        
        # Mock community pick data
        mock_community_data = [
            {
                'match_id': 'match_1',
                'team_a': 'G2',
                'team_b': 'FaZe',
                'team_a_pick_percentage': 52.3,
                'team_b_pick_percentage': 47.7,
                'total_picks': 15420
            },
            {
                'match_id': 'match_2',
                'team_a': 'NAVI',
                'team_b': 'Astralis',
                'team_a_pick_percentage': 68.1,
                'team_b_pick_percentage': 31.9,
                'total_picks': 18750
            }
        ]
        
        odds_data = []
        
        for match_data in mock_community_data:
            if match_ids and match_data['match_id'] not in match_ids:
                continue
            
            # Convert percentages to probabilities
            team_a_win_prob = match_data['team_a_pick_percentage'] / 100
            team_b_win_prob = match_data['team_b_pick_percentage'] / 100
            
            odds_data.append(OddsData(
                match_id=match_data['match_id'],
                team_a=match_data['team_a'],
                team_b=match_data['team_b'],
                team_a_odds=team_a_win_prob,
                team_b_odds=team_b_win_prob,
                source='community_picks',
                timestamp=datetime.utcnow(),
                raw_data={
                    'total_picks': match_data['total_picks'],
                    'team_a_percentage': match_data['team_a_pick_percentage'],
                    'team_b_percentage': match_data['team_b_pick_percentage']
                }
            ))
        
        return odds_data
    
    def _fetch_mock_data(self, match_ids: List[str] = None) -> List[OddsData]:
        """Generate mock odds data for development and testing"""
        
        import random
        
        mock_matches = [
            {'id': 'swiss_1_1', 'team_a': 'G2', 'team_b': 'FaZe'},
            {'id': 'swiss_1_2', 'team_a': 'NAVI', 'team_b': 'Astralis'},
            {'id': 'swiss_1_3', 'team_a': 'Vitality', 'team_b': 'Team Liquid'},
            {'id': 'swiss_1_4', 'team_a': 'NIP', 'team_b': 'Heroic'},
            {'id': 'swiss_1_5', 'team_a': 'FURIA', 'team_b': 'Cloud9'},
            {'id': 'swiss_1_6', 'team_a': 'MOUZ', 'team_b': 'Spirit'},
            {'id': 'swiss_1_7', 'team_a': 'Eternal Fire', 'team_b': 'ENCE'},
            {'id': 'swiss_1_8', 'team_a': 'BIG', 'team_b': 'Complexity'},
            {'id': 'swiss_1_9', 'team_a': 'Apeks', 'team_b': 'Imperial'}
        ]
        
        odds_data = []
        
        for match in mock_matches:
            if match_ids and match['id'] not in match_ids:
                continue
            
            # Generate realistic but random odds
            # Bias towards one team to create "safe" and "unsafe" matches
            bias = random.uniform(0.1, 0.4)
            if random.random() > 0.5:
                team_a_win_prob = 0.5 + bias
            else:
                team_a_win_prob = 0.5 - bias
            
            team_b_win_prob = 1 - team_a_win_prob
            
            odds_data.append(OddsData(
                match_id=match['id'],
                team_a=match['team_a'],
                team_b=match['team_b'],
                team_a_odds=team_a_win_prob,
                team_b_odds=team_b_win_prob,
                source='mock_data',
                timestamp=datetime.utcnow(),
                raw_data={
                    'generated': True,
                    'bias_applied': bias,
                    'random_seed': random.getstate()[1][0]
                }
            ))
        
        return odds_data

class MatchClassificationService:
    """Service for classifying matches as Safe or Unsafe"""
    
    def __init__(self, safe_threshold: float = 0.75):
        self.safe_threshold = safe_threshold
    
    def classify_matches(self, odds_data: List[OddsData]) -> Dict[str, Dict]:
        """
        Classify matches based on implied win rates
        
        Args:
            odds_data: List of odds data from various sources
            
        Returns:
            Dictionary mapping match IDs to classification data
        """
        classifications = {}
        
        # Group odds by match ID
        matches_odds = {}
        for odds in odds_data:
            if odds.match_id not in matches_odds:
                matches_odds[odds.match_id] = []
            matches_odds[odds.match_id].append(odds)
        
        # Classify each match
        for match_id, match_odds in matches_odds.items():
            classification = self._classify_single_match(match_odds)
            classifications[match_id] = classification
        
        return classifications
    
    def _classify_single_match(self, match_odds: List[OddsData]) -> Dict:
        """Classify a single match based on multiple odds sources"""
        
        if not match_odds:
            return {
                'is_safe': False,
                'confidence': 0.0,
                'implied_win_rate': 0.5,
                'consensus_favorite': None,
                'source_agreement': 0.0
            }
        
        # Calculate consensus odds (weighted average)
        weights = {
            'bookmaker_consensus': 0.4,
            'hltv_elo': 0.3,
            'community_picks': 0.2,
            'mock_data': 0.1
        }
        
        weighted_team_a_prob = 0
        weighted_team_b_prob = 0
        total_weight = 0
        
        favorites = []
        
        for odds in match_odds:
            weight = weights.get(odds.source, 0.1)
            weighted_team_a_prob += odds.team_a_odds * weight
            weighted_team_b_prob += odds.team_b_odds * weight
            total_weight += weight
            
            # Track which team each source favors
            if odds.team_a_odds > odds.team_b_odds:
                favorites.append(odds.team_a)
            else:
                favorites.append(odds.team_b)
        
        # Normalize
        if total_weight > 0:
            consensus_team_a_prob = weighted_team_a_prob / total_weight
            consensus_team_b_prob = weighted_team_b_prob / total_weight
        else:
            consensus_team_a_prob = 0.5
            consensus_team_b_prob = 0.5
        
        # Determine consensus favorite
        if consensus_team_a_prob > consensus_team_b_prob:
            consensus_favorite = match_odds[0].team_a
            implied_win_rate = consensus_team_a_prob
        else:
            consensus_favorite = match_odds[0].team_b
            implied_win_rate = consensus_team_b_prob
        
        # Calculate source agreement (what percentage of sources agree on favorite)
        if favorites:
            most_common_favorite = max(set(favorites), key=favorites.count)
            source_agreement = favorites.count(most_common_favorite) / len(favorites)
        else:
            source_agreement = 0.0
        
        # Classify as safe/unsafe
        is_safe = implied_win_rate >= self.safe_threshold
        confidence = min(implied_win_rate, 1 - implied_win_rate) * 2  # Distance from 50/50
        
        return {
            'is_safe': is_safe,
            'confidence': confidence,
            'implied_win_rate': implied_win_rate,
            'consensus_favorite': consensus_favorite,
            'source_agreement': source_agreement,
            'consensus_team_a_prob': consensus_team_a_prob,
            'consensus_team_b_prob': consensus_team_b_prob,
            'sources_count': len(match_odds)
        }

def create_odds_ingestion_job():
    """Create a background job for periodic odds ingestion"""
    
    def run_ingestion():
        """Main ingestion function to be run periodically"""
        try:
            logger.info("Starting odds ingestion job")
            
            # Initialize services
            odds_service = OddsIngestionService()
            classification_service = MatchClassificationService()
            
            # Fetch odds from all sources
            all_odds = odds_service.fetch_all_odds()
            
            # Flatten odds data
            all_odds_flat = []
            for source_odds in all_odds.values():
                all_odds_flat.extend(source_odds)
            
            # Classify matches
            classifications = classification_service.classify_matches(all_odds_flat)
            
            # Here you would save to database
            # For now, just log the results
            logger.info(f"Ingested odds for {len(all_odds_flat)} match-source combinations")
            logger.info(f"Classified {len(classifications)} matches")
            
            return {
                'success': True,
                'odds_count': len(all_odds_flat),
                'matches_classified': len(classifications),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Odds ingestion job failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    return run_ingestion

