import React, { JSX } from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate
} from 'react-router-dom';
import { message } from 'antd';
import AdminLayout from './components/layout/AdminLayout';
import UserLayout from './components/layout/UserLayout';
import './App.css';

// Configure message globally
message.config({
  top: 100,
  duration: 4,
  maxCount: 3,
});

// Import Page Components
import AdminDashboard from './components/pages/admin/Dashboard';
import SyllabusEditPage from './components/pages/admin/SyllabusEditPage';
import ConversationLogs from './components/pages/admin/ConversationLogs';
import AdminSettings from './components/pages/admin/Settings';
import UserChat from './components/pages/user/Chat';
import LoginPage from './components/pages/auth/LoginPage';
import SyllabusManagement from './components/pages/admin/SyllabusManagement';
import SyllabusViewPage from './components/pages/admin/SyllabusViewPage';
import LLMTestPage from './components/pages/admin/LLMTestPage';

// Placeholder Page Components (will be created next)
// const AdminDashboard = () => <div>Admin Dashboard</div>;
// const SyllabusManagement = () => <div>Syllabus Management</div>;
// const ConversationLogs = () => <div>Conversation Logs</div>;
// const AdminSettings = () => <div>Admin Settings</div>;
// const UserChat = () => <div>User Chat Interface</div>;

// Mock auth hook (replace with your actual auth logic)
const useAuth = () => {
  // In a real app, this would check for a token, user context, etc.
  const isAuthenticated = true; // Or localStorage.getItem('token') etc.
  return { isAuthenticated };
};

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

function App() {
  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<LoginPage />} />

        {/* Admin Routes (Protected) */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              <AdminLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<AdminDashboard />} />
          <Route path="syllabus" element={<SyllabusManagement />} />
          <Route path="syllabus/view/:courseId" element={<SyllabusViewPage />} />
          <Route path="syllabus/edit/:courseId" element={<SyllabusEditPage />} />
          <Route path="llm-test" element={<LLMTestPage />} />
          <Route path="logs" element={<ConversationLogs />} />
          <Route path="settings" element={<AdminSettings />} />
          {/* Add other admin routes here */}
        </Route>

        {/* User Chat Route */}
        <Route path="/chat" element={<UserLayout />}>
          <Route index element={<UserChat />} />
          {/* Add other user routes if needed */}
        </Route>

        {/* Redirect base path (e.g., to user chat or a landing page) */}
        <Route path="/" element={<Navigate to="/chat" replace />} />

        {/* Optional: 404 Not Found Route */}
        <Route path="*" element={<Navigate to="/admin" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
