import { useEffect } from 'react';
import { Login } from '@/components/Login';
import { Sidebar } from '@/components/Sidebar';
import { Dashboard } from '@/components/Dashboard';
import { useStore } from '@/store/useStore';
import { Toaster } from '@/components/ui/sonner';
import { toast } from 'sonner';

function App() {
  const { isAuthenticated, logout, setUser, setAuthenticated } = useStore();

  useEffect(() => {
    // Check for existing session
    const storedUser = localStorage.getItem('nexus-storage');
    if (storedUser) {
      try {
        const parsed = JSON.parse(storedUser);
        if (parsed.state?.user && parsed.state?.isAuthenticated) {
          setUser(parsed.state.user);
          setAuthenticated(true);
        }
      } catch (e) {
        console.error('Failed to parse stored user:', e);
      }
    }
  }, [setUser, setAuthenticated]);

  const handleLogout = () => {
    logout();
    toast.success('Logged out successfully');
  };

  if (!isAuthenticated) {
    return (
      <>
        <Login />
        <Toaster position="top-right" />
      </>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar onLogout={handleLogout} />
      <Dashboard />
      <Toaster position="top-right" />
    </div>
  );
}

export default App;
