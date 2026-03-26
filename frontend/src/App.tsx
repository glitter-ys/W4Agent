import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AppLayout from './components/Layout/AppLayout';
import Dashboard from './pages/Dashboard';
import ProjectList from './pages/ProjectList';
import TaskCreate from './pages/TaskCreate';
import TaskDetail from './pages/TaskDetail';
import ReportView from './pages/ReportView';
import Settings from './pages/Settings';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/projects" element={<ProjectList />} />
          <Route path="/tasks/create" element={<TaskCreate />} />
          <Route path="/tasks/:taskId" element={<TaskDetail />} />
          <Route path="/reports/:taskId" element={<ReportView />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </AppLayout>
    </BrowserRouter>
  );
};

export default App;
