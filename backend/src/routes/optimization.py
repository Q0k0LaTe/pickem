from flask import Blueprint, jsonify, request
from src.models.user import OptimizationJob, Match, Odds, Pick, User, db
from src.optimizer import PickEmOptimizer, OptimizationInput
import logging
from datetime import datetime
import threading
import time

logger = logging.getLogger(__name__)

optimization_bp = Blueprint('optimization', __name__)

# Global optimizer instance
optimizer = PickEmOptimizer(num_simulations=10000)

@optimization_bp.route('/optimize', methods=['POST'])
def create_optimization_job():
    """Create a new Pick'Em optimization job"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'safe_matches', 'unsafe_matches']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        user_id = data['user_id']
        safe_matches = data['safe_matches']  # List of match IDs
        unsafe_matches = data['unsafe_matches']  # List of match IDs
        constraints = data.get('constraints', {
            'max_3_0': 1,
            'max_0_3': 1,
            'advance_picks': 7,
            'total_picks': 9
        })
        target_score = data.get('target_score', 5)
        
        # Validate user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Validate matches exist
        all_match_ids = safe_matches + unsafe_matches
        matches = Match.query.filter(Match.id.in_(all_match_ids)).all()
        
        if len(matches) != len(all_match_ids):
            return jsonify({
                'success': False,
                'error': 'One or more matches not found'
            }), 404
        
        # Create optimization job
        job = OptimizationJob(
            user_id=user_id,
            status='pending',
            safe_picks=safe_matches,
            unsafe_picks=unsafe_matches,
            constraints=constraints
        )
        
        db.session.add(job)
        db.session.commit()
        
        # Start optimization in background thread
        thread = threading.Thread(
            target=run_optimization_job,
            args=(job.id, target_score)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'data': {
                'job_id': job.id,
                'status': job.status,
                'estimated_time_seconds': 30  # Rough estimate
            },
            'message': 'Optimization job created and started'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating optimization job: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to create optimization job'
        }), 500

@optimization_bp.route('/optimize/status/<job_id>', methods=['GET'])
def get_optimization_status(job_id):
    """Check the status of an optimization job"""
    try:
        job = OptimizationJob.query.get_or_404(job_id)
        
        response_data = job.to_dict()
        
        # Add progress information
        if job.status == 'running':
            # Calculate estimated progress based on time elapsed
            if job.started_at:
                elapsed = (datetime.utcnow() - job.started_at).total_seconds()
                estimated_total = 30  # seconds
                progress = min(elapsed / estimated_total * 100, 95)  # Cap at 95% until complete
                response_data['progress_percentage'] = progress
            else:
                response_data['progress_percentage'] = 0
        elif job.status == 'completed':
            response_data['progress_percentage'] = 100
        else:
            response_data['progress_percentage'] = 0
        
        return jsonify({
            'success': True,
            'data': response_data
        })
        
    except Exception as e:
        logger.error(f"Error fetching optimization status {job_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Job not found'
        }), 404

@optimization_bp.route('/optimize/result/<job_id>', methods=['GET'])
def get_optimization_result(job_id):
    """Get the result of a completed optimization job"""
    try:
        job = OptimizationJob.query.get_or_404(job_id)
        
        if job.status != 'completed':
            return jsonify({
                'success': False,
                'error': f'Job is not completed (status: {job.status})'
            }), 400
        
        if not job.result:
            return jsonify({
                'success': False,
                'error': 'No result available'
            }), 404
        
        # Enhance result with match information
        enhanced_result = job.result.copy()
        
        # Get match details for the optimal picks
        if 'optimal_picks' in enhanced_result:
            match_details = []
            all_match_ids = job.safe_picks + job.unsafe_picks
            
            for i, pick in enumerate(enhanced_result['optimal_picks']):
                if i < len(all_match_ids):
                    match = Match.query.get(all_match_ids[i])
                    if match:
                        match_details.append({
                            'match_id': match.id,
                            'team_a': match.team_a,
                            'team_b': match.team_b,
                            'selected_team': pick,
                            'is_safe': match.id in job.safe_picks,
                            'confidence_threshold': match.confidence_threshold
                        })
            
            enhanced_result['match_details'] = match_details
        
        return jsonify({
            'success': True,
            'data': {
                'job_info': job.to_dict(),
                'optimization_result': enhanced_result
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching optimization result {job_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch result'
        }), 500

@optimization_bp.route('/optimize/jobs/<user_id>', methods=['GET'])
def get_user_optimization_jobs(user_id):
    """Get all optimization jobs for a user"""
    try:
        # Validate user exists
        user = User.query.get_or_404(user_id)
        
        # Get query parameters
        status = request.args.get('status')
        limit = request.args.get('limit', type=int, default=20)
        
        # Build query
        query = OptimizationJob.query.filter(OptimizationJob.user_id == user_id)
        
        if status:
            query = query.filter(OptimizationJob.status == status)
        
        jobs = query.order_by(OptimizationJob.created_at.desc()).limit(limit).all()
        
        jobs_data = [job.to_dict() for job in jobs]
        
        return jsonify({
            'success': True,
            'data': jobs_data,
            'count': len(jobs_data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching user optimization jobs {user_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch jobs'
        }), 500

@optimization_bp.route('/optimize/quick', methods=['POST'])
def quick_optimize():
    """Run a quick optimization without creating a persistent job"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['match_odds', 'safe_matches', 'unsafe_matches']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        match_odds = data['match_odds']  # List of win probabilities
        safe_matches = set(data['safe_matches'])
        unsafe_matches = set(data['unsafe_matches'])
        constraints = data.get('constraints', {
            'max_3_0': 1,
            'max_0_3': 1,
            'advance_picks': 7,
            'total_picks': 9
        })
        target_score = data.get('target_score', 5)
        match_ids = data.get('match_ids', [f'match_{i}' for i in range(len(match_odds))])
        
        # Create optimization input
        optimization_input = OptimizationInput(
            odds_vector=match_odds,
            safe_matches=safe_matches,
            unsafe_matches=unsafe_matches,
            constraints=constraints,
            target_score=target_score,
            match_ids=match_ids
        )
        
        # Run optimization
        start_time = time.time()
        result = optimizer.optimize(optimization_input)
        execution_time = int((time.time() - start_time) * 1000)
        
        # Convert result to dict
        result_dict = {
            'optimal_picks': result.optimal_picks,
            'expected_score': result.expected_score,
            'score_distribution': result.score_distribution,
            'confidence_interval': result.confidence_interval,
            'risk_analysis': result.risk_analysis,
            'alternative_strategies': result.alternative_strategies,
            'execution_time_ms': execution_time
        }
        
        return jsonify({
            'success': True,
            'data': result_dict,
            'message': f'Optimization completed in {execution_time}ms'
        })
        
    except Exception as e:
        logger.error(f"Error in quick optimization: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Optimization failed: {str(e)}'
        }), 500

