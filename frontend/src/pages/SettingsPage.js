import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { Globe, Shield, Settings as SettingsIcon, Save } from 'lucide-react';
import api from '@/lib/api';
import { toast } from 'sonner';

export default function SettingsPage() {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const response = await api.get('/settings');
      setSettings(response.data);
    } catch (error) {
      console.error('Error loading settings:', error);
      toast.error('Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    setSaving(true);
    try {
      await api.put('/settings', settings);
      toast.success('Settings saved successfully');
    } catch (error) {
      console.error('Error saving settings:', error);
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <SettingsIcon className="w-12 h-12 text-primary animate-pulse mx-auto mb-4" />
          <p className="text-muted-foreground">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl" data-testid="settings-page">
      <div>
        <h1 className="text-4xl font-heading font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground mt-2">Configure DDNS, SSL, and system settings</p>
      </div>

      <Card className="rounded-sm border-border">
        <CardHeader>
          <div className="flex items-center gap-3">
            <Globe className="w-5 h-5 text-primary" />
            <div>
              <CardTitle className="font-heading">DDNS Configuration</CardTitle>
              <CardDescription>Dynamic DNS settings for remote access</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="ddns-enabled">Enable DDNS</Label>
              <p className="text-sm text-muted-foreground">Automatically update DNS records</p>
            </div>
            <Switch
              id="ddns-enabled"
              data-testid="ddns-enabled-switch"
              checked={settings?.ddns_enabled || false}
              onCheckedChange={(checked) => setSettings({ ...settings, ddns_enabled: checked })}
            />
          </div>

          {settings?.ddns_enabled && (
            <>
              <Separator />
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="ddns-provider">Provider</Label>
                  <div className="flex items-center gap-2">
                    <Input
                      id="ddns-provider"
                      data-testid="ddns-provider-input"
                      value="No-IP"
                      disabled
                      className="rounded-sm"
                    />
                    <Badge variant="outline" className="rounded-sm text-xs font-mono">
                      DEFAULT
                    </Badge>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="ddns-hostname">Hostname</Label>
                  <Input
                    id="ddns-hostname"
                    data-testid="ddns-hostname-input"
                    placeholder="myserver.ddns.net"
                    value={settings?.ddns_hostname || ''}
                    onChange={(e) => setSettings({ ...settings, ddns_hostname: e.target.value })}
                    className="rounded-sm font-mono"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="ddns-username">Username</Label>
                  <Input
                    id="ddns-username"
                    data-testid="ddns-username-input"
                    placeholder="username"
                    value={settings?.ddns_username || ''}
                    onChange={(e) => setSettings({ ...settings, ddns_username: e.target.value })}
                    className="rounded-sm"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="ddns-password">Password</Label>
                  <Input
                    id="ddns-password"
                    data-testid="ddns-password-input"
                    type="password"
                    placeholder="••••••••"
                    value={settings?.ddns_password || ''}
                    onChange={(e) => setSettings({ ...settings, ddns_password: e.target.value })}
                    className="rounded-sm"
                  />
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <Card className="rounded-sm border-border">
        <CardHeader>
          <div className="flex items-center gap-3">
            <Shield className="w-5 h-5 text-primary" />
            <div>
              <CardTitle className="font-heading">SSL/TLS Configuration</CardTitle>
              <CardDescription>Let's Encrypt automatic SSL certificates</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="ssl-enabled">Enable SSL</Label>
              <p className="text-sm text-muted-foreground">Automatically obtain and renew certificates</p>
            </div>
            <Switch
              id="ssl-enabled"
              data-testid="ssl-enabled-switch"
              checked={settings?.ssl_enabled || false}
              onCheckedChange={(checked) => setSettings({ ...settings, ssl_enabled: checked })}
            />
          </div>

          {settings?.ssl_enabled && (
            <>
              <Separator />
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="ssl-email">Email Address</Label>
                  <Input
                    id="ssl-email"
                    data-testid="ssl-email-input"
                    type="email"
                    placeholder="admin@example.com"
                    value={settings?.ssl_email || ''}
                    onChange={(e) => setSettings({ ...settings, ssl_email: e.target.value })}
                    className="rounded-sm"
                  />
                  <p className="text-xs text-muted-foreground">Used for important certificate notifications</p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="ssl-domains">Domains (comma-separated)</Label>
                  <Input
                    id="ssl-domains"
                    data-testid="ssl-domains-input"
                    placeholder="example.com, www.example.com"
                    value={settings?.ssl_domains?.join(', ') || ''}
                    onChange={(e) =>
                      setSettings({
                        ...settings,
                        ssl_domains: e.target.value.split(',').map((d) => d.trim()),
                      })
                    }
                    className="rounded-sm font-mono"
                  />
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button
          onClick={saveSettings}
          data-testid="save-settings-button"
          disabled={saving}
          className="rounded-sm uppercase tracking-wide font-medium"
        >
          <Save className="w-4 h-4 mr-2" />
          {saving ? 'Saving...' : 'Save Settings'}
        </Button>
      </div>
    </div>
  );
}