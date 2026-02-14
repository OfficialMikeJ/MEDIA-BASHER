import { useEffect, useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Cpu, HardDrive, MemoryStick, CheckCircle2, AlertTriangle } from 'lucide-react';
import api from '@/lib/api';

export default function FirstTimeModal() {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const checkFirstLogin = async () => {
      try {
        const response = await api.get('/auth/me');
        if (response.data.first_login) {
          setOpen(true);
        }
      } catch (error) {
        console.error('Error checking first login:', error);
      }
    };

    checkFirstLogin();
  }, []);

  const handleContinue = async () => {
    setLoading(true);
    try {
      await api.post('/auth/mark-onboarded');
      setOpen(false);
    } catch (error) {
      console.error('Error marking onboarded:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="sm:max-w-2xl rounded-sm" data-testid="first-time-modal">
        <DialogHeader>
          <DialogTitle className="text-2xl font-heading">Welcome to Media Basher</DialogTitle>
          <DialogDescription>System Requirements for Optimal Performance</DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          <Alert className="rounded-sm border-primary/50 bg-primary/5">
            <AlertTriangle className="h-5 w-5 text-primary" />
            <AlertDescription className="ml-2">
              <span className="font-semibold text-foreground">Minimum Requirements</span>
            </AlertDescription>
          </Alert>

          <div className="grid gap-3 pl-4">
            <div className="flex items-center gap-3 text-sm">
              <Cpu className="w-4 h-4 text-primary" />
              <span className="font-mono">2 vCPU</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <MemoryStick className="w-4 h-4 text-primary" />
              <span className="font-mono">4GB RAM</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <HardDrive className="w-4 h-4 text-primary" />
              <span className="font-mono">120GB Storage</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <CheckCircle2 className="w-4 h-4 text-primary" />
              <span className="font-mono">Ubuntu Server LTS 24.04 64-bit</span>
            </div>
          </div>

          <Alert className="rounded-sm border-primary bg-primary/10">
            <CheckCircle2 className="h-5 w-5 text-primary" />
            <AlertDescription className="ml-2">
              <span className="font-semibold text-foreground">Recommended Requirements</span>
            </AlertDescription>
          </Alert>

          <div className="grid gap-3 pl-4">
            <div className="flex items-center gap-3 text-sm">
              <Cpu className="w-4 h-4 text-primary" />
              <span className="font-mono">6 vCPU</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <MemoryStick className="w-4 h-4 text-primary" />
              <span className="font-mono">32GB RAM</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <HardDrive className="w-4 h-4 text-primary" />
              <span className="font-mono">1TB Storage</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <CheckCircle2 className="w-4 h-4 text-primary" />
              <span className="font-mono">Ubuntu Server LTS 24.04 64-bit</span>
            </div>
          </div>

          <div className="pt-4 border-t border-border">
            <p className="text-sm text-muted-foreground">
              These requirements ensure smooth operation of media servers, download clients, and management tools.
              Running below minimum specs may result in degraded performance.
            </p>
          </div>
        </div>

        <div className="flex justify-end">
          <Button
            onClick={handleContinue}
            data-testid="first-time-continue-button"
            disabled={loading}
            className="rounded-sm uppercase tracking-wide font-medium"
          >
            {loading ? 'Processing...' : 'Continue to Dashboard'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}