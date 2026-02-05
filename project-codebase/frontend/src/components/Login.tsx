import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, Loader2, Sparkles, Shield, Zap } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useStore } from '@/store/useStore';
import { authApi } from '@/services/api';

export function Login() {
  const [email, setEmail] = useState('admin@tatvic.com');
  const [password, setPassword] = useState('admin');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const { setUser, setAuthenticated, setToken } = useStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const response = await authApi.login(email, password);
      
      if (response.success && response.data) {
        setUser(response.data.user);
        setToken(response.data.token);
        setAuthenticated(true);
      } else {
        setError(response.error || 'Login failed');
      }
    } catch (err) {
      setError('An error occurred during login');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#321a75]/5 via-white to-[#00c3c4]/5 p-4">
      <div className="w-full max-w-5xl grid lg:grid-cols-2 gap-8 items-center">
        {/* Left Side - Branding */}
        <div className="hidden lg:flex flex-col space-y-8">
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#321a75] to-[#4a2d99] flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <span className="text-2xl font-bold text-[#321a75]">Nexus</span>
            </div>
            <h1 className="text-4xl font-bold text-gray-900 leading-tight">
              Account Intelligence <span className="text-gradient">Layer</span>
            </h1>
            <p className="text-lg text-gray-600 leading-relaxed">
              Centralized, living system that aggregates client knowledge from scattered sources into a structured dashboard.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-4">
            <div className="flex items-start space-x-4 p-4 rounded-xl bg-white/80 backdrop-blur-sm border border-gray-100 shadow-sm">
              <div className="w-10 h-10 rounded-lg bg-[#00c3c4]/10 flex items-center justify-center flex-shrink-0">
                <Zap className="w-5 h-5 text-[#00c3c4]" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Real-time Insights</h3>
                <p className="text-sm text-gray-600">Live data aggregation from Google Workspace and Basecamp</p>
              </div>
            </div>
            <div className="flex items-start space-x-4 p-4 rounded-xl bg-white/80 backdrop-blur-sm border border-gray-100 shadow-sm">
              <div className="w-10 h-10 rounded-lg bg-[#faab00]/10 flex items-center justify-center flex-shrink-0">
                <Shield className="w-5 h-5 text-[#faab00]" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Role-based Security</h3>
                <p className="text-sm text-gray-600">Granular permissions for different team roles</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side - Login Form */}
        <Card className="w-full max-w-md mx-auto border-0 shadow-2xl bg-white/90 backdrop-blur-sm">
          <CardHeader className="space-y-1 pb-6">
            <div className="lg:hidden flex items-center space-x-2 mb-4">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#321a75] to-[#4a2d99] flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <span className="text-xl font-bold text-[#321a75]">Nexus</span>
            </div>
            <CardTitle className="text-2xl font-bold text-gray-900">Welcome back</CardTitle>
            <CardDescription className="text-gray-500">
              Sign in to access your account intelligence dashboard
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <Alert variant="destructive" className="bg-red-50 border-red-200">
                  <AlertCircle className="h-4 w-4 text-red-600" />
                  <AlertDescription className="text-red-700">{error}</AlertDescription>
                </Alert>
              )}
              
              <div className="space-y-2">
                <Label htmlFor="email" className="text-gray-700 font-medium">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="h-11 border-gray-200 focus:border-[#321a75] focus:ring-[#321a75]/20"
                  required
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="password" className="text-gray-700 font-medium">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="h-11 border-gray-200 focus:border-[#321a75] focus:ring-[#321a75]/20"
                  required
                />
              </div>

              <div className="flex items-center justify-between text-sm">
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input type="checkbox" className="rounded border-gray-300 text-[#321a75] focus:ring-[#321a75]" />
                  <span className="text-gray-600">Remember me</span>
                </label>
                <a href="#" className="text-[#321a75] hover:text-[#4a2d99] font-medium">
                  Forgot password?
                </a>
              </div>
              
              <Button
                type="submit"
                className="w-full h-11 bg-gradient-to-r from-[#321a75] to-[#4a2d99] hover:from-[#3d208a] hover:to-[#5537a8] text-white font-semibold rounded-lg transition-all duration-200"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Signing in...
                  </>
                ) : (
                  'Sign in'
                )}
              </Button>
            </form>

            <div className="mt-6 pt-6 border-t border-gray-100">
              <p className="text-xs text-center text-gray-500 mb-3">Demo Credentials</p>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => { setEmail('admin@tatvic.com'); setPassword('admin'); }}
                  className="flex-1 py-2 px-3 text-xs bg-gray-50 hover:bg-gray-100 rounded-lg text-gray-600 transition-colors"
                >
                  Admin
                </button>
                <button
                  type="button"
                  onClick={() => { setEmail('tech@tatvic.com'); setPassword('admin'); }}
                  className="flex-1 py-2 px-3 text-xs bg-gray-50 hover:bg-gray-100 rounded-lg text-gray-600 transition-colors"
                >
                  Tech
                </button>
                <button
                  type="button"
                  onClick={() => { setEmail('pm@tatvic.com'); setPassword('admin'); }}
                  className="flex-1 py-2 px-3 text-xs bg-gray-50 hover:bg-gray-100 rounded-lg text-gray-600 transition-colors"
                >
                  PM
                </button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
