import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Layers, Plus, Trash2, Upload } from 'lucide-react';
import api from '@/lib/api';
import { toast } from 'sonner';

export default function DockerComposePage() {
  const [stacks, setStacks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deployDialog, setDeployDialog] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState({ open: false, stack: null });
  const [newStack, setNewStack] = useState({
    name: '',
    description: '',
    compose_content: ''
  });

  useEffect(() => {
    loadStacks();
  }, []);

  const loadStacks = async () => {
    try {
      const response = await api.get('/advanced/compose/stacks');
      setStacks(response.data.stacks || []);
    } catch (error) {
      console.error('Error loading stacks:', error);
      toast.error('Failed to load Docker Compose stacks');
    } finally {
      setLoading(false);
    }
  };

  const deployStack = async () => {
    try {
      await api.post('/advanced/compose/deploy', newStack);
      toast.success('Stack deployed successfully');
      setDeployDialog(false);
      setNewStack({ name: '', description: '', compose_content: '' });
      await loadStacks();
    } catch (error) {
      console.error('Error deploying stack:', error);
      toast.error(error.response?.data?.detail || 'Failed to deploy stack');
    }
  };

  const removeStack = async () => {
    const stackName = deleteDialog.stack;
    try {
      await api.delete(`/advanced/compose/${stackName}`);
      toast.success('Stack removed');
      setDeleteDialog({ open: false, stack: null });
      await loadStacks();
    } catch (error) {
      console.error('Error removing stack:', error);
      toast.error('Failed to remove stack');
    }
  };

  const sampleCompose = `version: '3.8'
services:
  web:
    image: nginx:latest
    ports:
      - "8080:80"
    volumes:
      - ./html:/usr/share/nginx/html
  
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"`;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Layers className="w-12 h-12 text-primary animate-pulse mx-auto mb-4" />
          <p className="text-muted-foreground">Loading stacks...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="compose-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-heading font-bold tracking-tight">Docker Compose</h1>
          <p className="text-muted-foreground mt-2">Deploy and manage multi-container applications</p>
        </div>
        <Button
          onClick={() => setDeployDialog(true)}
          className="rounded-sm uppercase tracking-wide font-medium"
        >
          <Plus className="w-4 h-4 mr-2" />
          Deploy Stack
        </Button>
      </div>

      {stacks.length === 0 ? (
        <Card className="rounded-sm border-border">
          <CardContent className="py-12 text-center">
            <Layers className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-heading font-bold mb-2">No Stacks Deployed</h3>
            <p className="text-muted-foreground mb-4">Deploy your first Docker Compose stack</p>
            <Button onClick={() => setDeployDialog(true)} className="rounded-sm uppercase tracking-wide font-medium">
              <Upload className="w-4 h-4 mr-2" />
              Deploy Stack
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {stacks.map((stack) => (
            <Card key={stack.name} className="rounded-sm border-border">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="font-heading text-lg flex items-center gap-3">
                      <Layers className="w-5 h-5 text-primary" />
                      {stack.name}
                    </CardTitle>
                    <CardDescription className="mt-2">
                      {stack.services} service{stack.services > 1 ? 's' : ''}
                    </CardDescription>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setDeleteDialog({ open: true, stack: stack.name })}
                    className="rounded-sm text-destructive hover:text-destructive hover:bg-destructive/10"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Location</span>
                    <span className="font-mono text-xs">{stack.path}</span>
                  </div>
                  <Badge variant="outline" className="rounded-sm text-xs font-mono">
                    ACTIVE
                  </Badge>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={deployDialog} onOpenChange={setDeployDialog}>
        <DialogContent className="sm:max-w-2xl rounded-sm max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-heading">Deploy Docker Compose Stack</DialogTitle>
            <DialogDescription>Upload or paste your docker-compose.yml configuration</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="stack-name">Stack Name</Label>
              <Input
                id="stack-name"
                placeholder="my-app-stack"
                value={newStack.name}
                onChange={(e) => setNewStack({ ...newStack, name: e.target.value })}
                className="rounded-sm"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="stack-description">Description (Optional)</Label>
              <Input
                id="stack-description"
                placeholder="Brief description"
                value={newStack.description}
                onChange={(e) => setNewStack({ ...newStack, description: e.target.value })}
                className="rounded-sm"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="compose-content">Docker Compose YAML</Label>
              <Textarea
                id="compose-content"
                placeholder={sampleCompose}
                value={newStack.compose_content}
                onChange={(e) => setNewStack({ ...newStack, compose_content: e.target.value })}
                className="rounded-sm font-mono text-xs h-80"
              />
              <p className="text-xs text-muted-foreground">
                Paste your docker-compose.yml content above
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button
              onClick={deployStack}
              disabled={!newStack.name || !newStack.compose_content}
              className="rounded-sm uppercase tracking-wide font-medium"
            >
              <Upload className="w-4 h-4 mr-2" />
              Deploy Stack
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={deleteDialog.open} onOpenChange={(open) => setDeleteDialog({ open, stack: null })}>
        <AlertDialogContent className="rounded-sm">
          <AlertDialogHeader>
            <AlertDialogTitle className="font-heading">Remove Stack</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to remove stack <span className="font-mono font-bold">{deleteDialog.stack}</span>?
              This will stop and remove all containers, networks, and volumes defined in the stack.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="rounded-sm">Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={removeStack}
              className="rounded-sm bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Remove Stack
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}