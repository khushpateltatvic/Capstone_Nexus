import { useEffect, useState } from 'react';
import { Header } from './Header';
import { UniversalContextModule } from './modules/UniversalContextModule';
import { OperationsModule } from './modules/OperationsModule';
import { TechnicalModule } from './modules/TechnicalModule';
import { CommercialModule } from './modules/CommercialModule';
import { StrategyModule } from './modules/StrategyModule';
import { MarketingModule } from './modules/MarketingModule';
import { IntelligenceModule } from './modules/IntelligenceModule';
import { ChatbotModule } from './modules/ChatbotModule';
import { useStore } from '@/store/useStore';
import { permissionsApi } from '@/services/api';
import { AlertCircle, RefreshCw } from 'lucide-react';

export function Dashboard() {
  const {
    selectedProject,
    selectedClient,
    expandedModules,
    toggleModule,
    expandAllModules,
    collapseAllModules,
    setPermissions,
    permissions,
    currentView,
  } = useStore();

  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadPermissions();
  }, [selectedProject, selectedClient]);

  const loadPermissions = async () => {
    if (!selectedProject) return;

    setIsLoading(true);
    try {
      // Pass project context if available for more accurate permissions
      const clientId = selectedClient?.id;
      const projectId = selectedProject?.project_id || selectedProject?.id;

      const response = await permissionsApi.getMyPermissions(clientId, projectId);
      if (response.success && response.data) {
        setPermissions(response.data);
      }
    } catch (error) {
      console.error('Failed to load permissions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const isModuleExpanded = (moduleId: string) => expandedModules.includes(moduleId);

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50">
        <div className="flex flex-col items-center">
          <RefreshCw className="w-8 h-8 animate-spin text-[#321a75] mb-3" />
          <p className="text-gray-500">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (!selectedProject) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50">
        <div className="text-center max-w-md mx-auto p-8">
          <div className="w-16 h-16 rounded-2xl bg-[#321a75]/10 flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-[#321a75]" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">No Project Selected</h2>
          <p className="text-gray-500 mb-6">
            Please select a client and project from the sidebar to view the dashboard.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-gray-50 min-h-screen">
      <Header onExpandAll={expandAllModules} onCollapseAll={collapseAllModules} />

      <main className="flex-1 p-6 overflow-auto">
        {currentView === 'intelligence' ? (
          <IntelligenceModule />
        ) : currentView === 'chatbot' ? (
          <ChatbotModule />
        ) : (
          <div className="max-w-7xl mx-auto space-y-6">
            {/* Module 1: Universal Context - Visible to All */}
            <UniversalContextModule
              isExpanded={isModuleExpanded('universal')}
              onToggle={() => toggleModule('universal')}
            />

            {/* Module 2: Operations & Status - Tech/PM Focus */}
            {(permissions?.operations !== 'NONE') && (
              <OperationsModule
                isExpanded={isModuleExpanded('operations')}
                onToggle={() => toggleModule('operations')}
              />
            )}

            {/* Module 3: Technical Details - Tech Focus */}
            {(permissions?.technical !== 'NONE') && (
              <TechnicalModule
                isExpanded={isModuleExpanded('technical')}
                onToggle={() => toggleModule('technical')}
              />
            )}

            {/* Module 4: Commercial & Legal - Management Focus (RESTRICTED) */}
            {(permissions?.commercial !== 'NONE') && (
              <CommercialModule
                isExpanded={isModuleExpanded('commercial')}
                onToggle={() => toggleModule('commercial')}
              />
            )}

            {/* Module 5: Strategy - Strategy/AM Focus */}
            {(permissions?.strategy !== 'NONE') && (
              <StrategyModule
                isExpanded={isModuleExpanded('strategy')}
                onToggle={() => toggleModule('strategy')}
              />
            )}

            {/* Module 6: Marketing - Marketing Team Focus */}
            {(permissions?.marketing !== 'NONE') && (
              <MarketingModule
                isExpanded={isModuleExpanded('marketing')}
                onToggle={() => toggleModule('marketing')}
              />
            )}
          </div>
        )}
      </main>
    </div>
  );
}
