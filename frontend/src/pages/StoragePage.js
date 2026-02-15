import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
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
import { HardDrive, Plus, Trash2 } from 'lucide-react';
import api from '@/lib/api';
import { toast } from 'sonner';

export default function StoragePage() {
  const [pools, setPools] = useState([]);
  const [loading, setLoading] = useState(true);
  const [addDialog, setAddDialog] = useState(false);
  const [newPool, setNewPool] = useState({
    name: '',
    path: '',
    pool_type: 'local',
  });

  useEffect(() => {
    loadPools();
  }, []);

  const loadPools = async () => {
    try {
      const response = await api.get('/storage/pools');
      setPools(response.data);
    } catch (error) {
      console.error('Error loading storage pools:', error);
      if (loading) {
        toast.error('Failed to load storage pools');
      }
    } finally {
      setLoading(false);
    }
  };

  const addPool = async () => {
    try {
      await api.post('/storage/pools', newPool);
      toast.success('Storage pool added');
      setAddDialog(false);
      setNewPool({ name: '', path: '', pool_type: 'local' });
      await loadPools();
    } catch (error) {
      console.error('Error adding storage pool:', error);
      toast.error(error.response?.data?.detail || 'Failed to add storage pool');
    }
  };

  const removePool = async (poolId) => {
    try {
      await api.delete(`/storage/pools/${poolId}`);
      toast.success('Storage pool removed');
      await loadPools();
    } catch (error) {
      console.error('Error removing storage pool:', error);
      toast.error('Failed to remove storage pool');
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
          <HardDrive className="w-12 h-12 text-primary animate-pulse mx-auto mb-4" />
          <p className="text-muted-foreground">Loading storage pools...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="storage-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-heading font-bold tracking-tight">Storage Pools</h1>
          <p className="text-muted-foreground mt-2">Manage local and remote storage</p>
        </div>
        <Button
          onClick={() => setAddDialog(true)}
          data-testid="add-storage-button"
          className="rounded-sm uppercase tracking-wide font-medium"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Storage
        </Button>
      </div>

      {pools.length === 0 ? (
        <Card className="rounded-sm border-border">
          <CardContent className="py-12 text-center">
            <HardDrive className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-heading font-bold mb-2">No Storage Pools</h3>
            <p className="text-muted-foreground">Add storage pools to manage media storage</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {pools.map((pool) => {
            const usagePercent = (pool.used_space / pool.total_space) * 100;
            return (
              <Card key={pool.id} className="rounded-sm border-border" data-testid={`storage-pool-${pool.name}`}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="font-heading text-lg flex items-center gap-3">
                        <HardDrive className="w-5 h-5 text-primary" />
                        {pool.name}
                      </CardTitle>
                      <div className="mt-2 space-y-1">
                        <p className="text-sm text-muted-foreground font-mono">{pool.mount_point}</p>
                        <Badge variant="outline" className="rounded-sm text-xs font-mono uppercase mt-2">
                          {pool.pool_type}
                        </Badge>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      data-testid={`remove-${pool.name}-button`}
                      onClick={() => removePool(pool.id)}
                      className="rounded-sm text-destructive hover:text-destructive hover:bg-destructive/10"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Used</span>
                      <span className="text-sm font-mono font-bold">{usagePercent.toFixed(1)}%</span>
                    </div>
                    <Progress value={usagePercent} className="h-2" />
                    <div className="flex justify-between text-xs font-mono text-muted-foreground">
                      <span>{formatBytes(pool.used_space)}</span>
                      <span>{formatBytes(pool.total_space)}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      <Dialog open={addDialog} onOpenChange={setAddDialog}>
        <DialogContent className="sm:max-w-md rounded-sm" data-testid="add-storage-dialog">
          <DialogHeader>
            <DialogTitle className="font-heading">Add Storage Pool</DialogTitle>
            <DialogDescription>Configure a new storage location for media files</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="pool-name">Pool Name</Label>
              <Input
                id="pool-name"
                data-testid="pool-name-input"
                placeholder="Media Storage"
                value={newPool.name}
                onChange={(e) => setNewPool({ ...newPool, name: e.target.value })}
                className="rounded-sm"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="mount-point">Mount Point</Label>
              <Input
                id="mount-point"
                data-testid="mount-point-input"
                placeholder="/mnt/media"
                value={newPool.mount_point}
                onChange={(e) => setNewPool({ ...newPool, mount_point: e.target.value })}
                className="rounded-sm font-mono text-sm"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="pool-type">Pool Type</Label>
              <Select value={newPool.pool_type} onValueChange={(value) => setNewPool({ ...newPool, pool_type: value })}>
                <SelectTrigger data-testid="pool-type-select" className="rounded-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="rounded-sm">
                  <SelectItem value="local">Local</SelectItem>
                  <SelectItem value="remote">Remote</SelectItem>
                  <SelectItem value="network">Network</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button
              onClick={addPool}
              data-testid="save-storage-button"
              disabled={!newPool.name || !newPool.mount_point}
              className="rounded-sm uppercase tracking-wide font-medium"
            >
              Add Storage Pool
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}