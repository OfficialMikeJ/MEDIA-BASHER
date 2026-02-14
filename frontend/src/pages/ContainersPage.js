import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Box, Play, Square, Trash2, AlertCircle, FileText } from 'lucide-react';
import api from '@/lib/api';
import { toast } from 'sonner';

export default function ContainersPage() {
  const [containers, setContainers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [deleteDialog, setDeleteDialog] = useState({ open: false, container: null });

  useEffect(() => {
    loadContainers();
    const interval = setInterval(loadContainers, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadContainers = async () => {
    try {
      const response = await api.get('/containers/list');
      setContainers(response.data);
    } catch (error) {
      console.error('Error loading containers:', error);
      if (loading) {
        toast.error('Failed to load containers');
      }
    } finally {
      setLoading(false);
    }
  };

  const startContainer = async (containerId) => {
    setActionLoading(containerId);
    try {
      await api.post(`/containers/${containerId}/start`);
      toast.success('Container started');
      await loadContainers();
    } catch (error) {
      console.error('Error starting container:', error);
      toast.error(error.response?.data?.detail || 'Failed to start container');
    } finally {
      setActionLoading(null);
    }
  };

  const stopContainer = async (containerId) => {
    setActionLoading(containerId);
    try {
      await api.post(`/containers/${containerId}/stop`);
      toast.success('Container stopped');
      await loadContainers();
    } catch (error) {
      console.error('Error stopping container:', error);
      toast.error(error.response?.data?.detail || 'Failed to stop container');
    } finally {
      setActionLoading(null);
    }
  };

  const deleteContainer = async () => {
    const containerId = deleteDialog.container?.id;
    setActionLoading(containerId);
    try {
      await api.delete(`/containers/${containerId}`);
      toast.success('Container removed');
      setDeleteDialog({ open: false, container: null });
      await loadContainers();
    } catch (error) {
      console.error('Error deleting container:', error);
      toast.error(error.response?.data?.detail || 'Failed to remove container');
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'running':
        return 'bg-primary text-primary-foreground';
      case 'exited':
        return 'bg-muted text-muted-foreground';
      default:
        return 'bg-secondary text-secondary-foreground';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Box className="w-12 h-12 text-primary animate-pulse mx-auto mb-4" />
          <p className="text-muted-foreground">Loading containers...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="containers-page">
      <div>
        <h1 className="text-4xl font-heading font-bold tracking-tight">Containers</h1>
        <p className="text-muted-foreground mt-2">Manage Docker containers</p>
      </div>

      {containers.length === 0 ? (
        <Card className="rounded-sm border-border">
          <CardContent className="py-12 text-center">
            <Box className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-heading font-bold mb-2">No Containers</h3>
            <p className="text-muted-foreground">Install applications to create containers</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {containers.map((container) => (
            <Card key={container.id} className="rounded-sm border-border" data-testid={`container-${container.name}`}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <CardTitle className="font-heading text-lg flex items-center gap-3">
                      {container.name}
                      <Badge className={`rounded-sm text-xs font-mono uppercase ${getStatusColor(container.status)}`}>
                        {container.status}
                      </Badge>
                    </CardTitle>
                    <div className="mt-2 space-y-1">
                      <p className="text-sm text-muted-foreground font-mono">
                        <span className="text-foreground">Image:</span> {container.image}
                      </p>
                      <p className="text-sm text-muted-foreground font-mono">
                        <span className="text-foreground">ID:</span> {container.id}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    {container.status === 'running' ? (
                      <Button
                        variant="outline"
                        size="sm"
                        data-testid={`stop-${container.name}-button`}
                        onClick={() => stopContainer(container.id)}
                        disabled={actionLoading === container.id}
                        className="rounded-sm"
                      >
                        <Square className="w-4 h-4 mr-2" />
                        Stop
                      </Button>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        data-testid={`start-${container.name}-button`}
                        onClick={() => startContainer(container.id)}
                        disabled={actionLoading === container.id}
                        className="rounded-sm"
                      >
                        <Play className="w-4 h-4 mr-2" />
                        Start
                      </Button>
                    )}
                    <Button
                      variant="destructive"
                      size="sm"
                      data-testid={`delete-${container.name}-button`}
                      onClick={() => setDeleteDialog({ open: true, container })}
                      disabled={actionLoading === container.id}
                      className="rounded-sm"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
            </Card>
          ))}
        </div>
      )}

      <AlertDialog open={deleteDialog.open} onOpenChange={(open) => setDeleteDialog({ open, container: null })}>
        <AlertDialogContent className="rounded-sm" data-testid="delete-container-dialog">
          <AlertDialogHeader>
            <AlertDialogTitle className="font-heading">Remove Container</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to remove <span className="font-mono font-bold">{deleteDialog.container?.name}</span>?
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="rounded-sm">Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={deleteContainer}
              data-testid="confirm-delete-button"
              className="rounded-sm bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Remove
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}