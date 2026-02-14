import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { RefreshCw, Download, CheckCircle2, AlertTriangle, Package } from 'lucide-react';
import api from '@/lib/api';
import { toast } from 'sonner';

export default function UpdatesPage() {
  const navigate = useNavigate();
  const [updates, setUpdates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);
  const [updating, setUpdating] = useState(null);

  useEffect(() => {
    checkForUpdates();
  }, []);

  const checkForUpdates = async () => {
    setChecking(true);
    try {
      const response = await api.get('/advanced/images/updates');
      setUpdates(response.data.updates || []);
      if (response.data.total > 0) {
        toast.info(`${response.data.total} updates available`);
      } else {
        toast.success('All containers are up to date');
      }
    } catch (error) {
      console.error('Error checking updates:', error);
      toast.error('Failed to check for updates');
    } finally {
      setChecking(false);
      setLoading(false);
    }
  };

  const updateContainer = async (containerId) => {
    setUpdating(containerId);
    try {
      await api.post(`/advanced/containers/${containerId}/update`);
      toast.success('Container updated successfully');
      await checkForUpdates();
    } catch (error) {
      console.error('Error updating container:', error);
      toast.error(error.response?.data?.detail || 'Failed to update container');
    } finally {
      setUpdating(null);
    }
  };

  const updateAll = async () => {
    for (const update of updates) {
      if (update.update_available) {
        await updateContainer(update.container_id);
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }
    toast.success('All containers updated');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 text-primary animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Checking for updates...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="updates-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-heading font-bold tracking-tight">Application Updates</h1>
          <p className="text-muted-foreground mt-2">Check and install container image updates</p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={checkForUpdates}
            disabled={checking}
            variant="outline"
            className="rounded-sm uppercase tracking-wide font-medium"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${checking ? 'animate-spin' : ''}`} />
            Check Updates
          </Button>
          {updates.length > 0 && (
            <Button
              onClick={updateAll}
              disabled={updating}
              className="rounded-sm uppercase tracking-wide font-medium"
            >
              <Download className="w-4 h-4 mr-2" />
              Update All
            </Button>
          )}
        </div>
      </div>

      {updates.length === 0 ? (
        <Alert className="rounded-sm border-primary/50 bg-primary/5">
          <CheckCircle2 className="h-4 w-4 text-primary" />
          <AlertDescription>
            All containers are running the latest images. No updates available.
          </AlertDescription>
        </Alert>
      ) : (
        <Alert className="rounded-sm border-yellow-500/50 bg-yellow-500/5">
          <AlertTriangle className="h-4 w-4 text-yellow-500" />
          <AlertDescription>
            {updates.length} container{updates.length > 1 ? 's' : ''} have updates available
          </AlertDescription>
        </Alert>
      )}

      <div className="space-y-4">
        {updates.map((update) => (
          <Card key={update.container_id} className="rounded-sm border-border">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <Package className="w-5 h-5 text-primary" />
                    <CardTitle className="font-heading text-lg">{update.container_name}</CardTitle>
                    <Badge variant="outline" className="rounded-sm text-xs font-mono">
                      UPDATE AVAILABLE
                    </Badge>
                  </div>
                  <CardDescription className="mt-2 font-mono text-xs">
                    {update.image}
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Current Version</p>
                    <Badge variant="secondary" className="rounded-sm text-xs font-mono">
                      {update.current_id}
                    </Badge>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Latest Version</p>
                    <Badge variant="default" className="rounded-sm text-xs font-mono">
                      {update.latest_id}
                    </Badge>
                  </div>
                </div>

                <Alert className="rounded-sm">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription className="text-xs">
                    <strong>Note:</strong> Updating will stop the current container, remove it, and create a new one with the latest image.
                    All data in non-persistent volumes will be lost.
                  </AlertDescription>
                </Alert>

                <Button
                  onClick={() => updateContainer(update.container_id)}
                  disabled={updating === update.container_id}
                  className="w-full rounded-sm uppercase tracking-wide font-medium"
                >
                  {updating === update.container_id ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Updating...
                    </>
                  ) : (
                    <>
                      <Download className="w-4 h-4 mr-2" />
                      Update Container
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}