import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import { AnimatePresence } from 'framer-motion';
import 'react-toastify/dist/ReactToastify.css';

import { AuthProvider, useAuth } from './contexts/AuthContext.tsx';
import Home from './pages/Home.tsx';
import Auth from './pages/Auth.tsx';
import Dashboard from './pages/Dashboard.tsx';
import LostItemForm from './pages/LostItemForm.tsx';
import FoundItemForm from './pages/FoundItemForm.tsx';
import Matches from './pages/Matches.tsx';
import Notifications from './pages/Notifications.tsx';
import Search from './pages/Search.tsx';
import Upload from './pages/Upload.tsx';
import Admin from './pages/Admin.tsx';
import Layout from './components/Layout.tsx';
import Footer from './components/Footer.tsx';

const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <>{children}</> : <Navigate to="/auth" />;
};

const AdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, user } = useAuth();
  if (!isAuthenticated) {
    return <Navigate to="/auth" />;
  }
  if (!user?.is_admin) {
    return <Navigate to="/dashboard" />;
  }
  return <>{children}</>;
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
          <AnimatePresence mode="wait">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/auth" element={<Auth />} />
              <Route
                path="/dashboard"
                element={
                  <PrivateRoute>
                    <Layout>
                      <Dashboard />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/lost-item"
                element={
                  <PrivateRoute>
                    <Layout>
                      <LostItemForm />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/found-item"
                element={
                  <PrivateRoute>
                    <Layout>
                      <FoundItemForm />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/matches"
                element={
                  <PrivateRoute>
                    <Layout>
                      <Matches />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/notifications"
                element={
                  <PrivateRoute>
                    <Layout>
                      <Notifications />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/search"
                element={
                  <PrivateRoute>
                    <Layout>
                      <Search />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/upload"
                element={
                  <PrivateRoute>
                    <Layout>
                      <Upload />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/admin"
                element={
                  <AdminRoute>
                    <Layout>
                      <Admin />
                    </Layout>
                  </AdminRoute>
                }
              />
            </Routes>
          </AnimatePresence>
          <Footer />
          <ToastContainer
            position="top-right"
            autoClose={5000}
            hideProgressBar={false}
            newestOnTop={false}
            closeOnClick
            rtl={false}
            pauseOnFocusLoss
            draggable
            pauseOnHover
            theme="colored"
          />
        </div>
      </Router>
    </AuthProvider>
  );
};

export default App;
