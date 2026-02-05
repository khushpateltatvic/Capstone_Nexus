import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type {
  User,
  Client,
  Project,
  UniversalContext,
  OperationsData,
  TechnicalData,
  CommercialData,
  StrategyData,
  MarketingData,
  SectionPermissions,
} from '@/types';

interface StoreState {
  // Auth
  user: User | null;
  isAuthenticated: boolean;
  token: string | null;
  setUser: (user: User | null) => void;
  setAuthenticated: (value: boolean) => void;
  setToken: (token: string | null) => void;
  logout: () => void;

  // Selection
  selectedClient: Client | null;
  selectedProject: Project | null;
  setSelectedClient: (client: Client | null) => void;
  setSelectedProject: (project: Project | null) => void;

  // Data
  clients: Client[];
  projects: Project[];
  universalContext: UniversalContext | null;
  operationsData: OperationsData | null;
  technicalData: TechnicalData | null;
  commercialData: CommercialData | null;
  strategyData: StrategyData | null;
  marketingData: MarketingData | null;
  permissions: SectionPermissions | null;

  setClients: (clients: Client[]) => void;
  setProjects: (projects: Project[]) => void;
  setUniversalContext: (data: UniversalContext | null) => void;
  setOperationsData: (data: OperationsData | null) => void;
  setTechnicalData: (data: TechnicalData | null) => void;
  setCommercialData: (data: CommercialData | null) => void;
  setStrategyData: (data: StrategyData | null) => void;
  setMarketingData: (data: MarketingData | null) => void;
  setPermissions: (permissions: SectionPermissions | null) => void;

  // UI State
  sidebarCollapsed: boolean;
  expandedModules: string[];
  activeSection: string;
  currentView: 'dashboard' | 'intelligence' | 'chatbot';

  setSidebarCollapsed: (value: boolean) => void;
  setCurrentView: (view: 'dashboard' | 'intelligence' | 'chatbot') => void;
  toggleModule: (moduleId: string) => void;
  expandAllModules: () => void;
  collapseAllModules: () => void;
  setActiveSection: (section: string) => void;

  // Loading States
  isLoading: boolean;
  loadingMessage: string;
  setIsLoading: (value: boolean) => void;
  setLoadingMessage: (message: string) => void;
}

const defaultModules = ['universal', 'operations', 'technical', 'commercial', 'strategy', 'marketing'];

export const useStore = create<StoreState>()(
  persist(
    (set, get) => ({
      // Auth
      user: null,
      isAuthenticated: false,
      token: null,
      setUser: (user) => set({ user }),
      setAuthenticated: (value) => set({ isAuthenticated: value }),
      setToken: (token) => {
        if (token) {
          localStorage.setItem('nexus_token', token);
        } else {
          localStorage.removeItem('nexus_token');
        }
        set({ token });
      },
      logout: () => {
        localStorage.removeItem('nexus_token');
        set({
          user: null,
          isAuthenticated: false,
          token: null,
          selectedClient: null,
          selectedProject: null,
        });
      },

      // Selection
      selectedClient: null,
      selectedProject: null,
      setSelectedClient: (client) => set({ selectedClient: client }),
      setSelectedProject: (project) => set({ selectedProject: project }),

      // Data
      clients: [],
      projects: [],
      universalContext: null,
      operationsData: null,
      technicalData: null,
      commercialData: null,
      strategyData: null,
      marketingData: null,
      permissions: null,

      setClients: (clients) => set({ clients }),
      setProjects: (projects) => set({ projects }),
      setUniversalContext: (data) => set({ universalContext: data }),
      setOperationsData: (data) => set({ operationsData: data }),
      setTechnicalData: (data) => set({ technicalData: data }),
      setCommercialData: (data) => set({ commercialData: data }),
      setStrategyData: (data) => set({ strategyData: data }),
      setMarketingData: (data) => set({ marketingData: data }),
      setPermissions: (permissions) => set({ permissions }),

      // UI State
      sidebarCollapsed: false,
      expandedModules: defaultModules,
      activeSection: 'dashboard',
      currentView: 'dashboard',

      setSidebarCollapsed: (value) => set({ sidebarCollapsed: value }),
      setCurrentView: (view: 'dashboard' | 'intelligence' | 'chatbot') => set({ currentView: view }),
      toggleModule: (moduleId) => {
        const { expandedModules } = get();
        if (expandedModules.includes(moduleId)) {
          set({ expandedModules: expandedModules.filter(id => id !== moduleId) });
        } else {
          set({ expandedModules: [...expandedModules, moduleId] });
        }
      },
      expandAllModules: () => set({ expandedModules: defaultModules }),
      collapseAllModules: () => set({ expandedModules: [] }),
      setActiveSection: (section) => set({ activeSection: section }),

      // Loading States
      isLoading: false,
      loadingMessage: '',
      setIsLoading: (value) => set({ isLoading: value }),
      setLoadingMessage: (message) => set({ loadingMessage: message }),
    }),
    {
      name: 'nexus-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        token: state.token,
        sidebarCollapsed: state.sidebarCollapsed,
        selectedClient: state.selectedClient,
        selectedProject: state.selectedProject,
        currentView: state.currentView,
      }),
    }
  )
);
