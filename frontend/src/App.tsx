import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, App as AntdApp } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import WorkflowListPage from './pages/WorkflowListPage';
import WorkflowDesignerPage from './pages/WorkflowDesignerPage';
import ExecutionLogsPage from './pages/ExecutionLogsPage';
import ExecutionDetailPage from './pages/ExecutionDetailPage';
import SettingsPage from './pages/SettingsPage';
import { useAuthStore } from './stores/authStore';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

const App: React.FC = () => {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#6366f1',
          borderRadius: 6,
        },
      }}
    >
      <AntdApp>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route
              path="/workflows"
              element={
                <ProtectedRoute>
                  <WorkflowListPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/workflows/:id/edit"
              element={
                <ProtectedRoute>
                  <WorkflowDesignerPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/workflows/:id/logs"
              element={
                <ProtectedRoute>
                  <ExecutionLogsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/workflows/:id/logs/:execId"
              element={
                <ProtectedRoute>
                  <ExecutionDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <SettingsPage />
                </ProtectedRoute>
              }
            />
            <Route path="/" element={<Navigate to="/workflows" replace />} />
            <Route path="*" element={<Navigate to="/workflows" replace />} />
          </Routes>
        </BrowserRouter>
      </AntdApp>
    </ConfigProvider>
  );
};

export default App;
