from flask import Blueprint, jsonify, request
from src.models.user import Match, Odds, db
from src.odds_ingestion import OddsIngestionService, MatchClassificationService
import logging

logger = logging.getLogger(__name__)

matches_bp = Blueprint('matches', __name__)

@matches_bp.route('/matches', methods=['GET'])
def get_matches():
    """Get all current Major matches with latest odds"""
    try:
        # Get query parameters
        stage = request.args.get('stage')  # 'swiss' or 'playoffs'
        status = request.args.get('status')  # 'upcoming', 'live', 'completed'
        
        # Build query
        query = Match.query
        
        if stage:
            query = query.filter(Match.stage == stage)
        if status:
            query = query.filter(Match.status == status)
        
        matches = query.order_by(Match.scheduled_time).all()
        
        # Get latest odds for each match
        matches_data = []
        for match in matches:
            match_dict = match.to_dict()
            
            # Get latest odds from each source
            latest_odds = {}
            for odds in match.odds:
                if odds.is_active:
                    if odds.source not in latest_odds or odds.timestamp > latest_odds[odds.source].timestamp:
                        latest_odds[odds.source] = odds
            
            match_dict['latest_odds'] = {source: odds.to_dict() for source, odds in latest_odds.items()}
            match_dict['pick_count'] = len(match.picks)
            
            matches_data.append(match_dict)
        
        return jsonify({
            'success': True,
            'data': matches_data,
            'count': len(matches_data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching matches: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch matches'
        }), 500

@matches_bp.route('/matches/<match_id>', methods=['GET'])
def get_match(match_id):
    """Get detailed information for a specific match"""
    try:
        match = Match.query.get_or_404(match_id)
        match_dict = match.to_dict()
        
        # Include all odds history
        odds_history = []
        for odds in match.odds:
            odds_history.append(odds.to_dict())
        
        match_dict['odds_history'] = sorted(odds_history, key=lambda x: x['timestamp'], reverse=True)
        match_dict['pick_count'] = len(match.picks)
        
        # Calculate pick distribution
        team_a_picks = sum(1 for pick in match.picks if pick.selected_team == 'team_a')
        team_b_picks = sum(1 for pick in match.picks if pick.selected_team == 'team_b')
        total_picks = team_a_picks + team_b_picks
        
        if total_picks > 0:
            match_dict['pick_distribution'] = {
                'team_a_percentage': (team_a_picks / total_picks) * 100,
                'team_b_percentage': (team_b_picks / total_picks) * 100,
                'total_picks': total_picks
            }
        else:
            match_dict['pick_distribution'] = {
                'team_a_percentage': 0,
                'team_b_percentage': 0,
                'total_picks': 0
            }
        
        return jsonify({
            'success': True,
            'data': match_dict
        })
        
    except Exception as e:
        logger.error(f"Error fetching match {match_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Match not found'
        }), 404

@matches_bp.route('/matches/<match_id>/odds', methods=['GET'])
def get_match_odds(match_id):
    """Get odds history for a specific match"""
    try:
        match = Match.query.get_or_404(match_id)
        
        # Get query parameters
        source = request.args.get('source')
        limit = request.args.get('limit', type=int, default=50)
        
        # Build odds query
        odds_query = Odds.query.filter(Odds.match_id == match_id)
        
        if source:
            odds_query = odds_query.filter(Odds.source == source)
        
        odds = odds_query.order_by(Odds.timestamp.desc()).limit(limit).all()
        
        odds_data = [odds_item.to_dict() for odds_item in odds]
        
        return jsonify({
            'success': True,
            'data': odds_data,
            'match_info': {
                'id': match.id,
                'team_a': match.team_a,
                'team_b': match.team_b,
                'stage': match.stage
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching odds for match {match_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch odds'
        }), 500

@matches_bp.route('/matches/<match_id>/classification', methods=['POST'])
def override_match_classification(match_id):
    """Override the Safe/Unsafe classification for a match"""
    try:
        match = Match.query.get_or_404(match_id)
        data = request.get_json()
        
        if 'is_safe' not in data:
            return jsonify({
                'success': False,
                'error': 'is_safe field is required'
            }), 400
        
        # Update match classification
        match.is_safe = data['is_safe']
        
        if 'confidence_threshold' in data:
            match.confidence_threshold = data['confidence_threshold']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': match.to_dict(),
            'message': f"Match classification updated to {'Safe' if match.is_safe else 'Unsafe'}"
        })
        
    except Exception as e:
        logger.error(f"Error updating match classification {match_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to update classification'
        }), 500