def run_optimization_job(job_id: str, target_score: int = 5):
    """Background function to run optimization job"""
    try:
        # Get job from database
        job = OptimizationJob.query.get(job_id)
        if not job:
            logger.error(f"Optimization job {job_id} not found")
            return
        
        # Update job status
        job.status = 'running'
        job.started_at = datetime.utcnow()
        db.session.commit()
        
        # Get match data and odds
        all_match_ids = job.safe_picks + job.unsafe_picks
        matches = Match.query.filter(Match.id.in_(all_match_ids)).all()
        
        # Build odds vector
        odds_vector = []
        match_id_order = []
        
        for match in matches:
            # Get latest consensus odds
            latest_odds = None
            for odds in match.odds:
                if odds.is_active and odds.source == 'bookmaker_consensus':
                    if not latest_odds or odds.timestamp > latest_odds.timestamp:
                        latest_odds = odds
            
            if latest_odds:
                # Use team A win probability
                odds_vector.append(latest_odds.team_a_win_prob)
            else:
                # Fallback to 50/50 if no odds available
                odds_vector.append(0.5)
            
            match_id_order.append(match.id)
        
        # Create optimization input
        optimization_input = OptimizationInput(
            odds_vector=odds_vector,
            safe_matches=set(job.safe_picks),
            unsafe_matches=set(job.unsafe_picks),
            constraints=job.constraints,
            target_score=target_score,
            match_ids=match_id_order
        )
        
        # Run optimization
        start_time = time.time()
        result = optimizer.optimize(optimization_input)
        execution_time = int((time.time() - start_time) * 1000)
        
        # Save result
        result_dict = {
            'optimal_picks': result.optimal_picks,
            'expected_score': result.expected_score,
            'score_distribution': result.score_distribution,
            'confidence_interval': result.confidence_interval,
            'risk_analysis': result.risk_analysis,
            'alternative_strategies': result.alternative_strategies,
            'execution_time_ms': execution_time,
            'match_id_order': match_id_order
        }
        
        job.result = result_dict
        job.execution_time_ms = execution_time
        job.status = 'completed'
        job.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Optimization job {job_id} completed successfully in {execution_time}ms")
        
    except Exception as e:
        logger.error(f"Optimization job {job_id} failed: {str(e)}")
        
        # Update job with error
        try:
            job = OptimizationJob.query.get(job_id)
            if job:
                job.status = 'failed'
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                db.session.commit()
        except Exception as db_error:
            logger.error(f"Failed to update job status: {str(db_error)}")

@optimization_bp.route('/optimize/simulate', methods=['POST'])
def simulate_scenarios():
    """Simulate different pick scenarios for comparison"""
    try:
        data = request.get_json()
        
        scenarios = data.get('scenarios', [])
        match_odds = data.get('match_odds', [])
        num_simulations = data.get('num_simulations', 1000)
        
        if not scenarios or not match_odds:
            return jsonify({
                'success': False,
                'error': 'scenarios and match_odds are required'
            }), 400
        
        results = []
        
        for i, scenario in enumerate(scenarios):
            scenario_name = scenario.get('name', f'Scenario {i+1}')
            picks = scenario.get('picks', [])
            
            if len(picks) != len(match_odds):
                continue
            
            # Convert picks to binary vector (1 for team_a, 0 for team_b)
            pick_vector = [1 if pick == 'team_a' else 0 for pick in picks]
            
            # Run simulation
            score_dist = optimizer._monte_carlo_simulation(match_odds, pick_vector)
            expected_score = sum(i * prob for i, prob in enumerate(score_dist))
            
            # Calculate probability of achieving different score thresholds
            prob_5_plus = sum(score_dist[5:])
            prob_7_plus = sum(score_dist[7:])
            
            results.append({
                'scenario_name': scenario_name,
                'picks': picks,
                'expected_score': expected_score,
                'score_distribution': score_dist,
                'prob_5_plus': prob_5_plus,
                'prob_7_plus': prob_7_plus
            })
        
        # Sort by expected score
        results.sort(key=lambda x: x['expected_score'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'scenarios': results,
                'best_scenario': results[0] if results else None,
                'comparison_metrics': {
                    'highest_expected_score': max(r['expected_score'] for r in results) if results else 0,
                    'highest_prob_5_plus': max(r['prob_5_plus'] for r in results) if results else 0
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error in scenario simulation: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Simulation failed: {str(e)}'
        }), 500

