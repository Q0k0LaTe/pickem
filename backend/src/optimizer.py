import numpy as np
import itertools
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass
import time
import logging

logger = logging.getLogger(__name__)

@dataclass
class OptimizationInput:
    """Input parameters for Pick'Em optimization"""
    odds_vector: List[float]  # Win probabilities for each match
    safe_matches: Set[str]    # User-marked safe matches
    unsafe_matches: Set[str]  # User-marked unsafe matches
    constraints: Dict         # Pick'Em constraints (3-0, 0-3, advance counts)
    target_score: int = 5     # Minimum target score
    match_ids: List[str] = None  # Match IDs corresponding to odds_vector

@dataclass
class OptimizationResult:
    """Output from Pick'Em optimization"""
    optimal_picks: List[str]           # Recommended team selections
    expected_score: float              # Expected total score
    score_distribution: List[float]    # Probability distribution 0-9
    confidence_interval: Tuple[float, float]  # 95% CI for score
    risk_analysis: Dict                # Risk breakdown by match
    alternative_strategies: List[Dict] # Top 3 alternative pick sets
    execution_time_ms: int             # Algorithm execution time

class PickEmOptimizer:
    """Monte Carlo optimizer for CS:GO Major Pick'Em predictions"""
    
    def __init__(self, num_simulations: int = 10000):
        self.num_simulations = num_simulations
        
    def optimize(self, input_data: OptimizationInput) -> OptimizationResult:
        """
        Main optimization function that maximizes P(score >= target_score)
        
        Algorithm:
        1. Enumerate all valid pick combinations for unsafe matches
        2. For each combination, run Monte Carlo simulation
        3. Calculate score distributions and select optimal strategy
        4. Generate risk analysis and alternatives
        """
        start_time = time.time()
        
        try:
            # Validate input
            self._validate_input(input_data)
            
            # Generate all possible pick combinations for unsafe matches
            unsafe_combinations = self._generate_unsafe_combinations(input_data)
            
            # Evaluate each combination
            best_combination = None
            best_score = -1
            all_results = []
            
            for combination in unsafe_combinations:
                # Create full pick vector
                pick_vector = self._create_pick_vector(input_data, combination)
                
                # Run Monte Carlo simulation
                score_dist = self._monte_carlo_simulation(input_data.odds_vector, pick_vector)
                
                # Calculate probability of achieving target score
                target_prob = sum(score_dist[input_data.target_score:])
                expected_score = sum(i * prob for i, prob in enumerate(score_dist))
                
                result = {
                    'combination': combination,
                    'pick_vector': pick_vector,
                    'score_distribution': score_dist,
                    'target_probability': target_prob,
                    'expected_score': expected_score
                }
                all_results.append(result)
                
                if target_prob > best_score:
                    best_score = target_prob
                    best_combination = result
            
            # Generate final result
            execution_time = int((time.time() - start_time) * 1000)
            
            return self._create_result(input_data, best_combination, all_results, execution_time)
            
        except Exception as e:
            logger.error(f"Optimization failed: {str(e)}")
            raise
    
    def _validate_input(self, input_data: OptimizationInput):
        """Validate optimization input parameters"""
        if not input_data.odds_vector:
            raise ValueError("Odds vector cannot be empty")
        
        if not all(0 <= prob <= 1 for prob in input_data.odds_vector):
            raise ValueError("All probabilities must be between 0 and 1")
        
        if len(input_data.safe_matches) + len(input_data.unsafe_matches) > len(input_data.odds_vector):
            raise ValueError("Total matches exceed odds vector length")
        
        # Validate Swiss format constraints
        constraints = input_data.constraints
        if constraints.get('total_picks', 9) != 9:
            raise ValueError("Swiss format requires exactly 9 picks")
    
    def _generate_unsafe_combinations(self, input_data: OptimizationInput) -> List[Dict]:
        """Generate all valid pick combinations for unsafe matches"""
        unsafe_matches = list(input_data.unsafe_matches)
        
        if len(unsafe_matches) == 0:
            return [{}]
        
        # Generate all possible team selections for unsafe matches
        # Each match can be picked as 'team_a' or 'team_b'
        combinations = []
        for picks in itertools.product(['team_a', 'team_b'], repeat=len(unsafe_matches)):
            combination = dict(zip(unsafe_matches, picks))
            
            # Validate against Swiss format constraints
            if self._validate_swiss_constraints(input_data, combination):
                combinations.append(combination)
        
        return combinations
    
    def _validate_swiss_constraints(self, input_data: OptimizationInput, unsafe_combination: Dict) -> bool:
        """Validate pick combination against Swiss format constraints"""
        constraints = input_data.constraints
        
        # For now, assume all combinations are valid
        # In a real implementation, this would check:
        # - Maximum 1 team can go 3-0
        # - Maximum 1 team can go 0-3
        # - Exactly 7 teams advance to playoffs
        # - No conflicting picks (same team picked to win and lose)
        
        return True
    
    def _create_pick_vector(self, input_data: OptimizationInput, unsafe_combination: Dict) -> List[int]:
        """Create binary pick vector from safe picks and unsafe combination"""
        # This is a simplified version - in reality, we'd need to map
        # match IDs to indices and handle team selections properly
        
        pick_vector = []
        for i, match_id in enumerate(input_data.match_ids or []):
            if match_id in input_data.safe_matches:
                # For safe matches, pick the team with higher probability
                pick_vector.append(1 if input_data.odds_vector[i] > 0.5 else 0)
            elif match_id in unsafe_combination:
                # For unsafe matches, use the user's selection
                pick_vector.append(1 if unsafe_combination[match_id] == 'team_a' else 0)
            else:
                # Default to higher probability team
                pick_vector.append(1 if input_data.odds_vector[i] > 0.5 else 0)
        
        return pick_vector
    
    def _monte_carlo_simulation(self, odds_vector: List[float], pick_vector: List[int]) -> List[float]:
        """Run Monte Carlo simulation to calculate score distribution"""
        scores = []
        
        for _ in range(self.num_simulations):
            # Simulate match outcomes
            outcomes = np.random.random(len(odds_vector)) < np.array(odds_vector)
            
            # Calculate score (number of correct picks)
            correct_picks = sum(1 for i, (outcome, pick) in enumerate(zip(outcomes, pick_vector))
                              if (outcome and pick == 1) or (not outcome and pick == 0))
            scores.append(correct_picks)
        
        # Convert to probability distribution
        score_dist = [0.0] * 10  # Scores 0-9
        for score in scores:
            if 0 <= score <= 9:
                score_dist[score] += 1
        
        # Normalize
        total = sum(score_dist)
        return [count / total for count in score_dist]
    
    def _create_result(self, input_data: OptimizationInput, best_combination: Dict, 
                      all_results: List[Dict], execution_time: int) -> OptimizationResult:
        """Create final optimization result"""
        
        if not best_combination:
            raise ValueError("No valid combinations found")
        
        # Calculate confidence interval (95%)
        score_dist = best_combination['score_distribution']
        cumulative = np.cumsum(score_dist)
        ci_lower = next(i for i, cum in enumerate(cumulative) if cum >= 0.025)
        ci_upper = next(i for i, cum in enumerate(cumulative) if cum >= 0.975)
        
        # Generate risk analysis
        risk_analysis = self._generate_risk_analysis(input_data, best_combination)
        
        # Find top 3 alternative strategies
        sorted_results = sorted(all_results, key=lambda x: x['target_probability'], reverse=True)
        alternatives = []
        for i, result in enumerate(sorted_results[1:4]):  # Skip best (index 0)
            alternatives.append({
                'rank': i + 2,
                'expected_score': result['expected_score'],
                'target_probability': result['target_probability'],
                'picks': result['combination']
            })
        
        # Convert optimal picks to the expected format
        optimal_picks = []
        for match_id in input_data.match_ids or []:
            if match_id in input_data.safe_matches:
                # Use higher probability team for safe matches
                idx = input_data.match_ids.index(match_id) if input_data.match_ids else 0
                optimal_picks.append('team_a' if input_data.odds_vector[idx] > 0.5 else 'team_b')
            elif match_id in best_combination['combination']:
                optimal_picks.append(best_combination['combination'][match_id])
            else:
                # Default selection
                idx = input_data.match_ids.index(match_id) if input_data.match_ids else 0
                optimal_picks.append('team_a' if input_data.odds_vector[idx] > 0.5 else 'team_b')
        
        return OptimizationResult(
            optimal_picks=optimal_picks,
            expected_score=best_combination['expected_score'],
            score_distribution=best_combination['score_distribution'],
            confidence_interval=(ci_lower, ci_upper),
            risk_analysis=risk_analysis,
            alternative_strategies=alternatives,
            execution_time_ms=execution_time
        )
    
    def _generate_risk_analysis(self, input_data: OptimizationInput, best_combination: Dict) -> Dict:
        """Generate risk analysis for the optimal strategy"""
        
        risk_analysis = {
            'total_risk_score': 0.0,
            'match_risks': {},
            'strategy_confidence': 0.0,
            'volatility_index': 0.0
        }
        
        # Calculate risk for each match
        for i, match_id in enumerate(input_data.match_ids or []):
            if i < len(input_data.odds_vector):
                prob = input_data.odds_vector[i]
                
                # Risk is higher for matches closer to 50/50
                risk_score = 1.0 - abs(prob - 0.5) * 2
                
                risk_analysis['match_risks'][match_id] = {
                    'risk_score': risk_score,
                    'win_probability': prob,
                    'is_safe': match_id in input_data.safe_matches,
                    'confidence_level': 'high' if prob > 0.75 or prob < 0.25 else 'medium' if prob > 0.6 or prob < 0.4 else 'low'
                }
                
                risk_analysis['total_risk_score'] += risk_score
        
        # Normalize total risk score
        if input_data.match_ids:
            risk_analysis['total_risk_score'] /= len(input_data.match_ids)
        
        # Calculate strategy confidence based on expected score
        expected_score = best_combination['expected_score']
        risk_analysis['strategy_confidence'] = min(expected_score / 9.0, 1.0)
        
        # Calculate volatility index (standard deviation of score distribution)
        score_dist = best_combination['score_distribution']
        mean_score = sum(i * prob for i, prob in enumerate(score_dist))
        variance = sum((i - mean_score) ** 2 * prob for i, prob in enumerate(score_dist))
        risk_analysis['volatility_index'] = np.sqrt(variance)
        
        return risk_analysis