@matches_bp.route('/matches/refresh-odds', methods=['POST'])
def refresh_odds():
    """Manually trigger odds refresh from all sources"""
    try:
        # Initialize odds ingestion service
        odds_service = OddsIngestionService()
        classification_service = MatchClassificationService()
        
        # Fetch fresh odds
        all_odds = odds_service.fetch_all_odds()
        
        # Process and save odds to database
        total_odds_saved = 0
        matches_updated = set()
        
        for source, odds_list in all_odds.items():
            for odds_data in odds_list:
                # Find or create match
                match = Match.query.filter_by(external_id=odds_data.match_id).first()
                
                if not match:
                    # Create new match if it doesn't exist
                    match = Match(
                        external_id=odds_data.match_id,
                        team_a=odds_data.team_a,
                        team_b=odds_data.team_b,
                        stage='swiss',  # Default to swiss, can be updated later
                        round_number=1,
                        scheduled_time=odds_data.timestamp,
                        status='upcoming'
                    )
                    db.session.add(match)
                    db.session.flush()  # Get the ID
                
                # Create new odds entry
                odds_entry = Odds(
                    match_id=match.id,
                    source=odds_data.source,
                    team_a_win_prob=odds_data.team_a_odds,
                    team_b_win_prob=odds_data.team_b_odds,
                    raw_data=odds_data.raw_data,
                    timestamp=odds_data.timestamp
                )
                
                db.session.add(odds_entry)
                total_odds_saved += 1
                matches_updated.add(match.id)
        
        # Classify matches based on new odds
        all_odds_flat = []
        for odds_list in all_odds.values():
            all_odds_flat.extend(odds_list)
        
        classifications = classification_service.classify_matches(all_odds_flat)
        
        # Update match classifications
        for external_id, classification in classifications.items():
            match = Match.query.filter_by(external_id=external_id).first()
            if match:
                match.is_safe = classification['is_safe']
                match.confidence_threshold = classification['implied_win_rate']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'odds_saved': total_odds_saved,
                'matches_updated': len(matches_updated),
                'matches_classified': len(classifications),
                'sources_used': list(all_odds.keys())
            },
            'message': 'Odds refreshed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error refreshing odds: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to refresh odds'
        }), 500

@matches_bp.route('/matches/classify', methods=['POST'])
def classify_all_matches():
    """Classify all matches as Safe or Unsafe based on current odds"""
    try:
        # Get all active matches
        matches = Match.query.filter(Match.status.in_(['upcoming', 'live'])).all()
        
        classification_service = MatchClassificationService()
        classified_count = 0
        
        for match in matches:
            # Get latest odds for this match
            latest_odds = {}
            for odds in match.odds:
                if odds.is_active:
                    if odds.source not in latest_odds or odds.timestamp > latest_odds[odds.source].timestamp:
                        latest_odds[odds.source] = odds
            
            if latest_odds:
                # Convert to OddsData format for classification
                from src.odds_ingestion import OddsData
                odds_data_list = []
                
                for source, odds in latest_odds.items():
                    odds_data_list.append(OddsData(
                        match_id=match.external_id,
                        team_a=match.team_a,
                        team_b=match.team_b,
                        team_a_odds=odds.team_a_win_prob,
                        team_b_odds=odds.team_b_win_prob,
                        source=source,
                        timestamp=odds.timestamp,
                        raw_data=odds.raw_data or {}
                    ))
                
                # Classify the match
                classification = classification_service._classify_single_match(odds_data_list)
                
                # Update match
                match.is_safe = classification['is_safe']
                match.confidence_threshold = classification['implied_win_rate']
                classified_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'matches_classified': classified_count,
                'total_matches': len(matches)
            },
            'message': f'Classified {classified_count} matches'
        })
        
    except Exception as e:
        logger.error(f"Error classifying matches: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to classify matches'
        }), 500

