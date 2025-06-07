import { useState, useEffect } from 'react'
import { ThemeProvider, useTheme } from './contexts/ThemeContext'
import { Button } from './components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card'
import { Badge } from './components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs'
import { Moon, Sun, Target, TrendingUp, Users, Zap, BarChart3, Eye } from 'lucide-react'
import { apiService } from './services/api'
import VisualizationDashboard from './components/VisualizationDashboard'
import ScenarioDashboard from './components/ScenarioDashboard'
import MatchAnalysis from './components/MatchAnalysis'
import './App.css'

function AppContent() {
  const { theme, toggleTheme } = useTheme()
  const [matches, setMatches] = useState([])
  const [selectedMatches, setSelectedMatches] = useState(new Set())
  const [optimizationResults, setOptimizationResults] = useState(null)
  const [isOptimizing, setIsOptimizing] = useState(false)
  const [selectedMatch, setSelectedMatch] = useState(null)
  const [activeTab, setActiveTab] = useState('matches')

  // Sample data for demonstration
  const sampleMatches = [
    {
      id: 1,
      teamA: 'NAVI',
      teamB: 'Astralis',
      teamALogo: '/api/placeholder/32/32',
      teamBLogo: '/api/placeholder/32/32',
      tournament: 'IEM Katowice 2024',
      startTime: '2024-06-07T15:00:00Z',
      teamAWinProbability: 0.65,
      teamBWinProbability: 0.35,
      confidence: 0.82,
      riskLevel: 0.25,
      expectedValue: 1.45,
      classification: 'safe'
    },
    {
      id: 2,
      teamA: 'G2',
      teamB: 'FaZe',
      teamALogo: '/api/placeholder/32/32',
      teamBLogo: '/api/placeholder/32/32',
      tournament: 'BLAST Premier',
      startTime: '2024-06-07T18:00:00Z',
      teamAWinProbability: 0.48,
      teamBWinProbability: 0.52,
      confidence: 0.45,
      riskLevel: 0.75,
      expectedValue: 0.95,
      classification: 'unsafe'
    },
    {
      id: 3,
      teamA: 'Vitality',
      teamB: 'Liquid',
      teamALogo: '/api/placeholder/32/32',
      teamBLogo: '/api/placeholder/32/32',
      tournament: 'ESL Pro League',
      startTime: '2024-06-07T21:00:00Z',
      teamAWinProbability: 0.72,
      teamBWinProbability: 0.28,
      confidence: 0.88,
      riskLevel: 0.15,
      expectedValue: 1.65,
      classification: 'safe'
    }
  ]

  const sampleOptimizationData = {
    scenarios: [
      {
        expectedPoints: 7.2,
        winProbability: 0.78,
        riskLevel: 0.25,
        confidence: 0.85,
        variance: 1.2,
        strategy: 'Conservative',
        picks: [
          { matchId: 1, teamA: 'NAVI', teamB: 'Astralis', selectedTeam: 'NAVI', confidence: 0.82 },
          { matchId: 3, teamA: 'Vitality', teamB: 'Liquid', selectedTeam: 'Vitality', confidence: 0.88 }
        ]
      },
      {
        expectedPoints: 8.5,
        winProbability: 0.65,
        riskLevel: 0.45,
        confidence: 0.72,
        variance: 2.1,
        strategy: 'Balanced',
        picks: [
          { matchId: 1, teamA: 'NAVI', teamB: 'Astralis', selectedTeam: 'NAVI', confidence: 0.82 },
          { matchId: 2, teamA: 'G2', teamB: 'FaZe', selectedTeam: 'FaZe', confidence: 0.52 },
          { matchId: 3, teamA: 'Vitality', teamB: 'Liquid', selectedTeam: 'Vitality', confidence: 0.88 }
        ]
      },
      {
        expectedPoints: 10.1,
        winProbability: 0.42,
        riskLevel: 0.75,
        confidence: 0.58,
        variance: 3.8,
        strategy: 'Aggressive',
        picks: [
          { matchId: 1, teamA: 'NAVI', teamB: 'Astralis', selectedTeam: 'Astralis', confidence: 0.35 },
          { matchId: 2, teamA: 'G2', teamB: 'FaZe', selectedTeam: 'G2', confidence: 0.48 },
          { matchId: 3, teamA: 'Vitality', teamB: 'Liquid', selectedTeam: 'Liquid', confidence: 0.28 }
        ]
      }
    ],
    pickDistribution: [
      { category: 'Safe Picks', count: 5, percentage: 55.6 },
      { category: 'Risky Picks', count: 3, percentage: 33.3 },
      { category: 'Wildcard Picks', count: 1, percentage: 11.1 }
    ],
    simulation: {
      iterations: 10000,
      distribution: [
        { score: 0, frequency: 120 },
        { score: 1, frequency: 340 },
        { score: 2, frequency: 680 },
        { score: 3, frequency: 1200 },
        { score: 4, frequency: 1850 },
        { score: 5, frequency: 2100 },
        { score: 6, frequency: 1900 },
        { score: 7, frequency: 1200 },
        { score: 8, frequency: 450 },
        { score: 9, frequency: 160 }
      ],
      statistics: {
        mean: 5.2,
        median: 5.0,
        standardDeviation: 1.8,
        confidenceInterval: [2.1, 8.3]
      }
    }
  }

  const sampleCommunityData = {
    communityStats: {
      totalUsers: 12847,
      averageScore: 5.3,
      successRate: 73,
      topPerformers: [
        { rank: 1, username: 'ProPicker', score: 8.9, accuracy: 95 },
        { rank: 2, username: 'CSGOOracle', score: 8.7, accuracy: 92 },
        { rank: 3, username: 'MajorMaster', score: 8.5, accuracy: 90 }
      ]
    }
  }

  const samplePerformanceData = {
    historicalPerformance: [
      { round: 'Round 1', actualPoints: 3, predictedPoints: 2.8, accuracy: 75 },
      { round: 'Round 2', actualPoints: 5, predictedPoints: 4.2, accuracy: 80 },
      { round: 'Round 3', actualPoints: 2, predictedPoints: 3.1, accuracy: 65 },
      { round: 'Round 4', actualPoints: 7, predictedPoints: 6.5, accuracy: 85 },
      { round: 'Round 5', actualPoints: 4, predictedPoints: 4.8, accuracy: 90 }
    ]
  }

  useEffect(() => {
    setMatches(sampleMatches)
  }, [])

  const toggleMatchSelection = (matchId) => {
    const newSelected = new Set(selectedMatches)
    if (newSelected.has(matchId)) {
      newSelected.delete(matchId)
    } else {
      newSelected.add(matchId)
    }
    setSelectedMatches(newSelected)
  }

  const handleOptimize = async () => {
    if (selectedMatches.size === 0) {
      alert('Please select at least one match to optimize')
      return
    }

    setIsOptimizing(true)
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000))
      setOptimizationResults(sampleOptimizationData)
      setActiveTab('scenarios')
    } catch (error) {
      console.error('Optimization failed:', error)
      alert('Optimization failed. Please try again.')
    } finally {
      setIsOptimizing(false)
    }
  }

  const getMatchClassificationColor = (classification) => {
    switch (classification) {
      case 'safe': return 'bg-green-500'
      case 'risky': return 'bg-yellow-500'
      case 'unsafe': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  return (
    <div className={`min-h-screen transition-colors duration-300 ${
      theme === 'dark' 
        ? 'bg-gray-900 text-white' 
        : 'bg-gray-50 text-gray-900'
    }`}>
      <div className="container mx-auto p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Target className="h-8 w-8 text-primary" />
              PickEm Pro
            </h1>
            <p className="text-muted-foreground mt-1">
              Advanced CS Major Pick'Em Optimization Platform
            </p>
          </div>
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="icon"
              onClick={toggleTheme}
              className="rounded-full"
            >
              {theme === 'dark' ? (
                <Sun className="h-4 w-4" />
              ) : (
                <Moon className="h-4 w-4" />
              )}
            </Button>
            <Button variant="outline">
              Connect Steam
            </Button>
          </div>
        </div>

        {/* Main Content */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="matches" className="flex items-center gap-2">
              <Target className="h-4 w-4" />
              Matches
            </TabsTrigger>
            <TabsTrigger value="scenarios" className="flex items-center gap-2">
              <Zap className="h-4 w-4" />
              Scenarios
            </TabsTrigger>
            <TabsTrigger value="analysis" className="flex items-center gap-2">
              <Eye className="h-4 w-4" />
              Analysis
            </TabsTrigger>
            <TabsTrigger value="dashboard" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Dashboard
            </TabsTrigger>
            <TabsTrigger value="community" className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              Community
            </TabsTrigger>
          </TabsList>

          <TabsContent value="matches" className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold">Available Matches</h2>
                <p className="text-muted-foreground">
                  Select matches for Pick'Em optimization
                </p>
              </div>
              <Button 
                onClick={handleOptimize}
                disabled={selectedMatches.size === 0 || isOptimizing}
                className="flex items-center gap-2"
              >
                <TrendingUp className="h-4 w-4" />
                {isOptimizing ? 'Optimizing...' : 'Optimize Picks'}
              </Button>
            </div>

            <div className="grid gap-4">
              {matches.map((match) => (
                <Card 
                  key={match.id}
                  className={`cursor-pointer transition-all hover:shadow-md ${
                    selectedMatches.has(match.id) ? 'ring-2 ring-primary' : ''
                  }`}
                  onClick={() => toggleMatchSelection(match.id)}
                >
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="flex items-center gap-3">
                          <img 
                            src={match.teamALogo} 
                            alt={match.teamA}
                            className="w-8 h-8 rounded"
                            onError={(e) => e.target.style.display = 'none'}
                          />
                          <span className="font-semibold">{match.teamA}</span>
                        </div>
                        <span className="text-muted-foreground">vs</span>
                        <div className="flex items-center gap-3">
                          <img 
                            src={match.teamBLogo} 
                            alt={match.teamB}
                            className="w-8 h-8 rounded"
                            onError={(e) => e.target.style.display = 'none'}
                          />
                          <span className="font-semibold">{match.teamB}</span>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="text-sm text-muted-foreground">{match.tournament}</p>
                          <p className="text-sm text-muted-foreground">
                            {new Date(match.startTime).toLocaleString()}
                          </p>
                        </div>
                        
                        <div className="text-right">
                          <p className="text-sm text-muted-foreground">Win Probability</p>
                          <p className="font-bold">
                            {(Math.max(match.teamAWinProbability, match.teamBWinProbability) * 100).toFixed(1)}%
                          </p>
                        </div>
                        
                        <Badge className={getMatchClassificationColor(match.classification)}>
                          {match.classification}
                        </Badge>
                        
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            setSelectedMatch(match)
                            setActiveTab('analysis')
                          }}
                        >
                          Analyze
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="scenarios" className="space-y-6">
            <ScenarioDashboard 
              optimizationData={optimizationResults}
              onOptimize={handleOptimize}
            />
          </TabsContent>

          <TabsContent value="analysis" className="space-y-6">
            <MatchAnalysis 
              match={selectedMatch}
              historicalData={{}}
              oddsData={{}}
            />
          </TabsContent>

          <TabsContent value="dashboard" className="space-y-6">
            <VisualizationDashboard 
              optimizationData={optimizationResults}
              communityData={sampleCommunityData}
              performanceData={samplePerformanceData}
            />
          </TabsContent>

          <TabsContent value="community" className="space-y-6">
            <div className="text-center py-12">
              <Users className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-xl font-semibold mb-2">Community Features</h3>
              <p className="text-muted-foreground">
                Connect with other Pick'Em enthusiasts, share strategies, and compete on leaderboards.
              </p>
              <Button className="mt-4">Join Community</Button>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  )
}

export default App

