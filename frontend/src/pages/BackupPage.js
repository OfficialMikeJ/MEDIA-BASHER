import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Archive, Download, Upload, Clock, HardDrive } from 'lucide-react';
import api from '@/lib/api';
import { toast } from 'sonner';

export default function BackupPage() {
  const [backups, setBackups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [createDialog, setCreateDialog] = useState(false);
  const [backupConfig, setBackupConfig] = useState({
    backup_path: '/backup',
    backup_mongodb: true,
    include_volumes: [],
    include_containers: []
  });

  useEffect(() => {
    loadBackups();
  }, []);

  const loadBackups = async () => {
    try {
      const response = await api.get('/advanced/backup/list');
      setBackups(response.data.backups || []);
    } catch (error) {
      console.error('Error loading backups:', error);
      if (loading) {
        toast.error('Failed to load backups');
      }
    } finally {
      setLoading(false);
    }
  };

  const createBackup = async () => {
    setCreating(true);
    try {
      const response = await api.post('/advanced/backup/create', backupConfig);
      if (response.data.status === 'completed') {
        toast.success('Backup created successfully');
        setCreateDialog(false);
        await loadBackups();
      } else {
        toast.error('Backup failed: ' + (response.data.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Error creating backup:', error);
      toast.error(error.response?.data?.detail || 'Failed to create backup');
    } finally {
      setCreating(false);
    }
  };

  const restoreBackup = async (backupPath) => {
    if (!confirm('Are you sure you want to restore from this backup? This will overwrite current data.')) {
      return;
    }

    try {
      await api.post('/advanced/backup/restore', null, { params: { backup_path: backupPath } });
      toast.success('Backup restored successfully');
    } catch (error) {
      console.error('Error restoring backup:', error);
      toast.error(error.response?.data?.detail || 'Failed to restore backup');
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
          <Archive className="w-12 h-12 text-primary animate-pulse mx-auto mb-4" />
          <p className="text-muted-foreground">Loading backups...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="backup-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-heading font-bold tracking-tight">Backup & Restore</h1>
          <p className="text-muted-foreground mt-2">Manage system backups and restoration</p>
        </div>
        <Button
          onClick={() => setCreateDialog(true)}
          className="rounded-sm uppercase tracking-wide font-medium"
        >
          <Archive className="w-4 h-4 mr-2" />
          Create Backup
        </Button>
      </div>

      {backups.length === 0 ? (
        <Card className="rounded-sm border-border">
          <CardContent className="py-12 text-center">
            <Archive className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-heading font-bold mb-2">No Backups Yet</h3>
            <p className="text-muted-foreground mb-4">Create your first backup to protect your data</p>
            <Button onClick={() => setCreateDialog(true)} className="rounded-sm uppercase tracking-wide font-medium">
              <Archive className="w-4 h-4 mr-2" />
              Create Backup
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {backups.map((backup) => (
            <Card key={backup.filename} className="rounded-sm border-border">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="font-heading text-lg flex items-center gap-3">
                      <Archive className="w-5 h-5 text-primary" />
                      {backup.filename}
                    </CardTitle>
                    <CardDescription className="mt-2 flex items-center gap-4">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(backup.created).toLocaleString()}
                      </span>
                      <span className="flex items-center gap-1">
                        <HardDrive className="w-3 h-3" />
                        {formatBytes(backup.size)}
                      </span>
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => restoreBackup(backup.path)}
                      className="rounded-sm"
                    >
                      <Upload className="w-4 h-4 mr-2" />
                      Restore
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => window.open(backup.path, '_blank')}
                      className="rounded-sm"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Download
                    </Button>
                  </div>
                </div>
              </CardHeader>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={createDialog} onOpenChange={setCreateDialog}>
        <DialogContent className="sm:max-w-md rounded-sm">
          <DialogHeader>
            <DialogTitle className="font-heading">Create System Backup</DialogTitle>
            <DialogDescription>Configure backup options</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="backup-path">Backup Path</Label>
              <Input
                id="backup-path"
                value={backupConfig.backup_path}
                onChange={(e) => setBackupConfig({ ...backupConfig, backup_path: e.target.value })}
                className="rounded-sm font-mono text-sm"
              />
            </div>

            <div className="flex items-center justify-between py-2">
              <div className="space-y-0.5">
                <Label>Include MongoDB</Label>
                <p className="text-sm text-muted-foreground">Backup database</p>
              </div>
              <Switch
                checked={backupConfig.backup_mongodb}
                onCheckedChange={(checked) => setBackupConfig({ ...backupConfig, backup_mongodb: checked })}
              />
            </div>

            <div className="space-y-2">
              <Label>Include Volumes (comma-separated)</Label>
              <Input
                placeholder="volume1,volume2"
                onChange={(e) => setBackupConfig({
                  ...backupConfig,
                  include_volumes: e.target.value.split(',').filter(v => v.trim())
                })}
                className="rounded-sm font-mono text-sm"
              />
            </div>

            <div className="space-y-2">
              <Label>Include Containers (comma-separated IDs)</Label>
              <Input
                placeholder="container1,container2"
                onChange={(e) => setBackupConfig({
                  ...backupConfig,
                  include_containers: e.target.value.split(',').filter(c => c.trim())
                })}
                className="rounded-sm font-mono text-sm"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              onClick={createBackup}
              disabled={creating}
              className="rounded-sm uppercase tracking-wide font-medium"
            >
              {creating ? 'Creating...' : 'Create Backup'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}