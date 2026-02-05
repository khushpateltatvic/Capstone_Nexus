import { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useStore } from '@/store/useStore';
import { clientsApi, projectsApi } from '@/services/api';
import type { Client, Project } from '@/types';
import {
  ChevronLeft,
  ChevronRight,
  LayoutDashboard,
  Building2,
  FolderKanban,
  LogOut,
  ChevronDown,
  Sparkles,
  Bot,
} from 'lucide-react';

interface SidebarProps {
  onLogout: () => void;
}

export function Sidebar({ onLogout }: SidebarProps) {
  const {
    sidebarCollapsed,
    setSidebarCollapsed,
    selectedClient,
    selectedProject,
    setSelectedClient,
    setSelectedProject,
    setClients,
    setProjects,
    clients,
    projects,
    user,
    currentView,
    setCurrentView,
  } = useStore();

  const [expandedClient, setExpandedClient] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [clientsRes, projectsRes] = await Promise.all([
        clientsApi.getAll(),
        projectsApi.getAll(),
      ]);

      if (clientsRes.success && clientsRes.data) {
        setClients(clientsRes.data);
        if (clientsRes.data.length > 0 && !selectedClient) {
          setSelectedClient(clientsRes.data[0]);
          setExpandedClient(clientsRes.data[0].id);
        }
      }

      if (projectsRes.success && projectsRes.data) {
        setProjects(projectsRes.data);
        if (projectsRes.data.length > 0 && !selectedProject) {
          const firstProject = projectsRes.data[0];
          setSelectedProject(firstProject);
          setSelectedClient(clients.find(c => c.id === firstProject.client_id) || clients[0]);
        }
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClientClick = (client: Client) => {
    if (expandedClient === client.id) {
      setExpandedClient(null);
    } else {
      setExpandedClient(client.id);
      setSelectedClient(client);
      setCurrentView('dashboard'); // Switch to dashboard when selecting client
      if (client.projects.length > 0 && !selectedProject) {
        const project = projects.find(p => p.id === client.projects[0].id);
        if (project) setSelectedProject(project);
      }
    }
  };

  const handleProjectClick = (project: Project) => {
    setSelectedProject(project);
    const client = clients.find(c => c.id === project.client_id);
    if (client) setSelectedClient(client);
    setCurrentView('dashboard'); // Switch to dashboard when selecting project
  };

  const getClientProjects = (clientId: string) => {
    return projects.filter(p => p.client_id === clientId);
  };

  return (
    <div
      className={cn(
        'flex flex-col h-screen bg-[#321a75] text-white transition-all duration-300 ease-in-out',
        sidebarCollapsed ? 'w-16' : 'w-72'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-white/10">
        {!sidebarCollapsed && (
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#00c3c4] to-[#00e5e6] flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="text-lg font-bold">Nexus</span>
          </div>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="text-white/70 hover:text-white hover:bg-white/10"
        >
          {sidebarCollapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
        </Button>
      </div>

      {/* Navigation */}
      <ScrollArea className="flex-1 py-4">
        {!sidebarCollapsed && (
          <div className="px-4 mb-4">
            <p className="text-xs font-medium text-white/50 uppercase tracking-wider mb-3">Workspace</p>
          </div>
        )}

        {/* Dashboard Link */}
        <Button
          variant="ghost"
          onClick={() => setCurrentView('dashboard')}
          className={cn(
            'w-full justify-start text-white/80 hover:text-white hover:bg-white/10',
            sidebarCollapsed ? 'px-4' : 'px-4 mx-2 w-[calc(100%-16px)]',
            currentView === 'dashboard' && 'bg-white/10 text-white'
          )}
        >
          <LayoutDashboard className="w-5 h-5 flex-shrink-0" />
          {!sidebarCollapsed && <span className="ml-3">Dashboard</span>}
        </Button>

        {/* Intelligence Link */}
        <Button
          variant="ghost"
          onClick={() => setCurrentView('intelligence')}
          className={cn(
            'w-full justify-start text-white/80 hover:text-white hover:bg-white/10 mt-1',
            sidebarCollapsed ? 'px-4' : 'px-4 mx-2 w-[calc(100%-16px)]',
            currentView === 'intelligence' && 'bg-white/10 text-white'
          )}
        >
          <Sparkles className="w-5 h-5 flex-shrink-0" />
          {!sidebarCollapsed && <span className="ml-3">Intelligence</span>}
        </Button>

        {/* Chatbot Link */}
        <Button
          variant="ghost"
          onClick={() => setCurrentView('chatbot')}
          className={cn(
            'w-full justify-start text-white/80 hover:text-white hover:bg-white/10 mt-1',
            sidebarCollapsed ? 'px-4' : 'px-4 mx-2 w-[calc(100%-16px)]',
            currentView === 'chatbot' && 'bg-white/10 text-white'
          )}
        >
          <Bot className="w-5 h-5 flex-shrink-0" />
          {!sidebarCollapsed && <span className="ml-3">Chatbot</span>}
        </Button>

        {!sidebarCollapsed && (
          <div className="px-4 mt-6 mb-3">
            <p className="text-xs font-medium text-white/50 uppercase tracking-wider">Clients & Projects</p>
          </div>
        )}

        {sidebarCollapsed && (
          <div className="px-4 py-2">
            <Building2 className="w-5 h-5 text-white/50 mx-auto" />
          </div>
        )}

        {/* Client List */}
        {/* Client List */}
        {!isLoading && !sidebarCollapsed && clients.length > 0 && (
          <div className="space-y-1 px-2">
            {clients.map((client) => (
              <div key={`client-full-${client.id}`}>
                <Button
                  variant="ghost"
                  onClick={() => handleClientClick(client)}
                  className={cn(
                    'w-full justify-between text-white/80 hover:text-white hover:bg-white/10 h-auto py-2',
                    selectedClient?.id === client.id && 'bg-white/10 text-white'
                  )}
                >
                  <div className="flex items-center overflow-hidden">
                    <div className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0 text-xs font-medium">
                      {client.name.charAt(0)}
                    </div>
                    <span className="ml-2 truncate text-sm">{client.name}</span>
                  </div>
                  <ChevronDown
                    className={cn(
                      'w-4 h-4 flex-shrink-0 transition-transform',
                      expandedClient === client.id && 'rotate-180'
                    )}
                  />
                </Button>

                {/* Projects under client */}
                {expandedClient === client.id && (
                  <div className="ml-4 mt-1 space-y-1 border-l border-white/10 pl-3">
                    {getClientProjects(client.id).map((project) => (
                      <Button
                        key={`project-${client.id}-${project.id}`}
                        variant="ghost"
                        onClick={() => handleProjectClick(project)}
                        className={cn(
                          'w-full justify-start text-white/60 hover:text-white hover:bg-white/10 h-auto py-1.5 text-xs',
                          selectedProject?.id === project.id && 'bg-white/10 text-white'
                        )}
                      >
                        <FolderKanban className="w-3.5 h-3.5 mr-2 flex-shrink-0" />
                        <span className="truncate">{project.name}</span>
                      </Button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Error/Empty State */}
        {!isLoading && !sidebarCollapsed && clients.length === 0 && (
          <div className="px-4 py-8 text-center">
            <p className="text-white/40 text-sm mb-2">Unavailable</p>
            <Button
              variant="secondary"
              size="sm"
              className="h-7 text-xs bg-white/10 hover:bg-white/20 text-white border-0"
              onClick={() => loadData()}
            >
              Retry Connection
            </Button>
          </div>
        )}

        {sidebarCollapsed && (
          <div className="px-4 py-2 space-y-2">
            {clients.slice(0, 3).map((client) => (
              <button
                key={`client-collapsed-${client.id}`}
                onClick={() => handleClientClick(client)}
                className={cn(
                  'w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium transition-colors',
                  selectedClient?.id === client.id
                    ? 'bg-[#00c3c4] text-white'
                    : 'bg-white/20 text-white/80 hover:bg-white/30'
                )}
              >
                {client.name.charAt(0)}
              </button>
            ))}
          </div>
        )}
      </ScrollArea>

      {/* Footer */}
      <div className="border-t border-white/10 p-4">
        {!sidebarCollapsed ? (
          <div className="space-y-2">
            {/* Removed unused Team and Settings buttons */}
            <div className="flex items-center justify-between pt-3 border-t border-white/10">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#00c3c4] to-[#faab00] flex items-center justify-center text-white text-sm font-medium">
                  {user?.name.charAt(0)}
                </div>
                <div className="text-sm">
                  <p className="font-medium text-white">{user?.name}</p>
                  <p className="text-xs text-white/60">{user?.job_title}</p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={onLogout}
                className="text-white/60 hover:text-white hover:bg-white/10"
              >
                <LogOut className="w-4 h-4" />
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center space-y-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#00c3c4] to-[#faab00] flex items-center justify-center text-white text-sm font-medium">
              {user?.name.charAt(0)}
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={onLogout}
              className="text-white/60 hover:text-white hover:bg-white/10"
            >
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
