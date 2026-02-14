import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Activity, RefreshCw } from 'lucide-react';
import api from '@/lib/api';
import { toast } from 'sonner';

export default function ResourceHeatmapPage() {
  const [containers, setContainers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadHeatmap();
    const interval = setInterval(loadHeatmap, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadHeatmap = async () => {
    try {
      const response = await api.get('/advanced/containers/resource-heatmap');
      setContainers(response.data.containers || []);
    } catch (error) {
      console.error('Error loading heatmap:', error);
      if (loading) {
        toast.error('Failed to load resource heatmap');
      }
    } finally {
      setLoading(false);
    }
  };

  const getHeatColor = (percent) => {
    if (percent >= 90) return 'bg-red-500';
    if (percent >= 75) return 'bg-orange-500';
    if (percent >= 50) return 'bg-yellow-500';
    if (percent >= 25) return 'bg-primary';
    return 'bg-green-500';
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
      <div className=\"flex items-center justify-center h-full\">
        <div className=\"text-center\">
          <Activity className=\"w-12 h-12 text-primary animate-pulse mx-auto mb-4\" />
          <p className=\"text-muted-foreground\">Loading resource heatmap...</p>
        </div>
      </div>
    );
  }

  return (
    <div className=\"space-y-6\" data-testid=\"resource-heatmap-page\">
      <div className=\"flex items-center justify-between\">
        <div>
          <h1 className=\"text-4xl font-heading font-bold tracking-tight\">Resource Heatmap</h1>
          <p className=\"text-muted-foreground mt-2\">Real-time container resource visualization</p>
        </div>
        <Button onClick={loadHeatmap} variant=\"outline\" className=\"rounded-sm\">
          <RefreshCw className=\"w-4 h-4 mr-2\" />
          Refresh
        </Button>
      </div>

      {containers.length === 0 ? (
        <Card className=\"rounded-sm border-border\">
          <CardContent className=\"py-12 text-center\">
            <Activity className=\"w-16 h-16 text-muted-foreground mx-auto mb-4\" />
            <h3 className=\"text-lg font-heading font-bold mb-2\">No Running Containers</h3>
            <p className=\"text-muted-foreground\">Start some containers to see resource usage</p>
          </CardContent>
        </Card>
      ) : (
        <div className=\"grid gap-6 md:grid-cols-2 lg:grid-cols-3\">
          {containers.map((container) => (
            <Card key={container.id} className=\"rounded-sm border-border\">
              <CardHeader>
                <CardTitle className=\"font-heading text-lg truncate\">{container.name}</CardTitle>
                <p className=\"text-xs text-muted-foreground font-mono\">{container.id}</p>
              </CardHeader>
              <CardContent className=\"space-y-4\">
                {/* CPU Heatmap */}
                <div>
                  <div className=\"flex justify-between text-sm mb-2\">
                    <span className=\"text-muted-foreground\">CPU</span>
                    <span className=\"font-mono font-bold\">{container.cpu_percent.toFixed(1)}%</span>
                  </div>
                  <div className=\"h-8 bg-secondary rounded-sm overflow-hidden\">
                    <div
                      className={`h-full ${getHeatColor(container.cpu_percent)} transition-all duration-500`}
                      style={{ width: `${Math.min(container.cpu_percent, 100)}%` }}
                    />
                  </div>
                </div>

                {/* Memory Heatmap */}
                <div>
                  <div className=\"flex justify-between text-sm mb-2\">
                    <span className=\"text-muted-foreground\">Memory</span>
                    <span className=\"font-mono font-bold\">{container.memory_percent.toFixed(1)}%</span>
                  </div>
                  <div className=\"h-8 bg-secondary rounded-sm overflow-hidden\">
                    <div
                      className={`h-full ${getHeatColor(container.memory_percent)} transition-all duration-500`}
                      style={{ width: `${Math.min(container.memory_percent, 100)}%` }}
                    />
                  </div>
                  <p className=\"text-xs text-muted-foreground mt-1 font-mono\">
                    {formatBytes(container.memory_usage)} / {formatBytes(container.memory_limit)}
                  </p>
                </div>

                {/* Status */}
                <div className=\"flex justify-between items-center pt-2 border-t border-border\">
                  <span className=\"text-sm text-muted-foreground\">Status</span>
                  <span className={`text-xs font-mono font-bold ${
                    container.status === 'running' ? 'text-primary' : 'text-muted-foreground'
                  }`}>
                    {container.status.toUpperCase()}
                  </span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
