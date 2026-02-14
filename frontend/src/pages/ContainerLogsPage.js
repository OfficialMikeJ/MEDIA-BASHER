import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ArrowLeft, Download, Search, Pause, Play, X } from 'lucide-react';
import { toast } from 'sonner';

export default function ContainerLogsPage() {
  const { containerId } = useParams();
  const navigate = useNavigate();
  const [logs, setLogs] = useState([]);
  const [filter, setFilter] = useState('');
  const [paused, setPaused] = useState(false);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (!containerId) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/advanced/ws/logs/${containerId}`;
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      toast.success('Connected to container logs');
    };

    ws.onmessage = (event) => {
      if (!paused) {
        setLogs(prev => [...prev, {
          id: Date.now() + Math.random(),
          text: event.data,
          timestamp: new Date().toISOString()
        }]);
      }
    };

    ws.onerror = () => {
      toast.error('WebSocket connection error');
      setConnected(false);
    };

    ws.onclose = () => {
      setConnected(false);
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [containerId, paused]);

  useEffect(() => {
    if (!paused && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, paused]);

  const downloadLogs = () => {
    const logText = logs.map(log => `[${new Date(log.timestamp).toLocaleTimeString()}] ${log.text}`).join('\n');
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `container-${containerId}-logs.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const clearLogs = () => {
    setLogs([]);
  };

  const filteredLogs = logs.filter(log => 
    !filter || log.text.toLowerCase().includes(filter.toLowerCase())
  );

  const getLogColor = (text) => {
    if (text.includes('ERROR') || text.includes('error')) return 'text-red-400';
    if (text.includes('WARN') || text.includes('warning')) return 'text-yellow-400';
    if (text.includes('INFO') || text.includes('info')) return 'text-blue-400';
    return 'text-foreground';
  };

  return (
    <div className="space-y-4" data-testid="container-logs-page">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate('/containers')}
            className="rounded-sm"
          >
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-heading font-bold tracking-tight">Container Logs</h1>
            <p className="text-sm text-muted-foreground mt-1">Container ID: {containerId}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={connected ? 'default' : 'destructive'} className="rounded-sm">
            {connected ? 'CONNECTED' : 'DISCONNECTED'}
          </Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPaused(!paused)}
            className="rounded-sm"
          >
            {paused ? <Play className="w-4 h-4 mr-2" /> : <Pause className="w-4 h-4 mr-2" />}
            {paused ? 'Resume' : 'Pause'}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={downloadLogs}
            className="rounded-sm"
          >
            <Download className="w-4 h-4 mr-2" />
            Download
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={clearLogs}
            className="rounded-sm"
          >
            <X className="w-4 h-4 mr-2" />
            Clear
          </Button>
        </div>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input
          placeholder="Filter logs..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="pl-10 rounded-sm font-mono text-sm"
        />
      </div>

      <Card className="rounded-sm border-border">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium">
            {filteredLogs.length} log entries {filter && `(filtered from ${logs.length})`}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[600px] w-full" ref={scrollRef}>
            <div className="space-y-1 font-mono text-xs">
              {filteredLogs.map((log) => (
                <div key={log.id} className="flex gap-3 hover:bg-accent/50 px-2 py-1 rounded">
                  <span className="text-muted-foreground shrink-0">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                  <span className={`break-all ${getLogColor(log.text)}`}>
                    {log.text}
                  </span>
                </div>
              ))}
              {filteredLogs.length === 0 && (
                <div className="text-center text-muted-foreground py-8">
                  {filter ? 'No logs match your filter' : 'No logs available'}
                </div>
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}