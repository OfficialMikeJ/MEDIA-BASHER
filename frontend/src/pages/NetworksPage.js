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
import { Network, Plus, Trash2, Globe } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
import api from '@/lib/api';
import { toast } from 'sonner';

export default function NetworksPage() {
  const [networks, setNetworks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [createDialog, setCreateDialog] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState({ open: false, network: null });
  const [newNetwork, setNewNetwork] = useState({
    name: '',
    driver: 'bridge'
  });

  useEffect(() => {
    loadNetworks();
  }, []);

  const loadNetworks = async () => {
    try {
      const response = await api.get('/advanced/networks');
      setNetworks(response.data.networks || []);
    } catch (error) {
      console.error('Error loading networks:', error);
      toast.error('Failed to load networks');
    } finally {
      setLoading(false);
    }
  };

  const createNetwork = async () => {
    try {
      await api.post('/advanced/networks', null, {
        params: { name: newNetwork.name, driver: newNetwork.driver }
      });
      toast.success('Network created');
      setCreateDialog(false);
      setNewNetwork({ name: '', driver: 'bridge' });
      await loadNetworks();
    } catch (error) {
      console.error('Error creating network:', error);
      toast.error(error.response?.data?.detail || 'Failed to create network');
    }
  };

  const removeNetwork = async () => {
    const networkId = deleteDialog.network?.id;
    try {
      await api.delete(`/advanced/networks/${networkId}`);
      toast.success('Network removed');
      setDeleteDialog({ open: false, network: null });
      await loadNetworks();
    } catch (error) {
      console.error('Error removing network:', error);
      toast.error(error.response?.data?.detail || 'Failed to remove network');
    }
  };

  const getDriverColor = (driver) => {
    const colors = {
      bridge: 'bg-blue-500/10 text-blue-400',
      host: 'bg-purple-500/10 text-purple-400',
      overlay: 'bg-green-500/10 text-green-400',
      macvlan: 'bg-yellow-500/10 text-yellow-400',
    };
    return colors[driver] || 'bg-muted text-muted-foreground';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Network className="w-12 h-12 text-primary animate-pulse mx-auto mb-4" />
          <p className="text-muted-foreground">Loading networks...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="networks-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-heading font-bold tracking-tight">Docker Networks</h1>
          <p className="text-muted-foreground mt-2">Manage container network configurations</p>
        </div>
        <Button
          onClick={() => setCreateDialog(true)}
          className="rounded-sm uppercase tracking-wide font-medium"
        >
          <Plus className="w-4 h-4 mr-2" />
          Create Network
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {networks.map((network) => (
          <Card key={network.id} className="rounded-sm border-border" data-testid={`network-${network.name}`}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <Globe className="w-5 h-5 text-primary" />
                    <CardTitle className="font-heading text-lg">{network.name}</CardTitle>
                  </div>
                  <div className="mt-3 space-y-2">
                    <Badge className={`rounded-sm text-xs font-mono uppercase ${getDriverColor(network.driver)}`}>
                      {network.driver}
                    </Badge>
                    <p className="text-xs text-muted-foreground">Scope: {network.scope}</p>
                  </div>
                </div>
                {!['bridge', 'host', 'none'].includes(network.name) && (
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setDeleteDialog({ open: true, network })}
                    className="rounded-sm text-destructive hover:text-destructive hover:bg-destructive/10"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex justify-between items-center py-2 border-t border-border">
                <span className="text-sm text-muted-foreground">Containers</span>
                <span className="text-sm font-mono font-bold">{network.containers}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-t border-border">
                <span className="text-sm text-muted-foreground">Network ID</span>
                <span className="text-xs font-mono text-muted-foreground">{network.id}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Dialog open={createDialog} onOpenChange={setCreateDialog}>
        <DialogContent className="sm:max-w-md rounded-sm">
          <DialogHeader>
            <DialogTitle className="font-heading">Create Docker Network</DialogTitle>
            <DialogDescription>Configure a new network for your containers</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="network-name">Network Name</Label>
              <Input
                id="network-name"
                placeholder="my-network"
                value={newNetwork.name}
                onChange={(e) => setNewNetwork({ ...newNetwork, name: e.target.value })}
                className="rounded-sm"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="network-driver">Driver</Label>
              <Select value={newNetwork.driver} onValueChange={(value) => setNewNetwork({ ...newNetwork, driver: value })}>
                <SelectTrigger className="rounded-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="rounded-sm">
                  <SelectItem value="bridge">Bridge</SelectItem>
                  <SelectItem value="overlay">Overlay</SelectItem>
                  <SelectItem value="macvlan">Macvlan</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                Bridge: Single host networking (default)<br/>
                Overlay: Multi-host swarm networking<br/>
                Macvlan: Direct MAC address assignment
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button
              onClick={createNetwork}
              disabled={!newNetwork.name}
              className="rounded-sm uppercase tracking-wide font-medium"
            >
              Create Network
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={deleteDialog.open} onOpenChange={(open) => setDeleteDialog({ open, network: null })}>
        <AlertDialogContent className="rounded-sm">
          <AlertDialogHeader>
            <AlertDialogTitle className="font-heading">Remove Network</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to remove network <span className="font-mono font-bold">{deleteDialog.network?.name}</span>?
              All containers must be disconnected first.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="rounded-sm">Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={removeNetwork}
              className="rounded-sm bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Remove Network
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}