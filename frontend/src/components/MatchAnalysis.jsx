import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell
} from 'recharts';
import { 
  TrendingUp, TrendingDown, Target, AlertTriangle, CheckCircle, 
  Clock, Users, Zap, Shield, Sword, Activity, BarChart3 
} from 'lucide-react';

// Match Analysis Component
export const MatchAnalysis = ({ match, historicalData, oddsData }) => {
  const [selectedTimeframe, setSelectedTimeframe] = useState('7d');

  if (!match) {
    return (
      <Card>
        <CardContent className="p-6 text-center">
          <p className="text-muted-foreground">Select a match to view analysis</p>
        </CardContent>
      </Card>
    );
  }

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConfidenceIcon = (confidence) => {
    if (confidence >= 0.8) return CheckCircle;
    if (confidence >= 0.6) return AlertTriangle;
    return TrendingDown;
  };

  const ConfidenceIcon = getConfidenceIcon(match.confidence);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            {match.teamA} vs {match.teamB}
          </CardTitle>
          <CardDescription>
            {match.tournament} • {new Date(match.startTime).toLocaleString()}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-3">
                  <img 
                    src={match.teamALogo} 
                    alt={match.teamA} 
                    className="w-8 h-8 rounded"
                    onError={(e) => e.target.style.display = 'none'}
                  />
                  <div>
                    <p className="font-semibold">{match.teamA}</p>
                    <p className="text-sm text-muted-foreground">Team A</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold">{(match.teamAWinProbability * 100).toFixed(1)}%</p>
                  <p className="text-sm text-muted-foreground">Win Probability</p>
                </div>
              </div>

              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-3">
                  <img 
                    src={match.teamBLogo} 
                    alt={match.teamB} 
                    className="w-8 h-8 rounded"
                    onError={(e) => e.target.style.display = 'none'}
                  />
                  <div>
                    <p className="font-semibold">{match.teamB}</p>
                    <p className="text-sm text-muted-foreground">Team B</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold">{(match.teamBWinProbability * 100).toFixed(1)}%</p>
                  <p className="text-sm text-muted-foreground">Win Probability</p>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="p-4 border rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <ConfidenceIcon className={`h-5 w-5 ${getConfidenceColor(match.confidence)}`} />
                  <span className="font-semibold">Prediction Confidence</span>
                </div>
                <Progress value={match.confidence * 100} className="mb-2" />
                <p className={`text-sm ${getConfidenceColor(match.confidence)}`}>
                  {(match.confidence * 100).toFixed(1)}% - {
                    match.confidence >= 0.8 ? 'High Confidence' :
                    match.confidence >= 0.6 ? 'Medium Confidence' : 'Low Confidence'
                  }
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-muted/50 rounded-lg text-center">
                  <p className="text-sm text-muted-foreground">Expected Value</p>
                  <p className="text-lg font-bold">{match.expectedValue?.toFixed(2) || 'N/A'}</p>
                </div>
                <div className="p-3 bg-muted/50 rounded-lg text-center">
                  <p className="text-sm text-muted-foreground">Risk Level</p>
                  <p className="text-lg font-bold">{(match.riskLevel * 100).toFixed(0)}%</p>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="odds" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="odds">Odds Analysis</TabsTrigger>
          <TabsTrigger value="history">Head-to-Head</TabsTrigger>
          <TabsTrigger value="form">Recent Form</TabsTrigger>
          <TabsTrigger value="stats">Team Stats</TabsTrigger>
        </TabsList>

        <TabsContent value="odds">
          <OddsAnalysisTab match={match} oddsData={oddsData} />
        </TabsContent>

        <TabsContent value="history">
          <HeadToHeadTab match={match} historicalData={historicalData} />
        </TabsContent>

        <TabsContent value="form">
          <RecentFormTab match={match} />
        </TabsContent>

        <TabsContent value="stats">
          <TeamStatsTab match={match} />
        </TabsContent>
      </Tabs>
    </div>
  );
};

