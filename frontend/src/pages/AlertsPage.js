import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { AlertTriangle, Plus, Trash2, Bell, Play, Pause } from 'lucide-react';
import api from '@/lib/api';
import { toast } from 'sonner';

export default function AlertsPage() {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [monitoring, setMonitoring] = useState(false);
  const [createDialog, setCreateDialog] = useState(false);
  const [newRule, setNewRule] = useState({
    name: '',
    metric: 'cpu',
    threshold: 80,
    comparison: 'gt',
    enabled: true
  });

  useEffect(() => {
    loadRules();
  }, []);

  const loadRules = async () => {
    try {
      const response = await api.get('/advanced/alerts/rules');
      setRules(response.data.rules || []);
    } catch (error) {
      console.error('Error loading alert rules:', error);
      if (loading) {
        toast.error('Failed to load alert rules');
      }
    } finally {
      setLoading(false);
    }
  };

  const createRule = async () => {
    try {
      await api.post('/advanced/alerts/rules', newRule);
      toast.success('Alert rule created');
      setCreateDialog(false);
      setNewRule({ name: '', metric: 'cpu', threshold: 80, comparison: 'gt', enabled: true });
      await loadRules();
    } catch (error) {
      toast.error('Failed to create alert rule');
    }
  };

  const deleteRule = async (ruleId) => {
    try {
      await api.delete(`/advanced/alerts/rules/${ruleId}`);
      toast.success('Alert rule deleted');
      await loadRules();
    } catch (error) {
      toast.error('Failed to delete rule');
    }
  };

  const toggleRule = async (ruleId, enabled) => {
    try {
      await api.put(`/advanced/alerts/rules/${ruleId}`, { enabled: !enabled });
      toast.success('Alert rule updated');
      await loadRules();
    } catch (error) {
      toast.error('Failed to update rule');
    }
  };

  const startMonitoring = async () => {
    try {
      await api.post('/advanced/alerts/start-monitoring');
      setMonitoring(true);
      toast.success('Alert monitoring started');
    } catch (error) {
      toast.error('Failed to start monitoring');
    }
  };

  const stopMonitoring = async () => {
    try {
      await api.post('/advanced/alerts/stop-monitoring');
      setMonitoring(false);
      toast.success('Alert monitoring stopped');
    } catch (error) {
      toast.error('Failed to stop monitoring');
    }
  };

  const getMetricColor = (metric) => {
    const colors = {
      cpu: 'bg-blue-500/10 text-blue-400',
      ram: 'bg-purple-500/10 text-purple-400',
      disk: 'bg-yellow-500/10 text-yellow-400',
    };
    return colors[metric] || 'bg-muted text-muted-foreground';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 text-primary animate-pulse mx-auto mb-4" />
          <p className="text-muted-foreground">Loading alerts...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="alerts-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-heading font-bold tracking-tight">Alert Rules</h1>
          <p className="text-muted-foreground mt-2">Configure threshold-based alerts for system metrics</p>
        </div>
        <div className="flex gap-2">
          {monitoring ? (
            <Button onClick={stopMonitoring} variant="outline" className="rounded-sm">
              <Pause className="w-4 h-4 mr-2" />
              Stop Monitoring
            </Button>
          ) : (
            <Button onClick={startMonitoring} variant="outline" className="rounded-sm">
              <Play className="w-4 h-4 mr-2" />
              Start Monitoring
            </Button>
          )}
          <Button onClick={() => setCreateDialog(true)} className="rounded-sm uppercase tracking-wide font-medium">
            <Plus className="w-4 h-4 mr-2" />
            Add Rule
          </Button>
        </div>
      </div>

      {rules.length === 0 ? (
        <Card className="rounded-sm border-border">
          <CardContent className="py-12 text-center">
            <Bell className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-heading font-bold mb-2">No Alert Rules</h3>
            <p className="text-muted-foreground mb-4">Create your first alert rule to monitor system metrics</p>
            <Button onClick={() => setCreateDialog(true)} className="rounded-sm uppercase tracking-wide font-medium">
              <Plus className="w-4 h-4 mr-2" />
              Add Rule
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {rules.map((rule) => (
            <Card key={rule.id} className="rounded-sm border-border">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="font-heading text-lg flex items-center gap-3">
                      {rule.name}
                      <Badge className={`rounded-sm text-xs font-mono uppercase ${getMetricColor(rule.metric)}`}>
                        {rule.metric}
                      </Badge>
                    </CardTitle>
                    <CardDescription className="mt-2">
                      Alert when {rule.metric} is {rule.comparison === 'gt' ? 'greater than' : 'less than'} {rule.threshold}%
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Switch
                      checked={rule.enabled}
                      onCheckedChange={() => toggleRule(rule.id, rule.enabled)}
                    />
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => deleteRule(rule.id)}
                      className="rounded-sm text-destructive hover:text-destructive hover:bg-destructive/10"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Status</span>
                    <Badge variant={rule.enabled ? 'default' : 'secondary'} className="rounded-sm text-xs">
                      {rule.enabled ? 'ACTIVE' : 'DISABLED'}
                    </Badge>
                  </div>
                  {rule.last_triggered && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Last Triggered</span>
                      <span className="text-xs font-mono">{new Date(rule.last_triggered).toLocaleString()}</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={createDialog} onOpenChange={setCreateDialog}>
        <DialogContent className="sm:max-w-md rounded-sm">
          <DialogHeader>
            <DialogTitle className="font-heading">Create Alert Rule</DialogTitle>
            <DialogDescription>Configure a new threshold-based alert</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="rule-name">Rule Name</Label>
              <Input
                id="rule-name"
                placeholder="High CPU Usage"
                value={newRule.name}
                onChange={(e) => setNewRule({ ...newRule, name: e.target.value })}
                className="rounded-sm"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="metric">Metric</Label>
              <Select value={newRule.metric} onValueChange={(value) => setNewRule({ ...newRule, metric: value })}>
                <SelectTrigger className="rounded-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="rounded-sm">
                  <SelectItem value="cpu">CPU Usage</SelectItem>
                  <SelectItem value="ram">RAM Usage</SelectItem>
                  <SelectItem value="disk">Disk Usage</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="comparison">Condition</Label>
              <Select value={newRule.comparison} onValueChange={(value) => setNewRule({ ...newRule, comparison: value })}>
                <SelectTrigger className="rounded-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="rounded-sm">
                  <SelectItem value="gt">Greater Than</SelectItem>
                  <SelectItem value="lt">Less Than</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="threshold">Threshold (%)</Label>
              <Input
                id="threshold"
                type="number"
                min="0"
                max="100"
                value={newRule.threshold}
                onChange={(e) => setNewRule({ ...newRule, threshold: parseFloat(e.target.value) })}
                className="rounded-sm"
              />
            </div>
            <div className="flex items-center justify-between">
              <Label>Enabled</Label>
              <Switch
                checked={newRule.enabled}
                onCheckedChange={(checked) => setNewRule({ ...newRule, enabled: checked })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              onClick={createRule}
              disabled={!newRule.name}
              className="rounded-sm uppercase tracking-wide font-medium"
            >
              Create Rule
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}