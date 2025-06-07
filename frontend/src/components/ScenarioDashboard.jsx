import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  Treemap, Cell
} from 'recharts';
import { 
  Target, TrendingUp, AlertTriangle, CheckCircle, 
  Zap, Brain, Calculator, Eye, Filter, RotateCcw 
} from 'lucide-react';

// Scenario Analysis Component
export const ScenarioAnalysis = ({ scenarios, onScenarioSelect, selectedScenario }) => {
  const [sortBy, setSortBy] = useState('expectedPoints');
  const [filterRisk, setFilterRisk] = useState('all');

  const sortedScenarios = useMemo(() => {
    let filtered = scenarios || [];
    
    if (filterRisk !== 'all') {
      filtered = filtered.filter(scenario => {
        const risk = scenario.riskLevel;
        switch (filterRisk) {
          case 'low': return risk < 0.3;
          case 'medium': return risk >= 0.3 && risk < 0.7;
          case 'high': return risk >= 0.7;
          default: return true;
        }
      });
    }

    return filtered.sort((a, b) => {
      switch (sortBy) {
        case 'expectedPoints': return b.expectedPoints - a.expectedPoints;
        case 'winProbability': return b.winProbability - a.winProbability;
        case 'riskLevel': return a.riskLevel - b.riskLevel;
        default: return 0;
      }
    });
  }, [scenarios, sortBy, filterRisk]);

  const getRiskColor = (riskLevel) => {
    if (riskLevel < 0.3) return 'bg-green-500';
    if (riskLevel < 0.7) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getRiskLabel = (riskLevel) => {
    if (riskLevel < 0.3) return 'Low Risk';
    if (riskLevel < 0.7) return 'Medium Risk';
    return 'High Risk';
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="h-5 w-5" />
          Scenario Analysis
        </CardTitle>
        <CardDescription>
          Compare different Pick'Em strategies and their potential outcomes
        </CardDescription>
        
        <div className="flex gap-2 flex-wrap">
          <select 
            value={sortBy} 
            onChange={(e) => setSortBy(e.target.value)}
            className="px-3 py-1 border rounded-md text-sm"
          >
            <option value="expectedPoints">Sort by Expected Points</option>
            <option value="winProbability">Sort by Win Probability</option>
            <option value="riskLevel">Sort by Risk Level</option>
          </select>
          
          <select 
            value={filterRisk} 
            onChange={(e) => setFilterRisk(e.target.value)}
            className="px-3 py-1 border rounded-md text-sm"
          >
            <option value="all">All Risk Levels</option>
            <option value="low">Low Risk Only</option>
            <option value="medium">Medium Risk Only</option>
            <option value="high">High Risk Only</option>
          </select>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-4">
          {sortedScenarios.map((scenario, index) => (
            <div 
              key={index}
              className={`p-4 border rounded-lg cursor-pointer transition-all hover:shadow-md ${
                selectedScenario === index ? 'border-primary bg-primary/5' : 'border-border'
              }`}
              onClick={() => onScenarioSelect?.(index)}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <h3 className="font-semibold">Scenario {index + 1}</h3>
                  <Badge variant="outline">{scenario.strategy || 'Balanced'}</Badge>
                  <Badge className={getRiskColor(scenario.riskLevel)}>
                    {getRiskLabel(scenario.riskLevel)}
                  </Badge>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold">{scenario.expectedPoints.toFixed(1)} pts</p>
                  <p className="text-sm text-muted-foreground">
                    {(scenario.winProbability * 100).toFixed(1)}% win rate
                  </p>
                </div>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Picks</p>
                  <p className="font-medium">{scenario.picks?.length || 0}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Confidence</p>
                  <p className="font-medium">{(scenario.confidence * 100).toFixed(0)}%</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Variance</p>
                  <p className="font-medium">{scenario.variance?.toFixed(2) || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">ROI</p>
                  <p className="font-medium text-green-600">
                    {((scenario.expectedPoints / (scenario.picks?.length || 1)) * 100).toFixed(0)}%
                  </p>
                </div>
              </div>
              
              <div className="mt-3">
                <div className="flex justify-between text-xs text-muted-foreground mb-1">
                  <span>Risk Level</span>
                  <span>{(scenario.riskLevel * 100).toFixed(0)}%</span>
                </div>
                <Progress value={scenario.riskLevel * 100} className="h-2" />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

// Detailed Scenario View
export const ScenarioDetailView = ({ scenario, scenarioIndex }) => {
  if (!scenario) {
    return (
      <Card>
        <CardContent className="p-6 text-center">
          <p className="text-muted-foreground">Select a scenario to view details</p>
        </CardContent>
      </Card>
    );
  }

  const radarData = [
    { subject: 'Expected Points', A: scenario.expectedPoints, fullMark: 10 },
    { subject: 'Win Probability', A: scenario.winProbability * 10, fullMark: 10 },
    { subject: 'Confidence', A: scenario.confidence * 10, fullMark: 10 },
    { subject: 'Consistency', A: (1 - scenario.riskLevel) * 10, fullMark: 10 },
    { subject: 'ROI Potential', A: (scenario.expectedPoints / (scenario.picks?.length || 1)), fullMark: 10 }
  ];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Eye className="h-5 w-5" />
            Scenario {scenarioIndex + 1} - Detailed Analysis
          </CardTitle>
          <CardDescription>
            In-depth breakdown of this Pick'Em strategy
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold mb-3">Performance Metrics</h4>
              <ResponsiveContainer width="100%" height={250}>
                <RadarChart data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="subject" />
                  <PolarRadiusAxis angle={90} domain={[0, 10]} />
                  <Radar
                    name="Performance"
                    dataKey="A"
                    stroke="#8b5cf6"
                    fill="#8b5cf6"
                    fillOpacity={0.3}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
            
            <div>
              <h4 className="font-semibold mb-3">Key Statistics</h4>
              <div className="space-y-4">
                <div className="flex justify-between items-center p-3 bg-muted/50 rounded-lg">
                  <span className="text-sm font-medium">Expected Points</span>
                  <span className="text-lg font-bold">{scenario.expectedPoints.toFixed(2)}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-muted/50 rounded-lg">
                  <span className="text-sm font-medium">Win Probability</span>
                  <span className="text-lg font-bold">{(scenario.winProbability * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-muted/50 rounded-lg">
                  <span className="text-sm font-medium">Risk Level</span>
                  <span className="text-lg font-bold">{(scenario.riskLevel * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-muted/50 rounded-lg">
                  <span className="text-sm font-medium">Total Picks</span>
                  <span className="text-lg font-bold">{scenario.picks?.length || 0}</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {scenario.picks && scenario.picks.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Pick Breakdown</CardTitle>
            <CardDescription>
              Detailed analysis of each pick in this scenario
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {scenario.picks.map((pick, index) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <Badge variant="outline">{pick.matchId}</Badge>
                    <div>
                      <p className="font-medium">{pick.teamA} vs {pick.teamB}</p>
                      <p className="text-sm text-muted-foreground">
                        Picked: {pick.selectedTeam}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">{(pick.confidence * 100).toFixed(0)}%</p>
                    <p className="text-sm text-muted-foreground">confidence</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

// Monte Carlo Simulation Visualization
export const MonteCarloVisualization = ({ simulationData }) => {
  const distributionData = simulationData?.distribution || [];
  const statistics = simulationData?.statistics || {
    mean: 0,
    median: 0,
    standardDeviation: 0,
    confidenceInterval: [0, 0]
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calculator className="h-5 w-5" />
          Monte Carlo Simulation Results
        </CardTitle>
        <CardDescription>
          Statistical analysis of {simulationData?.iterations || 10000} simulation runs
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <h4 className="font-semibold mb-3">Score Distribution</h4>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={distributionData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="score" />
                <YAxis />
                <Tooltip 
                  formatter={(value) => [`${value} runs`, 'Frequency']}
                  labelFormatter={(label) => `Score: ${label}`}
                />
                <Bar dataKey="frequency" fill="#8b5cf6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          
          <div>
            <h4 className="font-semibold mb-3">Statistical Summary</h4>
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-muted/50 rounded-lg">
                <span className="text-sm font-medium">Mean Score</span>
                <span className="text-lg font-bold">{statistics.mean.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-muted/50 rounded-lg">
                <span className="text-sm font-medium">Median Score</span>
                <span className="text-lg font-bold">{statistics.median.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-muted/50 rounded-lg">
                <span className="text-sm font-medium">Standard Deviation</span>
                <span className="text-lg font-bold">{statistics.standardDeviation.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-muted/50 rounded-lg">
                <span className="text-sm font-medium">95% Confidence Interval</span>
                <span className="text-lg font-bold">
                  {statistics.confidenceInterval[0].toFixed(1)} - {statistics.confidenceInterval[1].toFixed(1)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Main Scenario Dashboard
export const ScenarioDashboard = ({ optimizationData, onOptimize }) => {
  const [selectedScenario, setSelectedScenario] = useState(0);
  const [activeTab, setActiveTab] = useState('scenarios');

  const scenarios = optimizationData?.scenarios || [];
  const simulationData = optimizationData?.simulation;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Scenario Analysis</h2>
          <p className="text-muted-foreground">
            Explore different Pick'Em strategies and their potential outcomes
          </p>
        </div>
        <Button onClick={onOptimize} className="flex items-center gap-2">
          <RotateCcw className="h-4 w-4" />
          Re-optimize
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="scenarios">Scenarios</TabsTrigger>
          <TabsTrigger value="details">Details</TabsTrigger>
          <TabsTrigger value="simulation">Simulation</TabsTrigger>
        </TabsList>

        <TabsContent value="scenarios" className="space-y-6">
          <ScenarioAnalysis 
            scenarios={scenarios}
            onScenarioSelect={setSelectedScenario}
            selectedScenario={selectedScenario}
          />
        </TabsContent>

        <TabsContent value="details" className="space-y-6">
          <ScenarioDetailView 
            scenario={scenarios[selectedScenario]}
            scenarioIndex={selectedScenario}
          />
        </TabsContent>

        <TabsContent value="simulation" className="space-y-6">
          <MonteCarloVisualization simulationData={simulationData} />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ScenarioDashboard;