// Odds Analysis Tab
const OddsAnalysisTab = ({ match, oddsData }) => {
  const oddsHistory = oddsData?.history || [
    { time: '2024-01-01', teamAOdds: 1.8, teamBOdds: 2.1 },
    { time: '2024-01-02', teamAOdds: 1.75, teamBOdds: 2.15 },
    { time: '2024-01-03', teamAOdds: 1.7, teamBOdds: 2.2 },
    { time: '2024-01-04', teamAOdds: 1.65, teamBOdds: 2.3 },
    { time: '2024-01-05', teamAOdds: 1.6, teamBOdds: 2.4 }
  ];

  const bookmakerOdds = oddsData?.bookmakers || [
    { name: 'Bet365', teamAOdds: 1.65, teamBOdds: 2.3, margin: 4.2 },
    { name: 'Pinnacle', teamAOdds: 1.68, teamBOdds: 2.25, margin: 3.8 },
    { name: 'Betway', teamAOdds: 1.62, teamBOdds: 2.35, margin: 4.5 },
    { name: 'Unibet', teamAOdds: 1.7, teamBOdds: 2.2, margin: 4.1 }
  ];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Odds Movement
          </CardTitle>
          <CardDescription>
            Historical odds changes over time
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={oddsHistory}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip 
                formatter={(value, name) => [
                  value.toFixed(2),
                  name === 'teamAOdds' ? match.teamA : match.teamB
                ]}
              />
              <Line type="monotone" dataKey="teamAOdds" stroke="#8b5cf6" strokeWidth={2} />
              <Line type="monotone" dataKey="teamBOdds" stroke="#06b6d4" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Bookmaker Comparison</CardTitle>
          <CardDescription>
            Current odds across different bookmakers
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {bookmakerOdds.map((bookmaker, index) => (
              <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="font-medium">{bookmaker.name}</div>
                <div className="flex items-center gap-4">
                  <div className="text-center">
                    <p className="text-sm text-muted-foreground">{match.teamA}</p>
                    <p className="font-bold">{bookmaker.teamAOdds.toFixed(2)}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-muted-foreground">{match.teamB}</p>
                    <p className="font-bold">{bookmaker.teamBOdds.toFixed(2)}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-muted-foreground">Margin</p>
                    <p className="font-bold">{bookmaker.margin.toFixed(1)}%</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Head-to-Head Tab
const HeadToHeadTab = ({ match, historicalData }) => {
  const h2hData = historicalData?.headToHead || [
    { date: '2023-12-15', tournament: 'IEM Katowice', winner: match.teamA, score: '2-1' },
    { date: '2023-11-20', tournament: 'BLAST Premier', winner: match.teamB, score: '2-0' },
    { date: '2023-10-05', tournament: 'ESL Pro League', winner: match.teamA, score: '2-1' },
    { date: '2023-08-12', tournament: 'PGL Major', winner: match.teamA, score: '2-0' },
    { date: '2023-06-30', tournament: 'IEM Cologne', winner: match.teamB, score: '2-1' }
  ];

  const teamAWins = h2hData.filter(game => game.winner === match.teamA).length;
  const teamBWins = h2hData.filter(game => game.winner === match.teamB).length;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Head-to-Head Record</CardTitle>
          <CardDescription>
            Recent matches between these teams
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="text-center p-4 bg-muted/50 rounded-lg">
              <p className="text-2xl font-bold text-green-600">{teamAWins}</p>
              <p className="text-sm text-muted-foreground">{match.teamA} Wins</p>
            </div>
            <div className="text-center p-4 bg-muted/50 rounded-lg">
              <p className="text-2xl font-bold">{h2hData.length}</p>
              <p className="text-sm text-muted-foreground">Total Matches</p>
            </div>
            <div className="text-center p-4 bg-muted/50 rounded-lg">
              <p className="text-2xl font-bold text-blue-600">{teamBWins}</p>
              <p className="text-sm text-muted-foreground">{match.teamB} Wins</p>
            </div>
          </div>

          <div className="space-y-3">
            {h2hData.map((game, index) => (
              <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <p className="font-medium">{game.tournament}</p>
                  <p className="text-sm text-muted-foreground">{game.date}</p>
                </div>
                <div className="text-center">
                  <p className="font-bold">{game.score}</p>
                  <Badge variant={game.winner === match.teamA ? "default" : "secondary"}>
                    {game.winner} Won
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Recent Form Tab
const RecentFormTab = ({ match }) => {
  const teamAForm = [
    { opponent: 'FaZe', result: 'W', score: '2-1', date: '2024-01-10' },
    { opponent: 'G2', result: 'L', score: '1-2', date: '2024-01-08' },
    { opponent: 'Vitality', result: 'W', score: '2-0', date: '2024-01-05' },
    { opponent: 'NAVI', result: 'W', score: '2-1', date: '2024-01-03' },
    { opponent: 'Astralis', result: 'L', score: '0-2', date: '2024-01-01' }
  ];

  const teamBForm = [
    { opponent: 'Liquid', result: 'W', score: '2-0', date: '2024-01-09' },
    { opponent: 'NIP', result: 'W', score: '2-1', date: '2024-01-07' },
    { opponent: 'Heroic', result: 'L', score: '1-2', date: '2024-01-04' },
    { opponent: 'ENCE', result: 'W', score: '2-0', date: '2024-01-02' },
    { opponent: 'Mouz', result: 'W', score: '2-1', date: '2023-12-30' }
  ];

  const getFormColor = (result) => {
    return result === 'W' ? 'bg-green-500' : 'bg-red-500';
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              {match.teamA} Recent Form
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-1 mb-4">
              {teamAForm.map((game, index) => (
                <div
                  key={index}
                  className={`w-8 h-8 rounded flex items-center justify-center text-white text-sm font-bold ${getFormColor(game.result)}`}
                >
                  {game.result}
                </div>
              ))}
            </div>
            <div className="space-y-2">
              {teamAForm.map((game, index) => (
                <div key={index} className="flex items-center justify-between text-sm">
                  <span>vs {game.opponent}</span>
                  <span className={game.result === 'W' ? 'text-green-600' : 'text-red-600'}>
                    {game.score}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sword className="h-5 w-5" />
              {match.teamB} Recent Form
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-1 mb-4">
              {teamBForm.map((game, index) => (
                <div
                  key={index}
                  className={`w-8 h-8 rounded flex items-center justify-center text-white text-sm font-bold ${getFormColor(game.result)}`}
                >
                  {game.result}
                </div>
              ))}
            </div>
            <div className="space-y-2">
              {teamBForm.map((game, index) => (
                <div key={index} className="flex items-center justify-between text-sm">
                  <span>vs {game.opponent}</span>
                  <span className={game.result === 'W' ? 'text-green-600' : 'text-red-600'}>
                    {game.score}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// Team Stats Tab
const TeamStatsTab = ({ match }) => {
  const teamStats = {
    [match.teamA]: {
      rating: 1.15,
      kd: 1.23,
      adr: 78.5,
      kast: 72.3,
      mapWinRate: 68.2,
      pistolWinRate: 55.4
    },
    [match.teamB]: {
      rating: 1.08,
      kd: 1.18,
      adr: 75.2,
      kast: 69.8,
      mapWinRate: 64.7,
      pistolWinRate: 52.1
    }
  };

  const comparisonData = [
    { stat: 'Rating', teamA: teamStats[match.teamA].rating, teamB: teamStats[match.teamB].rating },
    { stat: 'K/D', teamA: teamStats[match.teamA].kd, teamB: teamStats[match.teamB].kd },
    { stat: 'ADR', teamA: teamStats[match.teamA].adr, teamB: teamStats[match.teamB].adr },
    { stat: 'KAST%', teamA: teamStats[match.teamA].kast, teamB: teamStats[match.teamB].kast },
    { stat: 'Map Win%', teamA: teamStats[match.teamA].mapWinRate, teamB: teamStats[match.teamB].mapWinRate },
    { stat: 'Pistol Win%', teamA: teamStats[match.teamA].pistolWinRate, teamB: teamStats[match.teamB].pistolWinRate }
  ];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Team Statistics Comparison
          </CardTitle>
          <CardDescription>
            Key performance metrics for both teams
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={comparisonData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="stat" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="teamA" fill="#8b5cf6" name={match.teamA} />
              <Bar dataKey="teamB" fill="#06b6d4" name={match.teamB} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>{match.teamA} Detailed Stats</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(teamStats[match.teamA]).map(([key, value]) => (
                <div key={key} className="flex justify-between items-center">
                  <span className="text-sm font-medium capitalize">{key.replace(/([A-Z])/g, ' $1')}</span>
                  <span className="font-bold">{typeof value === 'number' ? value.toFixed(1) : value}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{match.teamB} Detailed Stats</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(teamStats[match.teamB]).map(([key, value]) => (
                <div key={key} className="flex justify-between items-center">
                  <span className="text-sm font-medium capitalize">{key.replace(/([A-Z])/g, ' $1')}</span>
                  <span className="font-bold">{typeof value === 'number' ? value.toFixed(1) : value}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default MatchAnalysis;

