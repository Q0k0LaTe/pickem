import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, Area, AreaChart } from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Target, Award, Users, Zap } from 'lucide-react';

// Color palette for charts
const COLORS = {
  primary: '#8b5cf6',
  secondary: '#06b6d4',
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  muted: '#6b7280'
};

const CHART_COLORS = [COLORS.primary, COLORS.secondary, COLORS.success, COLORS.warning, COLORS.danger];

// Optimization Results Visualization
export const OptimizationResultsChart = ({ data, title = "Pick'Em Optimization Results" }) => {
  const chartData = data?.scenarios?.map((scenario, index) => ({
    name: `Scenario ${index + 1}`,
    expectedPoints: scenario.expectedPoints,
    winProbability: scenario.winProbability * 100,
    riskLevel: scenario.riskLevel,
    picks: scenario.picks?.length || 0
  })) || [];

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Target className="h-5 w-5" />
          {title}
        </CardTitle>
        <CardDescription>
          Comparison of different Pick'Em strategies and their expected outcomes
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip 
              formatter={(value, name) => [
                name === 'expectedPoints' ? `${value} points` : 
                name === 'winProbability' ? `${value.toFixed(1)}%` : value,
                name === 'expectedPoints' ? 'Expected Points' :
                name === 'winProbability' ? 'Win Probability' : name
              ]}
            />
            <Bar yAxisId="left" dataKey="expectedPoints" fill={COLORS.primary} name="expectedPoints" />
            <Bar yAxisId="right" dataKey="winProbability" fill={COLORS.secondary} name="winProbability" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

// Risk vs Reward Scatter Plot
export const RiskRewardChart = ({ data }) => {
  const scatterData = data?.scenarios?.map((scenario, index) => ({
    x: scenario.riskLevel * 100,
    y: scenario.expectedPoints,
    name: `Scenario ${index + 1}`,
    picks: scenario.picks?.length || 0,
    winProbability: scenario.winProbability * 100
  })) || [];

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          Risk vs Reward Analysis
        </CardTitle>
        <CardDescription>
          Relationship between risk level and expected points for each strategy
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={scatterData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="x" label={{ value: 'Risk Level (%)', position: 'insideBottom', offset: -5 }} />
            <YAxis label={{ value: 'Expected Points', angle: -90, position: 'insideLeft' }} />
            <Tooltip 
              formatter={(value, name) => [
                name === 'y' ? `${value} points` : `${value}%`,
                name === 'y' ? 'Expected Points' : 'Risk Level'
              ]}
              labelFormatter={(label) => `Risk: ${label}%`}
            />
            <Area type="monotone" dataKey="y" stroke={COLORS.primary} fill={COLORS.primary} fillOpacity={0.3} />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

// Pick Distribution Pie Chart
export const PickDistributionChart = ({ data }) => {
  const pieData = data?.pickDistribution?.map((item, index) => ({
    name: item.category,
    value: item.count,
    percentage: item.percentage
  })) || [
    { name: 'Safe Picks', value: 5, percentage: 55.6 },
    { name: 'Risky Picks', value: 3, percentage: 33.3 },
    { name: 'Wildcard Picks', value: 1, percentage: 11.1 }
  ];

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Award className="h-5 w-5" />
          Pick Distribution
        </CardTitle>
        <CardDescription>
          Breakdown of picks by risk category
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percentage }) => `${name}: ${percentage}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {pieData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(value, name) => [`${value} picks`, name]} />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

// Performance Tracking Line Chart
export const PerformanceChart = ({ data }) => {
  const performanceData = data?.historicalPerformance || [
    { round: 'Round 1', actualPoints: 3, predictedPoints: 2.8, accuracy: 75 },
    { round: 'Round 2', actualPoints: 5, predictedPoints: 4.2, accuracy: 80 },
    { round: 'Round 3', actualPoints: 2, predictedPoints: 3.1, accuracy: 65 },
    { round: 'Round 4', actualPoints: 7, predictedPoints: 6.5, accuracy: 85 },
    { round: 'Round 5', actualPoints: 4, predictedPoints: 4.8, accuracy: 90 }
  ];

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          Performance Tracking
        </CardTitle>
        <CardDescription>
          Historical performance vs predictions over time
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={performanceData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="round" />
            <YAxis />
            <Tooltip 
              formatter={(value, name) => [
                name === 'accuracy' ? `${value}%` : `${value} points`,
                name === 'actualPoints' ? 'Actual Points' :
                name === 'predictedPoints' ? 'Predicted Points' : 'Accuracy'
              ]}
            />
            <Line type="monotone" dataKey="actualPoints" stroke={COLORS.success} strokeWidth={2} name="actualPoints" />
            <Line type="monotone" dataKey="predictedPoints" stroke={COLORS.primary} strokeWidth={2} strokeDasharray="5 5" name="predictedPoints" />
            <Line type="monotone" dataKey="accuracy" stroke={COLORS.warning} strokeWidth={2} name="accuracy" />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

// Community Stats Dashboard
export const CommunityStatsChart = ({ data }) => {
  const communityData = data?.communityStats || {
    totalUsers: 12847,
    averageScore: 5.3,
    successRate: 73,
    topPerformers: [
      { rank: 1, username: 'ProPicker', score: 8.9, accuracy: 95 },
      { rank: 2, username: 'CSGOOracle', score: 8.7, accuracy: 92 },
      { rank: 3, username: 'MajorMaster', score: 8.5, accuracy: 90 }
    ]
  };

  const statsCards = [
    {
      title: 'Active Users',
      value: communityData.totalUsers.toLocaleString(),
      icon: Users,
      color: COLORS.primary,
      change: '+12%'
    },
    {
      title: 'Average Score',
      value: communityData.averageScore.toFixed(1),
      icon: Target,
      color: COLORS.success,
      change: '+0.3'
    },
    {
      title: 'Success Rate',
      value: `${communityData.successRate}%`,
      icon: TrendingUp,
      color: COLORS.warning,
      change: '+5%'
    }
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {statsCards.map((stat, index) => (
          <Card key={index}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">{stat.title}</p>
                  <p className="text-2xl font-bold">{stat.value}</p>
                  <p className="text-xs text-muted-foreground">
                    <span className="text-green-600">{stat.change}</span> from last week
                  </p>
                </div>
                <stat.icon className="h-8 w-8" style={{ color: stat.color }} />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Award className="h-5 w-5" />
            Top Performers
          </CardTitle>
          <CardDescription>
            Leaderboard of the most successful Pick'Em predictors
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {communityData.topPerformers.map((performer) => (
              <div key={performer.rank} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                <div className="flex items-center gap-3">
                  <Badge variant="outline" className="w-8 h-8 rounded-full flex items-center justify-center">
                    {performer.rank}
                  </Badge>
                  <div>
                    <p className="font-medium">{performer.username}</p>
                    <p className="text-sm text-muted-foreground">{performer.accuracy}% accuracy</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-bold text-lg">{performer.score}</p>
                  <p className="text-sm text-muted-foreground">score</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Scenario Comparison Table
export const ScenarioComparisonTable = ({ scenarios }) => {
  if (!scenarios || scenarios.length === 0) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-center text-muted-foreground">No scenarios to compare</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Zap className="h-5 w-5" />
          Scenario Comparison
        </CardTitle>
        <CardDescription>
          Detailed comparison of optimization scenarios
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2">Scenario</th>
                <th className="text-left p-2">Expected Points</th>
                <th className="text-left p-2">Win Probability</th>
                <th className="text-left p-2">Risk Level</th>
                <th className="text-left p-2">Picks Count</th>
                <th className="text-left p-2">Strategy</th>
              </tr>
            </thead>
            <tbody>
              {scenarios.map((scenario, index) => (
                <tr key={index} className="border-b hover:bg-muted/50">
                  <td className="p-2 font-medium">Scenario {index + 1}</td>
                  <td className="p-2">{scenario.expectedPoints.toFixed(1)}</td>
                  <td className="p-2">{(scenario.winProbability * 100).toFixed(1)}%</td>
                  <td className="p-2">
                    <Badge 
                      variant={scenario.riskLevel < 0.3 ? "default" : scenario.riskLevel < 0.7 ? "secondary" : "destructive"}
                    >
                      {scenario.riskLevel < 0.3 ? 'Low' : scenario.riskLevel < 0.7 ? 'Medium' : 'High'}
                    </Badge>
                  </td>
                  <td className="p-2">{scenario.picks?.length || 0}</td>
                  <td className="p-2 text-sm text-muted-foreground">{scenario.strategy || 'Balanced'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
};

// Main Visualization Dashboard Component
export const VisualizationDashboard = ({ optimizationData, communityData, performanceData }) => {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <OptimizationResultsChart data={optimizationData} />
        <RiskRewardChart data={optimizationData} />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PickDistributionChart data={optimizationData} />
        <PerformanceChart data={performanceData} />
      </div>

      <CommunityStatsChart data={communityData} />

      <ScenarioComparisonTable scenarios={optimizationData?.scenarios} />
    </div>
  );
};

export default VisualizationDashboard;

