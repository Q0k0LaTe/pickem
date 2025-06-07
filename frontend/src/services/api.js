// API service for PickEm Pro backend communication

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

class ApiService {
  constructor() {
    this.token = localStorage.getItem('access_token')
  }

  // Helper method to make authenticated requests
  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }

    // Add authorization header if token exists
    if (this.token) {
      config.headers.Authorization = `Bearer ${this.token}`
    }

    try {
      const response = await fetch(url, config)
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || `HTTP error! status: ${response.status}`)
      }

      return data
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error)
      throw error
    }
  }

  // Authentication methods
  async mockLogin(steamId = '76561198000000001') {
    const data = await this.request('/auth/mock-login', {
      method: 'POST',
      body: JSON.stringify({ steam_id: steamId }),
    })

    if (data.success) {
      this.token = data.data.access_token
      localStorage.setItem('access_token', this.token)
      localStorage.setItem('refresh_token', data.data.refresh_token)
      localStorage.setItem('user', JSON.stringify(data.data.user))
    }

    return data
  }

  async refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token')
    if (!refreshToken) {
      throw new Error('No refresh token available')
    }

    const data = await this.request('/auth/refresh', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${refreshToken}`,
      },
    })

    if (data.success) {
      this.token = data.data.access_token
      localStorage.setItem('access_token', this.token)
    }

    return data
  }

  async getProfile() {
    return this.request('/auth/profile')
  }

  logout() {
    this.token = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  // Matches methods
  async getMatches(stage = null, status = null) {
    const params = new URLSearchParams()
    if (stage) params.append('stage', stage)
    if (status) params.append('status', status)
    
    const query = params.toString() ? `?${params.toString()}` : ''
    return this.request(`/matches${query}`)
  }

  async getMatch(matchId) {
    return this.request(`/matches/${matchId}`)
  }

  async getMatchOdds(matchId, source = null, limit = 50) {
    const params = new URLSearchParams()
    if (source) params.append('source', source)
    params.append('limit', limit.toString())
    
    const query = params.toString() ? `?${params.toString()}` : ''
    return this.request(`/matches/${matchId}/odds${query}`)
  }

  async overrideMatchClassification(matchId, isSafe, confidenceThreshold = null) {
    const body = { is_safe: isSafe }
    if (confidenceThreshold !== null) {
      body.confidence_threshold = confidenceThreshold
    }

    return this.request(`/matches/${matchId}/classification`, {
      method: 'POST',
      body: JSON.stringify(body),
    })
  }

  async refreshOdds() {
    return this.request('/matches/refresh-odds', {
      method: 'POST',
    })
  }

  async classifyAllMatches() {
    return this.request('/matches/classify', {
      method: 'POST',
    })
  }

  // Optimization methods
  async createOptimizationJob(userId, safeMatches, unsafeMatches, constraints = null, targetScore = 5) {
    const body = {
      user_id: userId,
      safe_matches: safeMatches,
      unsafe_matches: unsafeMatches,
      target_score: targetScore,
    }

    if (constraints) {
      body.constraints = constraints
    }

    return this.request('/optimize', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  }

  async getOptimizationStatus(jobId) {
    return this.request(`/optimize/status/${jobId}`)
  }

  async getOptimizationResult(jobId) {
    return this.request(`/optimize/result/${jobId}`)
  }

  async getUserOptimizationJobs(userId, status = null, limit = 20) {
    const params = new URLSearchParams()
    if (status) params.append('status', status)
    params.append('limit', limit.toString())
    
    const query = params.toString() ? `?${params.toString()}` : ''
    return this.request(`/optimize/jobs/${userId}${query}`)
  }

  async quickOptimize(matchOdds, safeMatches, unsafeMatches, constraints = null, targetScore = 5, matchIds = null) {
    const body = {
      match_odds: matchOdds,
      safe_matches: safeMatches,
      unsafe_matches: unsafeMatches,
      target_score: targetScore,
    }

    if (constraints) {
      body.constraints = constraints
    }

    if (matchIds) {
      body.match_ids = matchIds
    }

    return this.request('/optimize/quick', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  }

  async simulateScenarios(scenarios, matchOdds, numSimulations = 1000) {
    return this.request('/optimize/simulate', {
      method: 'POST',
      body: JSON.stringify({
        scenarios,
        match_odds: matchOdds,
        num_simulations: numSimulations,
      }),
    })
  }

  // Picks methods
  async getUserPicks(userId, matchId = null, pickType = null, isLocked = null) {
    const params = new URLSearchParams()
    if (matchId) params.append('match_id', matchId)
    if (pickType) params.append('pick_type', pickType)
    if (isLocked !== null) params.append('is_locked', isLocked.toString())
    
    const query = params.toString() ? `?${params.toString()}` : ''
    return this.request(`/picks/${userId}${query}`)
  }

  async createOrUpdatePick(userId, matchId, selectedTeam, confidence = 0.5, pickType = 'manual', templateId = null) {
    const body = {
      user_id: userId,
      match_id: matchId,
      selected_team: selectedTeam,
      confidence,
      pick_type: pickType,
    }

    if (templateId) {
      body.template_id = templateId
    }

    return this.request('/picks', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  }

  async updatePick(pickId, selectedTeam = null, confidence = null, pickType = null) {
    const body = {}
    if (selectedTeam) body.selected_team = selectedTeam
    if (confidence !== null) body.confidence = confidence
    if (pickType) body.pick_type = pickType

    return this.request(`/picks/${pickId}`, {
      method: 'PUT',
      body: JSON.stringify(body),
    })
  }

  async deletePick(pickId) {
    return this.request(`/picks/${pickId}`, {
      method: 'DELETE',
    })
  }

  async bulkCreatePicks(userId, picks, pickType = 'optimized') {
    return this.request('/picks/bulk', {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        picks,
        pick_type: pickType,
      }),
    })
  }

  async lockUserPicks(userId) {
    return this.request(`/picks/lock/${userId}`, {
      method: 'POST',
    })
  }

  async unlockUserPicks(userId) {
    return this.request(`/picks/unlock/${userId}`, {
      method: 'POST',
    })
  }

  async getPicksSummary(userId) {
    return this.request(`/picks/summary/${userId}`)
  }

  // Health check
  async healthCheck() {
    return this.request('/health')
  }

  async getApiInfo() {
    return this.request('/info')
  }
}

// Create and export a singleton instance
const apiService = new ApiService()
export default apiService

// Export the class for testing or multiple instances
export { ApiService }

