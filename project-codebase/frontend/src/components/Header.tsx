import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useStore } from '@/store/useStore';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  FileText,
  Loader2,
} from 'lucide-react';
import { cn } from '@/lib/utils';

import { reportsApi } from '@/services/api';

interface HeaderProps {
  onExpandAll: () => void;
  onCollapseAll: () => void;
}

export function Header({ onExpandAll, onCollapseAll }: HeaderProps) {
  const { selectedClient, selectedProject, user } = useStore();
  const [isExporting, setIsExporting] = useState(false);

  const getHealthColor = (score: number) => {
    if (score >= 80) return 'text-emerald-600 bg-emerald-50';
    if (score >= 60) return 'text-amber-600 bg-amber-50';
    return 'text-red-600 bg-red-50';
  };

  const getHealthIcon = (score: number) => {
    if (score >= 80) return <TrendingUp className="w-3 h-3" />;
    if (score >= 60) return <Minus className="w-3 h-3" />;
    return <TrendingDown className="w-3 h-3" />;
  };

  const handleGenerateReport = async () => {
    if (!selectedProject) return;

    const projectId = selectedProject.project_id || selectedProject.id;
    setIsExporting(true);

    try {
      const response = await reportsApi.generate(projectId);
      if (response.success && response.data) {
        // Create a blob and open in new tab
        const blob = new Blob([response.data], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        window.open(url, '_blank');
      } else {
        alert('Failed to generate report: ' + (response.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Report error:', error);
      alert('An error occurred while generating the report.');
    } finally {
      setIsExporting(true); // Small delay before resetting
      setTimeout(() => setIsExporting(false), 1000);
    }
  };

  return (
    <header className="h-16 bg-white border-b border-gray-100 flex items-center justify-between px-6 sticky top-0 z-30">
      {/* Left Section - Breadcrumb & Project Info */}
      <div className="flex items-center space-x-4">
        <div>
          {selectedClient && selectedProject ? (
            <div className="flex items-center space-x-3">
              <div>
                <div className="flex items-center space-x-2">
                  <h1 className="text-lg font-semibold text-gray-900">{selectedProject.name}</h1>
                  <Badge
                    variant="secondary"
                    className={cn(
                      'text-xs font-medium',
                      getHealthColor(selectedProject.health_score)
                    )}
                  >
                    {getHealthIcon(selectedProject.health_score)}
                    <span className="ml-1">{selectedProject.health_score}% Health</span>
                  </Badge>
                </div>
                <p className="text-sm text-gray-500">
                  {selectedClient.name} · {selectedProject.department}
                </p>
              </div>
            </div>
          ) : (
            <div>
              <h1 className="text-lg font-semibold text-gray-900">Dashboard</h1>
              <p className="text-sm text-gray-500">Select a project to view details</p>
            </div>
          )}
        </div>
      </div>

      {/* Center Section - Module Controls */}
      <div className="flex items-center space-x-2">
        <Button
          variant="outline"
          size="sm"
          onClick={onExpandAll}
          className="text-xs border-gray-200 hover:bg-gray-50"
        >
          Expand All
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onCollapseAll}
          className="text-xs border-gray-200 hover:bg-gray-50"
        >
          Collapse All
        </Button>
      </div>

      {/* Right Section - Actions & User */}
      <div className="flex items-center space-x-3">
        {selectedProject && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleGenerateReport}
            disabled={isExporting}
            className="text-xs text-[#321a75] hover:bg-[#321a75]/5 gap-2 mr-2"
          >
            {isExporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
            {isExporting ? 'Generating...' : 'Export Report'}
          </Button>
        )}

        {/* Notifications
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="relative">
              <Bell className="w-5 h-5 text-gray-600" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                  {unreadCount}
                </span>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80">
            <div className="px-3 py-2 border-b border-gray-100">
              <p className="font-semibold text-gray-900">Notifications</p>
            </div>
            {notifications.map((notification) => (
              <DropdownMenuItem key={notification.id} className="px-3 py-3 cursor-pointer">
                <div className="flex items-start space-x-3">
                  <div className={cn(
                    'w-2 h-2 rounded-full mt-1.5 flex-shrink-0',
                    notification.read ? 'bg-gray-300' : 'bg-[#00c3c4]'
                  )} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900">{notification.title}</p>
                    <p className="text-xs text-gray-500 truncate">{notification.message}</p>
                    <p className="text-xs text-gray-400 mt-1">{notification.time}</p>
                  </div>
                </div>
              </DropdownMenuItem>
            ))}
            <DropdownMenuSeparator />
            <DropdownMenuItem className="justify-center text-[#321a75] font-medium">
              View all notifications
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>*/}

        {/* User Info with Logout */}
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#321a75] to-[#00c3c4] flex items-center justify-center text-white text-sm font-medium">
            {user?.name.charAt(0)}
          </div>
          <div className="hidden sm:block text-left">
            <p className="text-sm font-medium text-gray-900">{user?.name}</p>
            <button
              onClick={() => {
                useStore.getState().logout();
                window.location.reload();
              }}
              className="text-xs text-red-500 hover:text-red-700 font-medium block"
            >
              Sign out
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
