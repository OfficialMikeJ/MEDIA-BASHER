import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity, TrendingUp, Clock, Database } from 'lucide-react';
import api from '@/lib/api';
import { toast } from 'sonner';

export default function MonitoringPage() {
  const [metrics, setMetrics] = useState([]);
  const [aggregated, setAggregated] = useState(null);
  const [timeRange, setTimeRange] = useState('1');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMetrics();
    const interval = setInterval(loadMetrics, 60000); // Update every minute
    return () => clearInterval(interval);
  }, [timeRange]);

  const loadMetrics = async () => {
    try {
      const response = await api.get('/system/metrics');
      // Transform single metrics response to array format for charts
      const currentMetrics = response.data;
      const timestamp = new Date().toISOString();
      
      setMetrics(prev => [...prev.slice(-50), { // Keep last 50 data points
        timestamp,
        cpu_percent: currentMetrics.cpu_percent,
        ram_percent: currentMetrics.memory_percent,
        disk_percent: currentMetrics.disk_percent
      }]);
      
      // Calculate aggregated data from current metrics
      setAggregated({
        cpu_avg: currentMetrics.cpu_percent,
        cpu_max: currentMetrics.cpu_percent,
        ram_avg: currentMetrics.memory_percent,
        ram_max: currentMetrics.memory_percent,
        disk_avg: currentMetrics.disk_percent,
        data_points: metrics.length + 1,
        time_range_hours: parseInt(timeRange)
      });
    } catch (error) {
      console.error('Error loading metrics:', error);
      if (loading) {
        toast.error('Failed to load system metrics');
      }
    } finally {
      setLoading(false);
    }
  };

  const startCollection = async () => {
    try {
      await api.post('/advanced/metrics/start-collection');
      toast.success('Metrics collection started');
      setTimeout(loadMetrics, 2000);
    } catch (error) {
      toast.error('Failed to start collection');
    }
  };

  const formatTime = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const chartData = metrics.map(m => ({
    time: formatTime(m.timestamp),
    cpu: m.cpu_percent,
    ram: m.ram_percent,
    disk: m.disk_percent
  }));

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Activity className="w-12 h-12 text-primary animate-pulse mx-auto mb-4" />
          <p className="text-muted-foreground">Loading monitoring data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="monitoring-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-heading font-bold tracking-tight">Advanced Monitoring</h1>
          <p className="text-muted-foreground mt-2">Historical performance metrics and analytics</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={loadMetrics} className="rounded-sm">
            <Activity className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          {metrics.length === 0 && (
            <Button onClick={startCollection} className="rounded-sm uppercase tracking-wide font-medium">
              Start Collection
            </Button>
          )}
        </div>
      </div>

      <Tabs value={timeRange} onValueChange={setTimeRange} className="w-full">
        <TabsList className="rounded-sm">
          <TabsTrigger value="1" className="rounded-sm">Last Hour</TabsTrigger>
          <TabsTrigger value="6" className="rounded-sm">Last 6 Hours</TabsTrigger>
          <TabsTrigger value="24" className="rounded-sm">Last 24 Hours</TabsTrigger>
          <TabsTrigger value="168" className="rounded-sm">Last Week</TabsTrigger>
        </TabsList>
      </Tabs>

      {aggregated && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card className="rounded-sm border-border">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
                Avg CPU
              </CardTitle>
              <TrendingUp className="w-4 h-4 text-blue-400" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-heading font-bold">{aggregated.cpu_avg.toFixed(1)}%</div>
              <p className="text-xs text-muted-foreground mt-1">Peak: {aggregated.cpu_max.toFixed(1)}%</p>
            </CardContent>
          </Card>

          <Card className="rounded-sm border-border">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
                Avg RAM
              </CardTitle>
              <Database className="w-4 h-4 text-purple-400" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-heading font-bold">{aggregated.ram_avg.toFixed(1)}%</div>
              <p className="text-xs text-muted-foreground mt-1">Peak: {aggregated.ram_max.toFixed(1)}%</p>
            </CardContent>
          </Card>

          <Card className="rounded-sm border-border">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
                Avg Disk
              </CardTitle>
              <TrendingUp className="w-4 h-4 text-yellow-400" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-heading font-bold">{aggregated.disk_avg.toFixed(1)}%</div>
              <p className="text-xs text-muted-foreground mt-1">Storage usage</p>
            </CardContent>
          </Card>

          <Card className="rounded-sm border-border">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
                Data Points
              </CardTitle>
              <Clock className="w-4 h-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-heading font-bold">{aggregated.data_points}</div>
              <p className="text-xs text-muted-foreground mt-1">{aggregated.time_range_hours}h period</p>
            </CardContent>
          </Card>
        </div>
      )}

      {metrics.length === 0 ? (
        <Card className="rounded-sm border-border">
          <CardContent className="py-12 text-center">
            <Activity className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-heading font-bold mb-2">No Metrics Data</h3>
            <p className="text-muted-foreground mb-4">Start collecting metrics to see historical data</p>
            <Button onClick={startCollection} className="rounded-sm uppercase tracking-wide font-medium">
              Start Collection
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          <Card className="rounded-sm border-border">
            <CardHeader>
              <CardTitle className="font-heading">CPU Usage Over Time</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="cpuGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                  <XAxis dataKey="time" stroke="#71717a" style={{ fontSize: '12px' }} />
                  <YAxis stroke="#71717a" style={{ fontSize: '12px' }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#18181b', border: '1px solid #27272a', borderRadius: '4px' }}
                    labelStyle={{ color: '#a1a1aa' }}
                  />
                  <Area type="monotone" dataKey="cpu" stroke="#10b981" fillOpacity={1} fill="url(#cpuGradient)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card className="rounded-sm border-border">
            <CardHeader>
              <CardTitle className="font-heading">Memory Usage Over Time</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="ramGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                  <XAxis dataKey="time" stroke="#71717a" style={{ fontSize: '12px' }} />
                  <YAxis stroke="#71717a" style={{ fontSize: '12px' }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#18181b', border: '1px solid #27272a', borderRadius: '4px' }}
                    labelStyle={{ color: '#a1a1aa' }}
                  />
                  <Area type="monotone" dataKey="ram" stroke="#8b5cf6" fillOpacity={1} fill="url(#ramGradient)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card className="rounded-sm border-border">
            <CardHeader>
              <CardTitle className="font-heading">Disk Usage Over Time</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                  <XAxis dataKey="time" stroke="#71717a" style={{ fontSize: '12px' }} />
                  <YAxis stroke="#71717a" style={{ fontSize: '12px' }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#18181b', border: '1px solid #27272a', borderRadius: '4px' }}
                    labelStyle={{ color: '#a1a1aa' }}
                  />
                  <Line type="monotone" dataKey="disk" stroke="#f59e0b" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}