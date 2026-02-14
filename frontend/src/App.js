import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';
import LoginPage from '@/pages/LoginPage';
import DashboardPage from '@/pages/DashboardPage';
import ApplicationsPage from '@/pages/ApplicationsPage';
import ContainersPage from '@/pages/ContainersPage';
import StoragePage from '@/pages/StoragePage';
import SettingsPage from '@/pages/SettingsPage';
import ContainerLogsPage from '@/pages/ContainerLogsPage';
import UpdatesPage from '@/pages/UpdatesPage';
import DockerComposePage from '@/pages/DockerComposePage';
import NotificationsPage from '@/pages/NotificationsPage';
import NetworksPage from '@/pages/NetworksPage';
import MonitoringPage from '@/pages/MonitoringPage';
import BackupPage from '@/pages/BackupPage';
import DashboardLayout from '@/components/layout/DashboardLayout';
import '@/App.css';

const PrivateRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/login" replace />;
};

function App() {
  return (
    <>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <PrivateRoute>
                <DashboardLayout />
              </PrivateRoute>
            }
          >
            <Route index element={<DashboardPage />} />
            <Route path="applications" element={<ApplicationsPage />} />
            <Route path="containers" element={<ContainersPage />} />
            <Route path="containers/:containerId/logs" element={<ContainerLogsPage />} />
            <Route path="storage" element={<StoragePage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="updates" element={<UpdatesPage />} />
            <Route path="compose" element={<DockerComposePage />} />
            <Route path="notifications" element={<NotificationsPage />} />
            <Route path="networks" element={<NetworksPage />} />
            <Route path="monitoring" element={<MonitoringPage />} />
            <Route path="backup" element={<BackupPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
      <Toaster />
    </>
  );
}

export default App;