def classify_match_safety(odds: List[float], threshold: float = 0.75) -> List[bool]:
    """
    Classify matches as safe or unsafe based on implied win rate
    
    Args:
        odds: List of win probabilities for team A
        threshold: Minimum probability to consider a match "safe"
    
    Returns:
        List of boolean values indicating if each match is safe
    """
    return [max(prob, 1 - prob) >= threshold for prob in odds]

def calculate_implied_win_rates(bookmaker_odds: Dict) -> List[float]:
    """
    Convert bookmaker odds to implied win probabilities
    
    Args:
        bookmaker_odds: Dictionary with team odds
    
    Returns:
        List of win probabilities
    """
    # This is a placeholder - real implementation would handle
    # various odds formats (decimal, fractional, American)
    
    probabilities = []
    for match_odds in bookmaker_odds.get('matches', []):
        team_a_decimal = match_odds.get('team_a_odds', 2.0)
        team_b_decimal = match_odds.get('team_b_odds', 2.0)
        
        # Convert decimal odds to probabilities
        prob_a = 1.0 / team_a_decimal
        prob_b = 1.0 / team_b_decimal
        
        # Normalize to remove bookmaker margin
        total = prob_a + prob_b
        prob_a_normalized = prob_a / total
        
        probabilities.append(prob_a_normalized)
    
    return probabilities

