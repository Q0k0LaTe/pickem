from flask import Blueprint, jsonify, request
from src.models.user import Pick, Match, User, db
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

picks_bp = Blueprint('picks', __name__)

@picks_bp.route('/picks/<user_id>', methods=['GET'])
def get_user_picks(user_id):
    """Get all picks for a user"""
    try:
        # Validate user exists
        user = User.query.get_or_404(user_id)
        
        # Get query parameters
        match_id = request.args.get('match_id')
        pick_type = request.args.get('pick_type')
        is_locked = request.args.get('is_locked', type=bool)
        
        # Build query
        query = Pick.query.filter(Pick.user_id == user_id)
        
        if match_id:
            query = query.filter(Pick.match_id == match_id)
        if pick_type:
            query = query.filter(Pick.pick_type == pick_type)
        if is_locked is not None:
            query = query.filter(Pick.is_locked == is_locked)
        
        picks = query.order_by(Pick.created_at.desc()).all()
        
        # Enhance picks with match information
        picks_data = []
        for pick in picks:
            pick_dict = pick.to_dict()
            
            # Add match details
            match = Match.query.get(pick.match_id)
            if match:
                pick_dict['match_info'] = {
                    'team_a': match.team_a,
                    'team_b': match.team_b,
                    'stage': match.stage,
                    'scheduled_time': match.scheduled_time.isoformat() if match.scheduled_time else None,
                    'status': match.status,
                    'is_safe': match.is_safe
                }
            
            picks_data.append(pick_dict)
        
        return jsonify({
            'success': True,
            'data': picks_data,
            'count': len(picks_data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching picks for user {user_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch picks'
        }), 500

@picks_bp.route('/picks', methods=['POST'])
def create_or_update_pick():
    """Create a new pick or update an existing one"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'match_id', 'selected_team']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        user_id = data['user_id']
        match_id = data['match_id']
        selected_team = data['selected_team']
        
        # Validate selected_team
        if selected_team not in ['team_a', 'team_b']:
            return jsonify({
                'success': False,
                'error': 'selected_team must be either "team_a" or "team_b"'
            }), 400
        
        # Validate user and match exist
        user = User.query.get_or_404(user_id)
        match = Match.query.get_or_404(match_id)
        
        # Check if match is still open for picks
        if match.status not in ['upcoming', 'live']:
            return jsonify({
                'success': False,
                'error': 'Cannot pick for completed or cancelled matches'
            }), 400
        
        # Check if pick already exists
        existing_pick = Pick.query.filter_by(user_id=user_id, match_id=match_id).first()
        
        if existing_pick:
            # Check if pick is locked
            if existing_pick.is_locked:
                return jsonify({
                    'success': False,
                    'error': 'Pick is locked and cannot be modified'
                }), 400
            
            # Update existing pick
            existing_pick.selected_team = selected_team
            existing_pick.confidence = data.get('confidence', existing_pick.confidence)
            existing_pick.pick_type = data.get('pick_type', existing_pick.pick_type)
            existing_pick.updated_at = datetime.utcnow()
            
            pick = existing_pick
            action = 'updated'
        else:
            # Create new pick
            pick = Pick(
                user_id=user_id,
                match_id=match_id,
                selected_team=selected_team,
                confidence=data.get('confidence', 0.5),
                pick_type=data.get('pick_type', 'manual'),
                template_id=data.get('template_id')
            )
            
            db.session.add(pick)
            action = 'created'
        
        db.session.commit()
        
        # Return enhanced pick data
        pick_dict = pick.to_dict()
        pick_dict['match_info'] = {
            'team_a': match.team_a,
            'team_b': match.team_b,
            'stage': match.stage,
            'status': match.status
        }
        
        return jsonify({
            'success': True,
            'data': pick_dict,
            'message': f'Pick {action} successfully'
        }), 201 if action == 'created' else 200
        
    except Exception as e:
        logger.error(f"Error creating/updating pick: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to save pick'
        }), 500

@picks_bp.route('/picks/<pick_id>', methods=['PUT'])
def update_pick(pick_id):
    """Update a specific pick"""
    try:
        pick = Pick.query.get_or_404(pick_id)
        data = request.get_json()
        
        # Check if pick is locked
        if pick.is_locked:
            return jsonify({
                'success': False,
                'error': 'Pick is locked and cannot be modified'
            }), 400
        
        # Check if match is still open
        match = Match.query.get(pick.match_id)
        if match and match.status not in ['upcoming', 'live']:
            return jsonify({
                'success': False,
                'error': 'Cannot modify pick for completed or cancelled matches'
            }), 400
        
        # Update allowed fields
        if 'selected_team' in data:
            if data['selected_team'] not in ['team_a', 'team_b']:
                return jsonify({
                    'success': False,
                    'error': 'selected_team must be either "team_a" or "team_b"'
                }), 400
            pick.selected_team = data['selected_team']
        
        if 'confidence' in data:
            pick.confidence = data['confidence']
        
        if 'pick_type' in data:
            pick.pick_type = data['pick_type']
        
        pick.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': pick.to_dict(),
            'message': 'Pick updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating pick {pick_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to update pick'
        }), 500

@picks_bp.route('/picks/<pick_id>', methods=['DELETE'])
def delete_pick(pick_id):
    """Delete a specific pick"""
    try:
        pick = Pick.query.get_or_404(pick_id)
        
        # Check if pick is locked
        if pick.is_locked:
            return jsonify({
                'success': False,
                'error': 'Pick is locked and cannot be deleted'
            }), 400
        
        # Check if match is still open
        match = Match.query.get(pick.match_id)
        if match and match.status not in ['upcoming', 'live']:
            return jsonify({
                'success': False,
                'error': 'Cannot delete pick for completed or cancelled matches'
            }), 400
        
        db.session.delete(pick)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Pick deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting pick {pick_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to delete pick'
        }), 500

@picks_bp.route('/picks/bulk', methods=['POST'])
def bulk_create_picks():
    """Create multiple picks at once (e.g., from optimization result)"""
    try:
        data = request.get_json()
        
        user_id = data.get('user_id')
        picks_data = data.get('picks', [])
        pick_type = data.get('pick_type', 'optimized')
        
        if not user_id or not picks_data:
            return jsonify({
                'success': False,
                'error': 'user_id and picks are required'
            }), 400
        
        # Validate user exists
        user = User.query.get_or_404(user_id)
        
        created_picks = []
        updated_picks = []
        errors = []
        
        for pick_data in picks_data:
            try:
                match_id = pick_data.get('match_id')
                selected_team = pick_data.get('selected_team')
                confidence = pick_data.get('confidence', 0.5)
                
                if not match_id or not selected_team:
                    errors.append(f"Missing match_id or selected_team in pick data")
                    continue
                
                # Validate match exists and is open
                match = Match.query.get(match_id)
                if not match:
                    errors.append(f"Match {match_id} not found")
                    continue
                
                if match.status not in ['upcoming', 'live']:
                    errors.append(f"Match {match_id} is not open for picks")
                    continue
                
                # Check if pick already exists
                existing_pick = Pick.query.filter_by(user_id=user_id, match_id=match_id).first()
                
                if existing_pick:
                    if existing_pick.is_locked:
                        errors.append(f"Pick for match {match_id} is locked")
                        continue
                    
                    # Update existing pick
                    existing_pick.selected_team = selected_team
                    existing_pick.confidence = confidence
                    existing_pick.pick_type = pick_type
                    existing_pick.updated_at = datetime.utcnow()
                    updated_picks.append(existing_pick.to_dict())
                else:
                    # Create new pick
                    new_pick = Pick(
                        user_id=user_id,
                        match_id=match_id,
                        selected_team=selected_team,
                        confidence=confidence,
                        pick_type=pick_type
                    )
                    db.session.add(new_pick)
                    db.session.flush()  # Get the ID
                    created_picks.append(new_pick.to_dict())
                
            except Exception as pick_error:
                errors.append(f"Error processing pick: {str(pick_error)}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'created_picks': created_picks,
                'updated_picks': updated_picks,
                'errors': errors,
                'total_processed': len(created_picks) + len(updated_picks),
                'total_errors': len(errors)
            },
            'message': f'Processed {len(created_picks) + len(updated_picks)} picks with {len(errors)} errors'
        })
        
    except Exception as e:
        logger.error(f"Error in bulk pick creation: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to process bulk picks'
        }), 500

@picks_bp.route('/picks/lock/<user_id>', methods=['POST'])
def lock_user_picks(user_id):
    """Lock all picks for a user (prevent further modifications)"""
    try:
        # Validate user exists
        user = User.query.get_or_404(user_id)
        
        # Get all unlocked picks for the user
        picks = Pick.query.filter_by(user_id=user_id, is_locked=False).all()
        
        locked_count = 0
        for pick in picks:
            pick.is_locked = True
            locked_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'locked_picks_count': locked_count,
                'user_id': user_id
            },
            'message': f'Locked {locked_count} picks for user'
        })
        
    except Exception as e:
        logger.error(f"Error locking picks for user {user_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to lock picks'
        }), 500

@picks_bp.route('/picks/unlock/<user_id>', methods=['POST'])
def unlock_user_picks(user_id):
    """Unlock all picks for a user (allow modifications)"""
    try:
        # Validate user exists
        user = User.query.get_or_404(user_id)
        
        # Get all locked picks for the user
        picks = Pick.query.filter_by(user_id=user_id, is_locked=True).all()
        
        unlocked_count = 0
        for pick in picks:
            # Only unlock if the match is still open
            match = Match.query.get(pick.match_id)
            if match and match.status in ['upcoming', 'live']:
                pick.is_locked = False
                unlocked_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'unlocked_picks_count': unlocked_count,
                'user_id': user_id
            },
            'message': f'Unlocked {unlocked_count} picks for user'
        })
        
    except Exception as e:
        logger.error(f"Error unlocking picks for user {user_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to unlock picks'
        }), 500

@picks_bp.route('/picks/summary/<user_id>', methods=['GET'])
def get_picks_summary(user_id):
    """Get a summary of user's picks and performance"""
    try:
        # Validate user exists
        user = User.query.get_or_404(user_id)
        
        # Get all picks for the user
        picks = Pick.query.filter_by(user_id=user_id).all()
        
        # Calculate summary statistics
        total_picks = len(picks)
        locked_picks = sum(1 for pick in picks if pick.is_locked)
        
        # Group by pick type
        pick_types = {}
        for pick in picks:
            pick_type = pick.pick_type
            if pick_type not in pick_types:
                pick_types[pick_type] = 0
            pick_types[pick_type] += 1
        
        # Group by match stage
        stage_distribution = {}
        for pick in picks:
            match = Match.query.get(pick.match_id)
            if match:
                stage = match.stage
                if stage not in stage_distribution:
                    stage_distribution[stage] = 0
                stage_distribution[stage] += 1
        
        # Calculate confidence statistics
        confidences = [pick.confidence for pick in picks if pick.confidence is not None]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        summary = {
            'user_id': user_id,
            'total_picks': total_picks,
            'locked_picks': locked_picks,
            'unlocked_picks': total_picks - locked_picks,
            'pick_types': pick_types,
            'stage_distribution': stage_distribution,
            'average_confidence': avg_confidence,
            'last_pick_time': max(pick.updated_at for pick in picks).isoformat() if picks else None
        }
        
        return jsonify({
            'success': True,
            'data': summary
        })
        
    except Exception as e:
        logger.error(f"Error getting picks summary for user {user_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get picks summary'
        }), 500

