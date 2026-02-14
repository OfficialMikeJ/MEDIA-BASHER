import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Server, LayoutDashboard, Package, Box, HardDrive, Settings, Menu, X, RefreshCw, Layers, Bell, Network, Activity, Archive } from 'lucide-react';
import { Button } from '@/components/ui/button';

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/applications', label: 'Applications', icon: Package },
  { path: '/containers', label: 'Containers', icon: Box },
  { path: '/compose', label: 'Compose', icon: Layers },
  { path: '/networks', label: 'Networks', icon: Network },
  { path: '/storage', label: 'Storage', icon: HardDrive },
  { path: '/monitoring', label: 'Monitoring', icon: Activity },
  { path: '/updates', label: 'Updates', icon: RefreshCw },
  { path: '/backup', label: 'Backup', icon: Archive },
  { path: '/notifications', label: 'Notifications', icon: Bell },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <>
      <aside
        className={`${
          collapsed ? 'w-16' : 'w-64'
        } border-r border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 transition-all duration-200 flex flex-col`}
        data-testid="dashboard-sidebar"
      >
        <div className="p-4 border-b border-border flex items-center justify-between">
          {!collapsed && (
            <div className="flex items-center gap-2">
              <Server className="w-6 h-6 text-primary" />
              <span className="font-heading text-lg font-bold tracking-tight">MEDIA BASHER</span>
            </div>
          )}
          <Button
            variant="ghost"
            size="icon"
            data-testid="sidebar-toggle"
            onClick={() => setCollapsed(!collapsed)}
            className="rounded-sm"
          >
            {collapsed ? <Menu className="w-4 h-4" /> : <X className="w-4 h-4" />}
          </Button>
        </div>

        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                data-testid={`nav-${item.label.toLowerCase()}`}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-sm transition-colors ${
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                  }`
                }
              >
                <Icon className="w-5 h-5" strokeWidth={1.5} />
                {!collapsed && <span className="font-medium text-sm">{item.label}</span>}
              </NavLink>
            );
          })}
        </nav>

        {!collapsed && (
          <div className="p-4 border-t border-border">
            <div className="text-xs text-muted-foreground font-mono">
              <div>Version 1.0.0</div>
              <div className="text-primary mt-1">SYSTEM ONLINE</div>
            </div>
          </div>
        )}
      </aside>
    </>
  );
}