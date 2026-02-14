import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Cpu, MemoryStick, HardDrive, Layers, Activity, AlertCircle } from 'lucide-react';
import api from '@/lib/api';
import { toast } from 'sonner';

export default function DashboardPage() {
  const [metrics, setMetrics] = useState(null);
  const [containers, setContainers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [metricsRes, containersRes] = await Promise.all([
        api.get('/system/metrics'),
        api.get('/containers/list'),
      ]);
      setMetrics(metricsRes.data);
      setContainers(containersRes.data);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      if (loading) {
        toast.error('Failed to load system metrics');
      }
    } finally {
      setLoading(false);
    }
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Activity className="w-12 h-12 text-primary animate-pulse mx-auto mb-4" />
          <p className="text-muted-foreground">Loading system metrics...</p>
        </div>
      </div>
    );
  }

  const runningContainers = containers.filter((c) => c.status === 'running').length;

  return (
    <div className="space-y-6" data-testid="dashboard-page">
      <div>
        <h1 className="text-4xl font-heading font-bold tracking-tight">System Overview</h1>
        <p className="text-muted-foreground mt-2">Real-time server performance metrics</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="metric-card rounded-sm border-border" data-testid="cpu-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
              CPU Usage
            </CardTitle>
            <Cpu className="w-4 h-4 text-primary" strokeWidth={1.5} />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-heading font-bold stat-value">{metrics?.cpu_percent?.toFixed(1)}%</div>
            <Progress value={metrics?.cpu_percent || 0} className="mt-2 h-1.5" />
            <p className="text-xs text-muted-foreground mt-2 font-mono">{metrics?.cpu_count} Cores</p>
          </CardContent>
        </Card>

        <Card className="metric-card rounded-sm border-border" data-testid="ram-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
              RAM Usage
            </CardTitle>
            <MemoryStick className="w-4 h-4 text-primary" strokeWidth={1.5} />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-heading font-bold stat-value">{metrics?.ram_percent?.toFixed(1)}%</div>
            <Progress value={metrics?.ram_percent || 0} className="mt-2 h-1.5" />
            <p className="text-xs text-muted-foreground mt-2 font-mono">
              {formatBytes(metrics?.ram_used || 0)} / {formatBytes(metrics?.ram_total || 0)}
            </p>
          </CardContent>
        </Card>

        <Card className="metric-card rounded-sm border-border" data-testid="storage-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
              Storage
            </CardTitle>
            <HardDrive className="w-4 h-4 text-primary" strokeWidth={1.5} />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-heading font-bold stat-value">
              {metrics?.storage_percent?.toFixed(1)}%
            </div>
            <Progress value={metrics?.storage_percent || 0} className="mt-2 h-1.5" />
            <p className="text-xs text-muted-foreground mt-2 font-mono">
              {formatBytes(metrics?.storage_used || 0)} / {formatBytes(metrics?.storage_total || 0)}
            </p>
          </CardContent>
        </Card>

        <Card className="metric-card rounded-sm border-border" data-testid="gpu-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
              GPU Status
            </CardTitle>
            <Layers className="w-4 h-4 text-primary" strokeWidth={1.5} />
          </CardHeader>
          <CardContent>
            {metrics?.gpu_info?.installed ? (
              <>
                <div className="text-3xl font-heading font-bold stat-value text-primary">ACTIVE</div>
                <p className="text-xs text-muted-foreground mt-2 font-mono">
                  {metrics.gpu_info.gpus?.[0]?.name || 'GPU Detected'}
                </p>
                {metrics.gpu_info.gpus?.[0]?.memory_total && (
                  <p className="text-xs text-muted-foreground font-mono">
                    VRAM: {formatBytes(metrics.gpu_info.gpus[0].memory_used)} /{' '}
                    {formatBytes(metrics.gpu_info.gpus[0].memory_total)}
                  </p>
                )}
              </>
            ) : (
              <>
                <div className="text-3xl font-heading font-bold stat-value text-muted-foreground">N/A</div>
                <p className="text-xs text-muted-foreground mt-2">No GPU Detected</p>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card className="rounded-sm border-border" data-testid="containers-summary-card">
          <CardHeader>
            <CardTitle className="font-heading">Container Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Total Containers</span>
                <span className="text-2xl font-heading font-bold">{containers.length}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Running</span>
                <span className="text-2xl font-heading font-bold text-primary">{runningContainers}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Stopped</span>
                <span className="text-2xl font-heading font-bold text-muted-foreground">
                  {containers.length - runningContainers}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-sm border-border" data-testid="quick-info-card">
          <CardHeader>
            <CardTitle className="font-heading">System Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between items-center py-2 border-b border-border">
                <span className="text-sm text-muted-foreground">Platform</span>
                <span className="text-sm font-mono">Ubuntu 24.04 LTS</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-border">
                <span className="text-sm text-muted-foreground">Docker</span>
                <span className="text-sm font-mono text-primary">Active</span>
              </div>
              <div className="flex justify-between items-center py-2">
                <span className="text-sm text-muted-foreground">Panel Version</span>
                <span className="text-sm font-mono">v1.0.0</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {containers.length === 0 && (
        <Alert className="rounded-sm" data-testid="no-containers-alert">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            No containers installed yet. Visit the Applications page to install media server applications.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}