import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Package, Download, Plus, Search } from 'lucide-react';
import api from '@/lib/api';
import { toast } from 'sonner';

export default function ApplicationsPage() {
  const [apps, setApps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [installing, setInstalling] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [customAppDialog, setCustomAppDialog] = useState(false);
  const [customApp, setCustomApp] = useState({
    name: '',
    description: '',
    category: '',
    docker_image: '',
  });

  useEffect(() => {
    loadApps();
  }, []);

  const loadApps = async () => {
    try {
      const response = await api.get('/applications');
      setApps(response.data);
    } catch (error) {
      console.error('Error loading apps:', error);
      toast.error('Failed to load applications');
    } finally {
      setLoading(false);
    }
  };

  const seedApps = async () => {
    try {
      await api.post('/applications/seed');
      await loadApps();
      toast.success('App library initialized');
    } catch (error) {
      console.error('Error seeding apps:', error);
    }
  };

  const installApp = async (templateId) => {
    setInstalling(templateId);
    try {
      const response = await api.post(`/apps/install/${templateId}`);
      toast.success(response.data.message);
    } catch (error) {
      console.error('Error installing app:', error);
      toast.error(error.response?.data?.detail || 'Failed to install application');
    } finally {
      setInstalling(null);
    }
  };

  const addCustomApp = async () => {
    try {
      await api.post('/apps/templates', {
        ...customApp,
        official: false,
      });
      toast.success('Custom app added successfully');
      setCustomAppDialog(false);
      setCustomApp({ name: '', description: '', category: '', docker_image: '' });
      await loadApps();
    } catch (error) {
      console.error('Error adding custom app:', error);
      toast.error('Failed to add custom application');
    }
  };

  const filteredApps = apps.filter(
    (app) =>
      app.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      app.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const officialApps = filteredApps.filter((app) => app.official);
  const customApps = filteredApps.filter((app) => !app.official);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Package className="w-12 h-12 text-primary animate-pulse mx-auto mb-4" />
          <p className="text-muted-foreground">Loading applications...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="applications-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-heading font-bold tracking-tight">Applications</h1>
          <p className="text-muted-foreground mt-2">Install and manage server applications</p>
        </div>
        <Button
          onClick={() => setCustomAppDialog(true)}
          data-testid="add-custom-app-button"
          className="rounded-sm uppercase tracking-wide font-medium"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Custom App
        </Button>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input
          placeholder="Search applications..."
          data-testid="search-apps-input"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10 rounded-sm"
        />
      </div>

      {apps.length === 0 ? (
        <Card className="rounded-sm border-border">
          <CardContent className="py-12 text-center">
            <Package className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-heading font-bold mb-2">No Applications Available</h3>
            <p className="text-muted-foreground mb-4">Load the official app library to get started</p>
            <Button onClick={seedApps} data-testid="seed-apps-button" className="rounded-sm uppercase tracking-wide font-medium">
              Load Official Apps
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Tabs defaultValue="official" className="w-full">
          <TabsList className="rounded-sm">
            <TabsTrigger value="official" data-testid="official-apps-tab" className="rounded-sm">
              Official Apps ({officialApps.length})
            </TabsTrigger>
            <TabsTrigger value="custom" data-testid="custom-apps-tab" className="rounded-sm">
              Third-Party ({customApps.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="official" className="mt-6">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {officialApps.map((app) => (
                <Card key={app.id} className="rounded-sm border-border" data-testid={`app-card-${app.name.toLowerCase()}`}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="font-heading text-lg">{app.name}</CardTitle>
                        <CardDescription className="text-xs mt-1">{app.category}</CardDescription>
                      </div>
                      <Badge variant="secondary" className="rounded-sm text-xs font-mono">
                        OFFICIAL
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground mb-4">{app.description}</p>
                    {app.github_repo && (
                      <p className="text-xs font-mono text-muted-foreground mb-4 truncate">{app.github_repo}</p>
                    )}
                    <Button
                      onClick={() => installApp(app.id)}
                      disabled={installing === app.id}
                      data-testid={`install-${app.name.toLowerCase()}-button`}
                      className="w-full rounded-sm uppercase tracking-wide font-medium text-xs"
                    >
                      {installing === app.id ? (
                        'Installing...'
                      ) : (
                        <>
                          <Download className="w-4 h-4 mr-2" />
                          Install
                        </>
                      )}
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="custom" className="mt-6">
            {customApps.length === 0 ? (
              <Card className="rounded-sm border-border">
                <CardContent className="py-12 text-center">
                  <Package className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">No custom apps added yet</p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {customApps.map((app) => (
                  <Card key={app.id} className="rounded-sm border-border">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <CardTitle className="font-heading text-lg">{app.name}</CardTitle>
                          <CardDescription className="text-xs mt-1">{app.category}</CardDescription>
                        </div>
                        <Badge variant="outline" className="rounded-sm text-xs font-mono">
                          CUSTOM
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground mb-4">{app.description}</p>
                      <Button
                        onClick={() => installApp(app.id)}
                        disabled={installing === app.id}
                        className="w-full rounded-sm uppercase tracking-wide font-medium text-xs"
                      >
                        {installing === app.id ? (
                          'Installing...'
                        ) : (
                          <>
                            <Download className="w-4 h-4 mr-2" />
                            Install
                          </>
                        )}
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      )}

      <Dialog open={customAppDialog} onOpenChange={setCustomAppDialog}>
        <DialogContent className="sm:max-w-md rounded-sm" data-testid="custom-app-dialog">
          <DialogHeader>
            <DialogTitle className="font-heading">Add Custom Application</DialogTitle>
            <DialogDescription>Add a third-party application using a Docker image</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="app-name">Application Name</Label>
              <Input
                id="app-name"
                data-testid="custom-app-name-input"
                placeholder="My Custom App"
                value={customApp.name}
                onChange={(e) => setCustomApp({ ...customApp, name: e.target.value })}
                className="rounded-sm"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="app-description">Description</Label>
              <Textarea
                id="app-description"
                data-testid="custom-app-description-input"
                placeholder="Brief description of the application"
                value={customApp.description}
                onChange={(e) => setCustomApp({ ...customApp, description: e.target.value })}
                className="rounded-sm"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="app-category">Category</Label>
              <Input
                id="app-category"
                data-testid="custom-app-category-input"
                placeholder="Media, Download, etc."
                value={customApp.category}
                onChange={(e) => setCustomApp({ ...customApp, category: e.target.value })}
                className="rounded-sm"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="docker-image">Docker Image</Label>
              <Input
                id="docker-image"
                data-testid="custom-app-image-input"
                placeholder="username/image:tag"
                value={customApp.docker_image}
                onChange={(e) => setCustomApp({ ...customApp, docker_image: e.target.value })}
                className="rounded-sm font-mono text-sm"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              onClick={addCustomApp}
              data-testid="save-custom-app-button"
              disabled={!customApp.name || !customApp.docker_image}
              className="rounded-sm uppercase tracking-wide font-medium"
            >
              Add Application
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}