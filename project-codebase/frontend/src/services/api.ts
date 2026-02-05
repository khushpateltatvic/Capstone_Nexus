/* eslint-disable @typescript-eslint/no-unused-vars */
import axios from 'axios';
import type {
  ApiResponse,
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
  Task,
  Blocker,
  Interaction,
  TimelineEvent,
  POCContact,
  SquadMember,
  Experiment,
  Invoice,
  Renewal,
  TechStackItem,
  Credential,
  Implementation,
  UserRole,
} from '@/types';


// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const API_VERSION = '/api/v1';

// Create axios instance
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false,
});

// Request interceptor to add Bearer token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('nexus_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token on 401
      localStorage.removeItem('nexus_token');
    }
    return Promise.reject(error);
  }
);

// Helper function to extract nested data from backend response
const extractValue = (data: any) => {
  if (data?.value !== undefined) return data.value;
  if (data?.data?.value !== undefined) return data.data.value;
  return data;
};

// Auth API
export const authApi = {
  login: async (username: string, password: string): Promise<ApiResponse<{ user: User; token: string }>> => {
    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await apiClient.post(
        `${API_VERSION}/auth/login/access-token`,
        formData,
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }
      );

      const { access_token, user } = response.data;

      // Store token
      localStorage.setItem('nexus_token', access_token);

      return {
        success: true,
        data: {
          user: {
            id: user.email,
            email: user.email,
            name: user.full_name || user.email.split('@')[0],
            role: user.role.toLowerCase() as UserRole,
            job_title: user.job_title,
            department: user.department,
            avatar: user.avatar,
          },
          token: access_token,
        },
      };
    } catch (error: any) {
      console.error('Login error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Login failed',
      };
    }
  },

  getProfile: async (): Promise<ApiResponse<User>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/auth/me`);
      const userData = response.data;

      return {
        success: true,
        data: {
          id: userData.email,
          email: userData.email,
          name: userData.full_name || userData.email.split('@')[0],
          role: userData.role.toLowerCase() as UserRole,
          job_title: userData.job_title,
          department: userData.department,
          avatar: userData.avatar,
        },
      };
    } catch (error: any) {
      console.error('Get profile error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch profile',
      };
    }
  },

  getUsers: async (): Promise<ApiResponse<User[]>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/auth/users`);
      const usersData = response.data.map((user: any) => ({
        id: user.email,
        email: user.email,
        name: user.full_name || user.email.split('@')[0],
        role: user.role.toLowerCase() as UserRole,
        job_title: user.job_title,
        department: user.department,
        avatar: user.avatar,
      }));

      return {
        success: true,
        data: usersData,
      };
    } catch (error: any) {
      console.error('Get users error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch users',
      };
    }
  },

  changePassword: async (currentPassword: string, newPassword: string): Promise<ApiResponse<void>> => {
    try {
      await apiClient.post(`${API_VERSION}/auth/change-password`, {
        current_password: currentPassword,
        new_password: newPassword,
      });

      return {
        success: true,
        message: 'Password changed successfully',
      };
    } catch (error: any) {
      console.error('Change password error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to change password',
      };
    }
  },
};

// Projects API
export const projectsApi = {
  getAll: async (): Promise<ApiResponse<Project[]>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/projects/`);
      const projects = response.data.map((p: any) => ({
        id: p.project_id,
        project_id: p.project_id,
        client_id: p.client_id,
        name: p.name,
        description: p.description,
        department: p.department || 'General',
        assigned_users: p.assigned_users_count || 0,
        created_at: p.created_at,
        updated_at: p.updated_at,
        health_score: 85,
        status: 'active' as const,
      }));
      return { success: true, data: projects };
    } catch (error: any) {
      console.error('Get all projects error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch projects',
      };
    }
  },

  getByClient: async (clientId: string): Promise<ApiResponse<Project[]>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/projects/${clientId}`);
      const projects = response.data.map((p: any) => ({
        id: p.project_id,
        project_id: p.project_id,
        client_id: p.client_id,
        name: p.name,
        description: p.description,
        department: p.department || 'General',
        assigned_users: p.assigned_users_count || 0,
        created_at: p.created_at,
        updated_at: p.updated_at,
        health_score: 85,
        status: 'active' as const,
      }));
      return { success: true, data: projects };
    } catch (error: any) {
      console.error('Get client projects error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch client projects',
      };
    }
  },

  getById: async (clientId: string, projectId: string): Promise<ApiResponse<Project>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/projects/${clientId}/${projectId}`);
      const p = response.data;
      return {
        success: true,
        data: {
          id: p.project_id,
          project_id: p.project_id,
          client_id: p.client_id,
          name: p.name,
          description: p.description,
          department: p.department || 'General',
          assigned_users: p.assigned_users_count || 0,
          created_at: p.created_at,
          updated_at: p.updated_at,
          health_score: 85,
          status: 'active' as const,
        },
      };
    } catch (error: any) {
      console.error('Get project error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch project',
      };
    }
  },

  create: async (project: Partial<Project>): Promise<ApiResponse<Project>> => {
    try {
      const response = await apiClient.post(`${API_VERSION}/projects/`, project);
      return { success: true, data: response.data };
    } catch (error: any) {
      console.error('Create project error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to create project',
      };
    }
  },

  update: async (clientId: string, projectId: string, updates: Partial<Project>): Promise<ApiResponse<Project>> => {
    try {
      const response = await apiClient.patch(`${API_VERSION}/projects/${clientId}/${projectId}`, updates);
      return { success: true, data: response.data };
    } catch (error: any) {
      console.error('Update project error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to update project',
      };
    }
  },

  delete: async (clientId: string, projectId: string): Promise<ApiResponse<void>> => {
    try {
      await apiClient.delete(`${API_VERSION}/projects/${clientId}/${projectId}`);
      return { success: true };
    } catch (error: any) {
      console.error('Delete project error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to delete project',
      };
    }
  },
};

// Clients API
export const clientsApi = {
  getAll: async (): Promise<ApiResponse<Client[]>> => {
    try {
      // Backend returns projects, we can group them by client
      const response = await apiClient.get(`${API_VERSION}/projects/`);
      const projects: Project[] = (response.data || []).map((p: any) => ({
        id: p.project_id || p.id || '',
        project_id: p.project_id,
        client_id: p.client_id,
        name: p.name || 'Untitled Project',
        description: p.description,
        department: p.department || 'General',
        assigned_users: p.assigned_users_count || p.assigned_users || 0,
        created_at: p.created_at || new Date().toISOString(),
        updated_at: p.updated_at || new Date().toISOString(),
        health_score: p.health_score || 85,
        status: (p.status || 'active') as any,
      }));

      // Group projects by client_id to create client list
      const clientMap = new Map<string, Client>();
      projects.forEach(project => {
        if (!clientMap.has(project.client_id)) {
          clientMap.set(project.client_id, {
            id: project.client_id,
            name: project.client_id,
            industry: 'Technology',
            health_score: 85,
            projects: [],
          });
        }
        const projectData = {
          id: project.project_id || project.id || '',
          project_id: project.project_id,
          client_id: project.client_id,
          name: project.name,
          description: project.description,
          department: project.department || 'General',
          assigned_users: project.assigned_users || 0,
          created_at: project.created_at,
          updated_at: project.updated_at,
          health_score: project.health_score || 85,
          status: project.status || 'active',
        };
        clientMap.get(project.client_id)!.projects.push(projectData);
      });

      return { success: true, data: Array.from(clientMap.values()) };
    } catch (error: any) {
      console.error('Get all clients error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch clients',
      };
    }
  },

  getById: async (clientId: string): Promise<ApiResponse<Client>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/projects/${clientId}`);
      const projects: Project[] = (response.data || []).map((p: any) => ({
        id: p.project_id || p.id || '',
        project_id: p.project_id,
        client_id: p.client_id,
        name: p.name || 'Untitled Project',
        description: p.description,
        department: p.department || 'General',
        assigned_users: p.assigned_users_count || p.assigned_users || 0,
        created_at: p.created_at || new Date().toISOString(),
        updated_at: p.updated_at || new Date().toISOString(),
        health_score: p.health_score || 85,
        status: (p.status || 'active') as any,
      }));

      const client: Client = {
        id: clientId,
        name: clientId,
        industry: 'Technology',
        health_score: 85,
        projects: projects,
      };

      return { success: true, data: client };
    } catch (error: any) {
      console.error('Get client error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch client',
      };
    }
  },
};

// Permissions API
export const permissionsApi = {
  getProjectPermissions: async (clientId: string, projectId: string): Promise<ApiResponse<any[]>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/projects/${clientId}/${projectId}/permissions`);
      return { success: true, data: response.data };
    } catch (error: any) {
      console.error('Get project permissions error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch permissions',
      };
    }
  },

  getMyPermissions: async (clientId?: string, projectId?: string): Promise<ApiResponse<SectionPermissions>> => {
    try {
      // If we have client and project, get from project details which includes user_permissions
      if (clientId && projectId) {
        const response = await apiClient.get(`${API_VERSION}/projects/${clientId}/${projectId}`);
        const userPerms = response.data.user_permissions || {};

        const permissions: SectionPermissions = {
          universal: (userPerms.universal_context || 'VIEW').toUpperCase() as any,
          operations: (userPerms.operations || 'VIEW').toUpperCase() as any,
          technical: (userPerms.technical || 'VIEW').toUpperCase() as any,
          commercial: (userPerms.commercial || 'NONE').toUpperCase() as any,
          strategy: (userPerms.strategy || 'VIEW').toUpperCase() as any,
          marketing: (userPerms.marketing || 'VIEW').toUpperCase() as any,
        };
        return { success: true, data: permissions };
      }

      // Default permissions based on user role (moved logic to helper for reuse in catch)
      const getFallbackPermissions = async (): Promise<SectionPermissions> => {
        try {
          const profileRes = await authApi.getProfile();
          if (profileRes.success && profileRes.data) {
            const role = profileRes.data.role;
            return {
              universal: 'VIEW',
              operations: 'VIEW',
              technical: role === 'trainee' ? 'VIEW' : 'EDIT',
              commercial: ['head', 'admin', 'director'].includes(role) ? 'VIEW' : 'NONE',
              strategy: 'VIEW',
              marketing: 'VIEW',
            };
          }
        } catch (e) {
          console.error('Fallback permissions error:', e);
        }
        return {
          universal: 'VIEW',
          operations: 'VIEW',
          technical: 'VIEW',
          commercial: 'NONE',
          strategy: 'VIEW',
          marketing: 'VIEW',
        };
      };

      return { success: true, data: await getFallbackPermissions() };
    } catch (error: any) {
      console.error('Get my permissions error (switching to fallback):', error);

      // Attempt to get fallback permissions even on API failure (e.g. 404)
      const getFinalFallback = () => ({
        universal: 'VIEW' as any,
        operations: 'VIEW' as any,
        technical: 'VIEW' as any,
        commercial: 'NONE' as any,
        strategy: 'VIEW' as any,
        marketing: 'VIEW' as any,
      });

      try {
        const profileRes = await authApi.getProfile();
        if (profileRes.success && profileRes.data) {
          const role = profileRes.data.role;
          return {
            success: true,
            data: {
              universal: 'VIEW',
              operations: 'VIEW',
              technical: role === 'trainee' ? 'VIEW' : 'EDIT',
              commercial: ['head', 'admin', 'director'].includes(role) ? 'VIEW' : 'NONE',
              strategy: 'VIEW',
              marketing: 'VIEW',
            }
          };
        }
      } catch (innerError) {
        // Nested failure, return hardcoded defaults
      }

      return {
        success: true,
        data: getFinalFallback()
      };
    }
  },

  assignUser: async (clientId: string, projectId: string, data: any): Promise<ApiResponse<any>> => {
    try {
      const response = await apiClient.post(`${API_VERSION}/projects/${clientId}/${projectId}/permissions/assign`, data);
      return { success: true, data: response.data };
    } catch (error: any) {
      console.error('Assign user error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to assign user',
      };
    }
  },

  removeUser: async (clientId: string, projectId: string, email: string): Promise<ApiResponse<void>> => {
    try {
      await apiClient.delete(`${API_VERSION}/projects/${clientId}/${projectId}/permissions/${email}`);
      return { success: true };
    } catch (error: any) {
      console.error('Remove user error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to remove user',
      };
    }
  },
};

// Universal Context API - Real backend calls
export const universalContextApi = {
  get: async (clientId: string, projectId: string): Promise<ApiResponse<UniversalContext>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/universal-context/${clientId}/${projectId}`);
      const data = response.data.data || response.data;

      // Extract arrays using helper
      const squadArray = extractValue(data.squad) || [];
      const pocArray = extractValue(data.poc_map) || [];
      const timelineArray = extractValue(data.timeline) || [];
      const clientProfileData = extractValue(data.client_profile) || {};
      const hygieneData = extractValue(data.communication_hygiene) || {};
      const engagementType = extractValue(data.engagement_type) || 'Project';

      // Transform backend response to frontend format
      const universalContext: UniversalContext = {
        client_profile: {
          name: clientProfileData.company_name || clientProfileData.name || clientId,
          industry: clientProfileData.industry || 'Technology',
          health_score: clientProfileData.health_score === 'Green' ? 85 :
            clientProfileData.health_score === 'Yellow' ? 60 :
              typeof clientProfileData.health_score === 'number' ? clientProfileData.health_score : 85,
          account_tier: clientProfileData.account_tier || 'enterprise',
          contract_start: clientProfileData.engagement_start_date || clientProfileData.contract_start || '',
          contract_end: clientProfileData.contract_end || '',
          account_manager: clientProfileData.account_manager || '',
        },
        engagement_type: engagementType,
        internal_squad: (Array.isArray(squadArray) ? squadArray : []).map((s: any, idx: number) => ({
          id: idx.toString(),
          name: s.name || s.value || s || '',
          role: s.role || 'Team Member',
          email: s.email || '',
          department: 'Engineering',
        })),
        poc_map: (Array.isArray(pocArray) ? pocArray : []).map((poc: any, idx: number) => ({
          id: idx.toString(),
          name: poc.name || '',
          role: poc.role || '',
          email: poc.email || '',
          phone: poc.phone || '',
          is_primary: idx === 0,
          influence_level: (poc.influence || 'medium').toLowerCase(),
        })),
        communication_hygiene: {
          last_meeting: hygieneData.last_meeting || '',
          last_email: hygieneData.last_email || '',
          response_time_avg: hygieneData.response_time_avg || hygieneData.response_time || 'N/A',
          meetings_this_month: hygieneData.meetings_this_month || 0,
          emails_this_month: hygieneData.emails_this_month || 0,
          health_status: hygieneData.meeting_frequency === 'Weekly' ? 'excellent' : 'good',
        },
        ai_summary: extractValue(data.summary) || 'No summary available.',
        timeline: (Array.isArray(timelineArray) ? timelineArray : []).map((t: any, idx: number) => ({
          id: idx.toString(),
          date: t.date || '',
          event: t.event || '',
          significance: (t.significance || 'medium').toLowerCase(),
          category: t.category || 'milestone',
        })),
        important_notes: extractValue(data.important_notes) || [],
        google_workspace: extractValue(data.google_workspace) || [],
      };

      return { success: true, data: universalContext };
    } catch (error: any) {
      console.error('Get universal context error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch universal context',
      };
    }
  },

  getSummary: async (clientId: string, projectId: string): Promise<ApiResponse<string>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/universal-context/${clientId}/${projectId}/summary`);
      const summary = extractValue(response.data) || 'No summary available.';
      return { success: true, data: summary };
    } catch (error: any) {
      console.error('Get summary error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch summary' };
    }
  },

  updateSummary: async (clientId: string, projectId: string, summary: string): Promise<ApiResponse<void>> => {
    try {
      await apiClient.put(`${API_VERSION}/universal-context/${clientId}/${projectId}/summary`, { value: summary });
      return { success: true };
    } catch (error: any) {
      console.error('Update summary error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to update summary' };
    }
  },

  getTimeline: async (clientId: string, projectId: string): Promise<ApiResponse<TimelineEvent[]>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/universal-context/${clientId}/${projectId}/timeline`);
      const data = extractValue(response.data) || [];
      const timeline = Array.isArray(data) ? data.map((t: any, idx: number) => ({
        id: idx.toString(),
        date: t.value?.date || t.date || '',
        event: t.value?.event || t.event || '',
        significance: t.value?.significance || 'medium',
        category: t.value?.category || 'milestone',
      })) : [];
      return { success: true, data: timeline };
    } catch (error: any) {
      console.error('Get timeline error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch timeline' };
    }
  },

  addTimelineEvent: async (clientId: string, projectId: string, event: Omit<TimelineEvent, 'id'>): Promise<ApiResponse<TimelineEvent>> => {
    try {
      await apiClient.post(`${API_VERSION}/universal-context/${clientId}/${projectId}/timeline`, event);
      return { success: true, data: { ...event, id: Date.now().toString() } };
    } catch (error: any) {
      console.error('Add timeline event error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to add timeline event' };
    }
  },

  getPOCMap: async (clientId: string, projectId: string): Promise<ApiResponse<POCContact[]>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/universal-context/${clientId}/${projectId}/poc_map`);
      const data = extractValue(response.data) || [];
      const pocMap = Array.isArray(data) ? data.map((poc: any, idx: number) => ({
        id: idx.toString(),
        name: poc.value?.name || poc.name || '',
        role: poc.value?.role || poc.role || '',
        email: poc.value?.email || poc.email || '',
        phone: poc.value?.phone || poc.phone || '',
        is_primary: idx === 0,
        influence_level: poc.value?.influence || poc.influence || 'medium',
      })) : [];
      return { success: true, data: pocMap };
    } catch (error: any) {
      console.error('Get POC map error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch POC map' };
    }
  },

  addPOC: async (clientId: string, projectId: string, poc: Omit<POCContact, 'id'>): Promise<ApiResponse<POCContact>> => {
    try {
      await apiClient.post(`${API_VERSION}/universal-context/${clientId}/${projectId}/poc_map`, poc);
      return { success: true, data: { ...poc, id: Date.now().toString() } };
    } catch (error: any) {
      console.error('Add POC error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to add POC' };
    }
  },

  updateHygiene: async (clientId: string, projectId: string, hygiene: Partial<UniversalContext['communication_hygiene']>): Promise<ApiResponse<void>> => {
    try {
      await apiClient.put(`${API_VERSION}/universal-context/${clientId}/${projectId}/communication`, hygiene);
      return { success: true };
    } catch (error: any) {
      console.error('Update hygiene error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to update communication hygiene' };
    }
  },

  addSquadMember: async (clientId: string, projectId: string, member: Omit<SquadMember, 'id'>): Promise<ApiResponse<SquadMember>> => {
    try {
      const response = await apiClient.post(`${API_VERSION}/universal-context/${clientId}/${projectId}/internal_squad`, member);
      return { success: true, data: response.data.member };
    } catch (error: any) {
      console.error('Add squad member error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to add squad member' };
    }
  },

  getUsers: async (): Promise<ApiResponse<User[]>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/universal-context/squad-search-users`);
      return {
        success: true, data: response.data.users.map((u: any) => ({
          id: u.email,
          email: u.email,
          name: u.name,
          role: u.role.toLowerCase() as UserRole,
          department: u.department,
        }))
      };
    } catch (error: any) {
      console.error('Get users error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch users' };
    }
  },

  getImportantNotes: async (clientId: string, projectId: string): Promise<ApiResponse<string[]>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/universal-context/${clientId}/${projectId}/important_notes`);
      const data = extractValue(response.data) || [];
      return { success: true, data: Array.isArray(data) ? data : [] };
    } catch (error: any) {
      console.error('Get important notes error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch important notes' };
    }
  },

  addImportantNote: async (clientId: string, projectId: string, note: string): Promise<ApiResponse<void>> => {
    try {
      await apiClient.post(`${API_VERSION}/universal-context/${clientId}/${projectId}/important_notes`, { note });
      return { success: true };
    } catch (error: any) {
      console.error('Add important note error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to add note' };
    }
  },

  getGoogleWorkspace: async (clientId: string, projectId: string): Promise<ApiResponse<string[]>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/universal-context/${clientId}/${projectId}/google_workspace`);
      const data = extractValue(response.data) || [];
      return { success: true, data: Array.isArray(data) ? data : [] };
    } catch (error: any) {
      console.error('Get google workspace error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch google workspace' };
    }
  },

  addGoogleWorkspace: async (clientId: string, projectId: string, items: string[]): Promise<ApiResponse<void>> => {
    try {
      await apiClient.put(`${API_VERSION}/universal-context/${clientId}/${projectId}/google_workspace`, items);
      return { success: true };
    } catch (error: any) {
      console.error('Add google workspace error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to add google workspace items' };
    }
  },

  updateClientProfile: async (clientId: string, projectId: string, profile: any): Promise<ApiResponse<void>> => {
    try {
      await apiClient.put(`${API_VERSION}/universal-context/${clientId}/${projectId}/client_profile`, { value: profile });
      return { success: true };
    } catch (error: any) {
      console.error('Update client profile error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to update client profile' };
    }
  },

  updateTimeline: async (clientId: string, projectId: string, timeline: any[]): Promise<ApiResponse<void>> => {
    try {
      await apiClient.put(`${API_VERSION}/universal-context/${clientId}/${projectId}/timeline`, timeline);
      return { success: true };
    } catch (error: any) {
      console.error('Update timeline error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to update timeline' };
    }
  },

  updateImportantNotes: async (clientId: string, projectId: string, notes: string[]): Promise<ApiResponse<void>> => {
    try {
      await apiClient.put(`${API_VERSION}/universal-context/${clientId}/${projectId}/important_notes`, notes);
      return { success: true };
    } catch (error: any) {
      console.error('Update important notes error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to update important notes' };
    }
  },

  updateSquad: async (clientId: string, projectId: string, squad: any[]): Promise<ApiResponse<void>> => {
    try {
      await apiClient.put(`${API_VERSION}/universal-context/${clientId}/${projectId}/internal_squad`, squad);
      return { success: true };
    } catch (error: any) {
      console.error('Update squad error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to update squad' };
    }
  },
};

// Operations API - Real backend calls
export const operationsApi = {
  get: async (clientId: string, projectId: string): Promise<ApiResponse<OperationsData>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/operations/${clientId}/${projectId}`);
      const data = response.data.data || response.data;

      // Extract arrays from nested value structures (backend stores as {value: [...], source_doc: ..., confidence: ...})
      // Extract arrays using helper
      const upcomingArray = extractValue(data.task_board_upcoming) || [];
      const ongoingArray = extractValue(data.task_board_ongoing) || [];
      const completedArray = extractValue(data.task_board_completed) || [];
      const blockersArray = extractValue(data.blockers) || [];
      const interactionsArray = extractValue(data.recent_interactions) || [];

      const engagementStatus = extractValue(data.engagement_status) || 'Active'; // Maintenance, etc.

      // Map engagement status to traffic light color
      const mapStatus = (status: string): 'green' | 'yellow' | 'red' => {
        const s = (status || '').toLowerCase().replace(/_/g, '');
        if (s === 'atrisk' || s === 'yellow' || s === 'warning') return 'yellow';
        if (s === 'critical' || s === 'red' || s === 'danger') return 'red';
        return 'green';
      };

      const rawTrafficStatus = data.traffic_light?.value || 'green';

      const operationsData: OperationsData = {
        traffic_light: {
          status: mapStatus(rawTrafficStatus),
          reason: data.traffic_light?.reasoning || data.engagement_status?.source_doc || 'Project on track',
          updated_at: data.traffic_light?.timestamp || new Date().toISOString(),
          updated_by: data.traffic_light?.updated_by || 'System',
        },
        engagement_status: engagementStatus,
        tasks: {
          upcoming: (Array.isArray(upcomingArray) ? upcomingArray : []).map((t: any, idx: number) => ({
            id: idx.toString(),
            title: t.name || '',
            description: t.description || '',
            assignee: t.owner || '',
            due_date: t.due_date || '',
            priority: 'medium' as const,
            status: 'pending' as const,
            created_at: new Date().toISOString(),
          })),
          ongoing: (Array.isArray(ongoingArray) ? ongoingArray : []).map((t: any, idx: number) => ({
            id: idx.toString(),
            title: t.name || '',
            description: t.description || '',
            assignee: t.owner || '',
            due_date: t.due_date || '',
            priority: 'medium' as const,
            status: 'in_progress' as const,
            created_at: new Date().toISOString(),
          })),
          completed: (Array.isArray(completedArray) ? completedArray : []).map((t: any, idx: number) => ({
            id: idx.toString(),
            title: t.name || '',
            description: t.description || '',
            assignee: t.owner || '',
            due_date: t.completed_date || t.due_date || '',
            priority: 'medium' as const,
            status: 'completed' as const,
            created_at: new Date().toISOString(),
          })),
        },
        blockers: (Array.isArray(blockersArray) ? blockersArray : []).map((b: any, idx: number) => ({
          id: idx.toString(),
          description: b.issue || '',
          severity: (b.severity || 'medium').toLowerCase().trim() as any,
          reported_by: b.owner || 'Team',
          reported_at: new Date().toISOString(),
          status: 'active' as const,
        })),
        interactions: (Array.isArray(interactionsArray) ? interactionsArray : []).map((i: any, idx: number) => ({
          id: idx.toString(),
          date: i.date || new Date().toISOString(),
          type: (i.type || 'meeting').toLowerCase() as any,
          summary: i.summary || '',
          participants: [],
        })),
      };

      return { success: true, data: operationsData };
    } catch (error: any) {
      console.error('Get operations error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch operations data',
      };
    }
  },

  getTrafficLight: async (clientId: string, projectId: string): Promise<ApiResponse<OperationsData['traffic_light']>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/operations/${clientId}/${projectId}/traffic_light`);
      const data = extractValue(response.data);
      return {
        success: true,
        data: {
          status: data?.value || data || 'green',
          reason: data?.reasoning || 'Project on track',
          updated_at: new Date().toISOString(),
          updated_by: 'System',
        },
      };
    } catch (error: any) {
      console.error('Get traffic light error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch traffic light' };
    }
  },

  updateTrafficLight: async (clientId: string, projectId: string, status: OperationsData['traffic_light']): Promise<ApiResponse<void>> => {
    try {
      await apiClient.put(`${API_VERSION}/operations/${clientId}/${projectId}/traffic_light`, {
        value: status.status,
        reasoning: status.reason,
      });
      return { success: true };
    } catch (error: any) {
      console.error('Update traffic light error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to update traffic light' };
    }
  },

  getTasks: async (clientId: string, projectId: string): Promise<ApiResponse<Task[]>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/operations/${clientId}/${projectId}/tasks`);
      const data = extractValue(response.data) || { upcoming: [], ongoing: [] };
      const tasks = [
        ...(data.upcoming || []).map((t: any) => ({ ...t, status: 'pending' })),
        ...(data.ongoing || []).map((t: any) => ({ ...t, status: 'in_progress' })),
      ];
      return { success: true, data: tasks };
    } catch (error: any) {
      console.error('Get tasks error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch tasks' };
    }
  },

  addTask: async (clientId: string, projectId: string, task: Omit<Task, 'id' | 'created_at'>): Promise<ApiResponse<Task>> => {
    try {
      const endpoint = task.status === 'pending' ? 'tasks/upcoming' : 'tasks/ongoing';
      await apiClient.post(`${API_VERSION}/operations/${clientId}/${projectId}/${endpoint}`, task);
      return { success: true, data: { ...task, id: Date.now().toString(), created_at: new Date().toISOString() } };
    } catch (error: any) {
      console.error('Add task error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to add task' };
    }
  },

  updateTask: async (clientId: string, projectId: string, taskId: string, task: Partial<Task>): Promise<ApiResponse<Task>> => {
    try {
      const endpoint = task.status === 'pending' ? 'tasks/upcoming' : task.status === 'in_progress' ? 'tasks/ongoing' : 'tasks/completed';
      await apiClient.put(`${API_VERSION}/operations/${clientId}/${projectId}/${endpoint}/${taskId}`, {
        name: task.title,
        description: task.description,
        owner: task.assignee,
        due_date: task.due_date,
        priority: task.priority,
      });
      return { success: true, data: task as Task };
    } catch (error: any) {
      console.error('Update task error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to update task' };
    }
  },

  deleteTask: async (clientId: string, projectId: string, taskId: string, status: string): Promise<ApiResponse<void>> => {
    try {
      const endpoint = status === 'pending' ? 'tasks/upcoming' : status === 'in_progress' ? 'tasks/ongoing' : 'tasks/completed';
      await apiClient.delete(`${API_VERSION}/operations/${clientId}/${projectId}/${endpoint}/${taskId}`);
      return { success: true };
    } catch (error: any) {
      console.error('Delete task error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to delete task' };
    }
  },

  getBlockers: async (clientId: string, projectId: string): Promise<ApiResponse<Blocker[]>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/operations/${clientId}/${projectId}/blockers`);
      const data = extractValue(response.data) || [];
      const blockers = Array.isArray(data) ? data.map((b: any, idx: number) => ({
        id: idx.toString(),
        description: b.value?.issue || b.issue || '',
        severity: (b.value?.severity || b.severity || 'medium').toLowerCase() as any,
        reported_by: 'Team',
        reported_at: new Date().toISOString(),
        status: 'active' as const,
      })) : [];
      return { success: true, data: blockers };
    } catch (error: any) {
      console.error('Get blockers error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch blockers' };
    }
  },

  addBlocker: async (clientId: string, projectId: string, blocker: Omit<Blocker, 'id' | 'reported_at'>): Promise<ApiResponse<Blocker>> => {
    try {
      await apiClient.post(`${API_VERSION}/operations/${clientId}/${projectId}/blockers`, {
        issue: blocker.description,
        severity: blocker.severity,
      });
      return { success: true, data: { ...blocker, id: Date.now().toString(), reported_at: new Date().toISOString() } };
    } catch (error: any) {
      console.error('Add blocker error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to add blocker' };
    }
  },

  updateBlocker: async (clientId: string, projectId: string, blockerId: string, blocker: Partial<Blocker>): Promise<ApiResponse<Blocker>> => {
    try {
      await apiClient.put(`${API_VERSION}/operations/${clientId}/${projectId}/blockers/${blockerId}`, {
        issue: blocker.description,
        severity: blocker.severity,
        status: blocker.status,
      });
      return { success: true, data: blocker as Blocker };
    } catch (error: any) {
      console.error('Update blocker error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to update blocker' };
    }
  },

  deleteBlocker: async (clientId: string, projectId: string, blockerId: string): Promise<ApiResponse<void>> => {
    try {
      await apiClient.delete(`${API_VERSION}/operations/${clientId}/${projectId}/blockers/${blockerId}`);
      return { success: true };
    } catch (error: any) {
      console.error('Delete blocker error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to delete blocker' };
    }
  },

  resolveBlocker: async (_clientId: string, _projectId: string, _blockerId: string): Promise<ApiResponse<void>> => {
    // Backend may not have direct resolve endpoint - update blockers list
    return { success: true };
  },

  getInteractions: async (clientId: string, projectId: string): Promise<ApiResponse<Interaction[]>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/operations/${clientId}/${projectId}/interactions`);
      const data = extractValue(response.data) || [];
      const interactions = Array.isArray(data) ? data.map((i: any, idx: number) => ({
        id: idx.toString(),
        date: new Date().toISOString(),
        type: 'meeting' as const,
        summary: i.value || i || '',
        participants: [],
      })) : [];
      return { success: true, data: interactions };
    } catch (error: any) {
      console.error('Get interactions error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch interactions' };
    }
  },

  addInteraction: async (clientId: string, projectId: string, interaction: Omit<Interaction, 'id'>): Promise<ApiResponse<Interaction>> => {
    try {
      await apiClient.post(`${API_VERSION}/operations/${clientId}/${projectId}/interactions`, {
        value: interaction.summary,
        type: interaction.type,
        date: interaction.date,
        participants: interaction.participants,
      });
      return { success: true, data: { ...interaction, id: Date.now().toString() } };
    } catch (error: any) {
      console.error('Add interaction error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to add interaction' };
    }
  },

  updateInteraction: async (clientId: string, projectId: string, interactionId: string, interaction: Partial<Interaction>): Promise<ApiResponse<Interaction>> => {
    try {
      await apiClient.put(`${API_VERSION}/operations/${clientId}/${projectId}/interactions/${interactionId}`, {
        value: interaction.summary,
        type: interaction.type,
        date: interaction.date,
        participants: interaction.participants,
      });
      return { success: true, data: interaction as Interaction };
    } catch (error: any) {
      console.error('Update interaction error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to update interaction' };
    }
  },

  deleteInteraction: async (clientId: string, projectId: string, interactionId: string): Promise<ApiResponse<void>> => {
    try {
      await apiClient.delete(`${API_VERSION}/operations/${clientId}/${projectId}/interactions/${interactionId}`);
      return { success: true };
    } catch (error: any) {
      console.error('Delete interaction error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to delete interaction' };
    }
  },
};

// Technical API - Real backend calls
export const technicalApi = {
  get: async (clientId: string, projectId: string): Promise<ApiResponse<TechnicalData>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/technical/${clientId}/${projectId}`);
      const data = response.data.data || response.data;

      // Extract arrays from nested value structures
      const credentialsArray = extractValue(data.access_credentials) || [];
      const implementationsArray = extractValue(data.implementation_log) || [];
      const experimentsArray = extractValue(data.experiment_results) || [];

      const technicalData: TechnicalData = {
        tech_stack: (() => {
          const raw = data.tech_stack?.value || data.tech_stack || [];

          // CASE 1: The API returns a direct array of items
          if (Array.isArray(raw)) {
            return raw.map((t: any, idx: number) => ({
              id: idx.toString(),
              technology: t.name || t.technology || (typeof t === 'string' ? t : ''),
              category: t.category || 'General',
              status: (t.status || 'active').toLowerCase() as any,
            }));
          }

          // CASE 2: The API returns an object with status keys (active, planned, etc.)
          if (typeof raw === 'object' && raw !== null) {
            const flat: TechStackItem[] = [];
            ['active', 'planned', 'deprecated', 'current', 'added'].forEach(status => {
              const items = raw[status];
              if (Array.isArray(items)) {
                items.forEach((tech: any, i: number) => {
                  flat.push({
                    id: `${status}-${i}`,
                    // Handle simple strings like "Google Sheets" or objects
                    technology: typeof tech === 'string' ? tech : (tech.name || tech.technology || ''),
                    category: typeof tech === 'object' ? (tech.category || 'General') : 'General',
                    status: (status === 'current' || status === 'added') ? 'active' as const : status as any,
                  });
                });
              }
            });
            return flat;
          }
          return [];
        })(),
        credentials: (Array.isArray(credentialsArray) ? credentialsArray : []).map((c: any, idx: number) => ({
          id: idx.toString(),
          system: c.service || c.system || '',
          url: c.url || '',
          username: (c.access_method || '') + (c.username ? ` (${c.username})` : ''),
          status: 'active' as const,
          last_verified: '',
          notes: '',
        })),
        implementations: (Array.isArray(implementationsArray) ? implementationsArray : []).map((i: any, idx: number) => ({
          id: idx.toString(),
          title: i.task || i.title || '',
          description: '',
          date: i.date || new Date().toISOString(),
          implemented_by: i.owner || 'Team',
          category: 'General',
        })),
        experiments: (Array.isArray(experimentsArray) ? experimentsArray : []).map((e: any, idx: number) => ({
          id: idx.toString(),
          name: e.name || e.value || '',
          hypothesis: e.hypothesis || (e.variant_a ? `A/B Test: ${e.variant_a.name} vs ${e.variant_b?.name}` : ''),
          status: 'completed' as const,
          results: e.results || e.winner ? `Winner: ${e.winner}. Improvement: ${e.improvement}` : e.value || '',
        })),
      };

      return { success: true, data: technicalData };
    } catch (error: any) {
      console.error('Get technical error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch technical data',
      };
    }
  },

  getTechStack: async (clientId: string, projectId: string): Promise<ApiResponse<TechStackItem[]>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/technical/${clientId}/${projectId}/tech_stack`);

      const data = response.data?.data?.value || response.data?.value || response.data || [];

      const techStack: TechStackItem[] = (() => {
        const raw = data;

        // CASE 1: The API returns a direct array of items
        if (Array.isArray(raw)) {
          const extracted_data = raw.map((t: any, idx: number) => ({
            id: idx.toString(),
            technology: t.name || t.technology || (typeof t === 'string' ? t : ''),
            category: t.category || 'General',
            status: (t.status || 'active').toLowerCase() as any,
          }));
          return extracted_data;
        }

        // CASE 2: The API returns an object with status keys (active, planned, etc.)
        // This matches your provided JSON where raw is { active: [...], planned: [], ... }
        if (typeof raw === 'object' && raw !== null) {
          const flat: TechStackItem[] = [];
          ['active', 'planned', 'deprecated', 'current', 'added'].forEach(status => {
            const items = raw[status];
            if (Array.isArray(items)) {
              items.forEach((tech: any, i: number) => {
                flat.push({
                  id: `${status}-${i}`,
                  // Handle simple strings like "Google Sheets" or objects
                  technology: typeof tech === 'string' ? tech : (tech.name || tech.technology || ''),
                  category: typeof tech === 'object' ? (tech.category || 'General') : 'General',
                  status: (status === 'current' || status === 'added') ? 'active' as const : status as any,
                });
              });
            }
          });
          return flat;
        }
        return [];
      })();

      return { success: true, data: techStack };

    } catch (error: any) {
      console.error('Get tech stack error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch tech stack' };
    }
  },

  addTechStackItem: async (clientId: string, projectId: string, item: Omit<TechStackItem, 'id'>): Promise<ApiResponse<TechStackItem>> => {
    try {
      await apiClient.post(`${API_VERSION}/technical/${clientId}/${projectId}/tech_stack`, {
        name: item.technology,
        status: item.status,
      });
      return { success: true, data: { ...item, id: Date.now().toString() } };
    } catch (error: any) {
      console.error('Add tech stack item error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to add tech stack item' };
    }
  },

  updateTechStackItem: async (clientId: string, projectId: string, itemId: string, item: Partial<TechStackItem>): Promise<ApiResponse<TechStackItem>> => {
    try {
      await apiClient.put(`${API_VERSION}/technical/${clientId}/${projectId}/tech_stack/${itemId}`, {
        name: item.technology,
        category: item.category,
        status: item.status,
      });
      return { success: true, data: { ...item, id: itemId } as TechStackItem };
    } catch (error: any) {
      console.error('Update tech stack item error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to update tech stack item' };
    }
  },

  deleteTechStackItem: async (clientId: string, projectId: string, itemId: string): Promise<ApiResponse<void>> => {
    try {
      await apiClient.delete(`${API_VERSION}/technical/${clientId}/${projectId}/tech_stack/${itemId}`);
      return { success: true };
    } catch (error: any) {
      console.error('Delete tech stack item error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to delete tech stack item' };
    }
  },

  getCredentials: async (clientId: string, projectId: string): Promise<ApiResponse<Credential[]>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/technical/${clientId}/${projectId}/credentials`);
      // Backend returns: { field: "access_credentials", data: { value: [...] } }
      const data = response.data?.data?.value || response.data?.value || response.data || [];
      const credentials = (Array.isArray(data) ? data : []).map((c: any, idx: number) => ({
        id: idx.toString(),
        system: c.service || c.system || '',
        url: c.url || '',
        username: c.username || c.access_method || '',
        status: (c.status || 'active').toLowerCase() as any,
        last_verified: c.last_verified || '',
        notes: c.notes || '',
      }));
      return { success: true, data: credentials };
    } catch (error: any) {
      console.error('Get credentials error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch credentials' };
    }
  },

  addCredential: async (clientId: string, projectId: string, credential: Omit<Credential, 'id'>): Promise<ApiResponse<Credential>> => {
    try {
      await apiClient.post(`${API_VERSION}/technical/${clientId}/${projectId}/credentials`, credential);
      return { success: true, data: { ...credential, id: Date.now().toString() } };
    } catch (error: any) {
      console.error('Add credential error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to add credential' };
    }
  },

  updateCredential: async (clientId: string, projectId: string, credentialId: string, credential: Partial<Credential>): Promise<ApiResponse<Credential>> => {
    try {
      await apiClient.put(`${API_VERSION}/technical/${clientId}/${projectId}/credentials/${credentialId}`, credential);
      return { success: true, data: { ...credential, id: credentialId } as Credential };
    } catch (error: any) {
      console.error('Update credential error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to update credential' };
    }
  },

  deleteCredential: async (clientId: string, projectId: string, credentialId: string): Promise<ApiResponse<void>> => {
    try {
      await apiClient.delete(`${API_VERSION}/technical/${clientId}/${projectId}/credentials/${credentialId}`);
      return { success: true };
    } catch (error: any) {
      console.error('Delete credential error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to delete credential' };
    }
  },

  getExperiments: async (clientId: string, projectId: string): Promise<ApiResponse<Experiment[]>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/technical/${clientId}/${projectId}/experiments`);
      const data = response.data?.data?.value || response.data?.value || response.data || [];
      const experiments = (Array.isArray(data) ? data : []).map((e: any, idx: number) => ({
        id: idx.toString(),
        name: e.name || e.value || e.title || (typeof e === 'string' ? e : ''),
        hypothesis: e.hypothesis || '',
        status: (e.status || 'completed').toLowerCase() as any,
        results: e.results || e.result || e.value || '',
        winner: e.winner || '',
        end_date: e.deployed_date || e.end_date || '',
      }));
      return { success: true, data: experiments };
    } catch (error: any) {
      console.error('Get experiments error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch experiments' };
    }
  },

  addExperiment: async (clientId: string, projectId: string, experiment: Omit<Experiment, 'id'>): Promise<ApiResponse<Experiment>> => {
    try {
      await apiClient.post(`${API_VERSION}/technical/${clientId}/${projectId}/experiments`, {
        value: experiment.name,
      });
      return { success: true, data: { ...experiment, id: Date.now().toString() } };
    } catch (error: any) {
      console.error('Add experiment error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to add experiment' };
    }
  },

  updateExperiment: async (clientId: string, projectId: string, experimentId: string, experiment: Partial<Experiment>): Promise<ApiResponse<Experiment>> => {
    try {
      await apiClient.put(`${API_VERSION}/technical/${clientId}/${projectId}/experiments/${experimentId}`, {
        name: experiment.name,
        hypothesis: experiment.hypothesis,
        status: experiment.status,
        results: experiment.results,
      });
      return { success: true, data: { ...experiment, id: experimentId } as Experiment };
    } catch (error: any) {
      console.error('Update experiment error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to update experiment' };
    }
  },

  deleteExperiment: async (clientId: string, projectId: string, experimentId: string): Promise<ApiResponse<void>> => {
    try {
      await apiClient.delete(`${API_VERSION}/technical/${clientId}/${projectId}/experiments/${experimentId}`);
      return { success: true };
    } catch (error: any) {
      console.error('Delete experiment error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to delete experiment' };
    }
  },

  getImplementations: async (clientId: string, projectId: string): Promise<ApiResponse<Implementation[]>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/technical/${clientId}/${projectId}/implementations`);
      const data = response.data?.data?.value || response.data?.value || response.data || [];
      const implementations = (Array.isArray(data) ? data : []).map((i: any, idx: number) => ({
        id: idx.toString(),
        title: i.task || i.title || '',
        description: i.description || '',
        date: i.date || '',
        implemented_by: i.owner || i.implemented_by || '',
        category: i.category || 'General',
        impact: i.impact || '',
      }));
      return { success: true, data: implementations };
    } catch (error: any) {
      console.error('Get implementations error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch implementations' };
    }
  },

  addImplementation: async (clientId: string, projectId: string, implementation: Omit<Implementation, 'id'>): Promise<ApiResponse<Implementation>> => {
    try {
      await apiClient.post(`${API_VERSION}/technical/${clientId}/${projectId}/implementations`, {
        task: implementation.title,
        date: implementation.date,
        owner: implementation.implemented_by,
        description: implementation.description,
      });
      return { success: true, data: { ...implementation, id: Date.now().toString() } };
    } catch (error: any) {
      console.error('Add implementation error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to add implementation' };
    }
  },

  updateImplementation: async (clientId: string, projectId: string, implementationId: string, implementation: Partial<Implementation>): Promise<ApiResponse<Implementation>> => {
    try {
      await apiClient.put(`${API_VERSION}/technical/${clientId}/${projectId}/implementations/${implementationId}`, {
        task: implementation.title,
        date: implementation.date,
        owner: implementation.implemented_by,
        description: implementation.description,
      });
      return { success: true, data: { ...implementation, id: implementationId } as Implementation };
    } catch (error: any) {
      console.error('Update implementation error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to update implementation' };
    }
  },

  deleteImplementation: async (clientId: string, projectId: string, implementationId: string): Promise<ApiResponse<void>> => {
    try {
      await apiClient.delete(`${API_VERSION}/technical/${clientId}/${projectId}/implementations/${implementationId}`);
      return { success: true };
    } catch (error: any) {
      console.error('Delete implementation error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to delete implementation' };
    }
  },
};

// Commercial API - Real backend calls
export const commercialApi = {
  get: async (clientId: string, projectId: string): Promise<ApiResponse<CommercialData>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/commercial/${clientId}/${projectId}`);
      const data = response.data.data || response.data;

      // Extract arrays and objects from nested value structures
      const sowData = extractValue(data.active_sow) || {};
      const financialData = extractValue(data.financial_overview) || {};
      const invoicesArray = extractValue(data.invoices) || [];
      const renewalsArray = extractValue(data.upcoming_renewals) || [];
      const revenueArray = extractValue(data.revenue_channels) || [];

      // Helper to parse currency strings like "$75,000"
      const parseCurrency = (val: string | number): number => {
        if (typeof val === 'number') return val;
        if (typeof val === 'string') {
          return parseFloat(val.replace(/[$,]/g, '')) || 0;
        }
        return 0;
      };

      const commercialData: CommercialData = {
        sow: {
          sow_id: sowData.sow_number || sowData.sow_id || '',
          title: 'Statement of Work',
          value: parseCurrency(sowData.contract_value),
          currency: 'USD',
          start_date: sowData.start_date || '',
          end_date: sowData.end_date || '',
          status: (sowData.status || 'active').toLowerCase() as any,
          scope_summary: sowData.payment_terms || '',
          deliverables: [],
        },
        financial: {
          total_contract_value: parseCurrency(sowData.contract_value),
          total_billed: parseCurrency(financialData.total_billed),
          outstanding: parseCurrency(financialData.outstanding),
          burn_rate: parseCurrency(financialData.monthly_retainer || financialData.burn_rate),
          budget_remaining: parseCurrency(financialData.budget_remaining),
          currency: 'USD',
        },
        invoices: (Array.isArray(invoicesArray) ? invoicesArray : []).map((inv: any, idx: number) => ({
          id: idx.toString(),
          invoice_id: inv.invoice_number || '',
          amount: inv.amount || 0,
          date: inv.due_date || '',
          due_date: inv.due_date || '',
          status: (inv.status || 'pending').toLowerCase() as any,
        })),
        renewals: (Array.isArray(renewalsArray) ? renewalsArray : []).map((r: any, idx: number) => ({
          id: idx.toString(),
          contract_name: r.status || 'Contract Renewal',
          renewal_date: r.renewal_date || '',
          current_value: parseCurrency(r.proposed_value),
          status: 'upcoming' as const,
        })),
        revenue_channels: (Array.isArray(revenueArray) ? revenueArray : []).map((rc: any) => ({
          channel: rc.channel || '',
          amount: 0,
          percentage: rc.percentage || 0,
        })),
      };

      return { success: true, data: commercialData };
    } catch (error: any) {
      console.error('Get commercial error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch commercial data',
      };
    }
  },

  getSOW: async (clientId: string, projectId: string): Promise<ApiResponse<CommercialData['sow']>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/commercial/${clientId}/${projectId}/sow`);
      const data = extractValue(response.data);
      return {
        success: true,
        data: {
          sow_id: data?.sow_id || '',
          title: 'Statement of Work',
          value: data?.contract_value || 0,
          currency: 'USD',
          start_date: data?.start_date || '',
          end_date: data?.end_date || '',
          status: (data?.status || 'active').toLowerCase() as any,
          scope_summary: '',
          deliverables: [],
        },
      };
    } catch (error: any) {
      console.error('Get SOW error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch SOW' };
    }
  },

  updateSOW: async (clientId: string, projectId: string, sow: Partial<CommercialData['sow']>): Promise<ApiResponse<void>> => {
    try {
      await apiClient.put(`${API_VERSION}/commercial/${clientId}/${projectId}/sow`, {
        value: sow,
      });
      return { success: true };
    } catch (error: any) {
      console.error('Update SOW error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to update SOW' };
    }
  },

  getFinancial: async (clientId: string, projectId: string): Promise<ApiResponse<CommercialData['financial']>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/commercial/${clientId}/${projectId}/financial`);
      const data = extractValue(response.data);
      return {
        success: true,
        data: {
          total_contract_value: data?.total_contract_value || 0,
          total_billed: data?.total_billed || 0,
          outstanding: data?.outstanding || 0,
          burn_rate: data?.burn_rate || 0,
          budget_remaining: data?.budget_remaining || 0,
          currency: 'USD',
        },
      };
    } catch (error: any) {
      console.error('Get financial error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch financial data' };
    }
  },

  updateFinancial: async (clientId: string, projectId: string, financial: Partial<CommercialData['financial']>): Promise<ApiResponse<void>> => {
    try {
      await apiClient.put(`${API_VERSION}/commercial/${clientId}/${projectId}/financial`, {
        value: financial,
      });
      return { success: true };
    } catch (error: any) {
      console.error('Update financial error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to update financial data' };
    }
  },

  getInvoices: async (clientId: string, projectId: string): Promise<ApiResponse<Invoice[]>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/commercial/${clientId}/${projectId}/invoices`);
      const data = extractValue(response.data) || [];
      const invoices = Array.isArray(data) ? data.map((inv: any, idx: number) => ({
        id: idx.toString(),
        invoice_id: inv.value?.invoice_number || inv.invoice_number || '',
        amount: inv.value?.amount || inv.amount || 0,
        date: inv.value?.due_date || inv.due_date || '',
        due_date: inv.value?.due_date || inv.due_date || '',
        status: (inv.value?.status || inv.status || 'pending').toLowerCase() as any,
      })) : [];
      return { success: true, data: invoices };
    } catch (error: any) {
      console.error('Get invoices error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch invoices' };
    }
  },

  addInvoice: async (clientId: string, projectId: string, invoice: Omit<Invoice, 'id'>): Promise<ApiResponse<Invoice>> => {
    try {
      await apiClient.post(`${API_VERSION}/commercial/${clientId}/${projectId}/invoices`, invoice);
      return { success: true, data: { ...invoice, id: Date.now().toString() } };
    } catch (error: any) {
      console.error('Add invoice error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to add invoice' };
    }
  },

  getRenewals: async (clientId: string, projectId: string): Promise<ApiResponse<Renewal[]>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/commercial/${clientId}/${projectId}/renewals`);
      const data = extractValue(response.data) || [];
      const renewals = Array.isArray(data) ? data.map((r: any, idx: number) => ({
        id: idx.toString(),
        contract_name: r.value || r || '',
        renewal_date: '',
        current_value: 0,
        status: 'upcoming' as const,
      })) : [];
      return { success: true, data: renewals };
    } catch (error: any) {
      console.error('Get renewals error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch renewals' };
    }
  },

  addRenewal: async (clientId: string, projectId: string, renewal: Omit<Renewal, 'id'>): Promise<ApiResponse<Renewal>> => {
    try {
      await apiClient.post(`${API_VERSION}/commercial/${clientId}/${projectId}/renewals`, {
        value: renewal.contract_name,
      });
      return { success: true, data: { ...renewal, id: Date.now().toString() } };
    } catch (error: any) {
      console.error('Add renewal error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to add renewal' };
    }
  },
};

// Strategy API - Real backend calls
export const strategyApi = {
  get: async (clientId: string, projectId: string): Promise<ApiResponse<StrategyData>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/strategy/${clientId}/${projectId}`);
      const data = response.data.data || response.data;

      // Extract arrays from nested value structures
      const stakeholdersArray = extractValue(data.stakeholder_map) || [];
      const goalsArray = extractValue(data.goals_roadmap) || [];
      const upsellsArray = extractValue(data.upsell_opportunities) || [];
      const competitorsArray = extractValue(data.competitors) || [];
      const ecosystemArray = extractValue(data.ecosystem) || [];

      const strategyData: StrategyData = {
        stakeholders: (Array.isArray(stakeholdersArray) ? stakeholdersArray : []).map((s: any, idx: number) => ({
          id: idx.toString(),
          name: s.name || '',
          role: s.role || '',
          influence: (s.influence || s.influence_level || 'medium').toLowerCase() as any,
          alignment: ['champion', 'advocate'].includes((s.sentiment || 'neutral').toLowerCase()) ? 'advocate' :
            ['blocker', 'skeptical'].includes((s.sentiment || 'neutral').toLowerCase()) ? 'skeptical' : 'neutral' as any,
          notes: s.notes || '',
        })),
        roadmap: (Array.isArray(goalsArray) ? goalsArray : []).map((g: any, idx: number) => ({
          id: idx.toString(),
          title: g.goal || g.value || g || '',
          description: '',
          quarter: g.timeline || 'Q1',
          status: ((g.status || 'planned').toLowerCase()) as 'completed' | 'in_progress' | 'planned',
          priority: ((g.priority || 'medium').toLowerCase()) as 'high' | 'medium' | 'low',
        })),
        upsell_opportunities: (Array.isArray(upsellsArray) ? upsellsArray : []).map((u: any) => ({
          service_category: u.service_category || 'Cloud',
          title: u.title || u.opportunity || '',
          description: u.description || '',
          pitch: u.pitch || '',
          potential_value: (u.potential_value || 'Medium') as any,
          rationale: u.rationale || '',
        })),
        competitive_landscape: (Array.isArray(competitorsArray) ? competitorsArray : []).map((c: any, idx: number) => ({
          id: idx.toString(),
          name: c.name || c.value || c || '',
          strengths: c.strength ? [c.strength] : [],
          weaknesses: c.weakness ? [c.weakness] : [],
        })),
        ecosystem: (Array.isArray(ecosystemArray) ? ecosystemArray : []).map((e: any) => ({
          platform: e.platform || '',
          purpose: e.purpose || '',
        })),
      };

      return { success: true, data: strategyData };
    } catch (error: any) {
      console.error('Get strategy error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch strategy data',
      };
    }
  },

  getStakeholders: async (clientId: string, projectId: string): Promise<ApiResponse<StrategyData['stakeholders']>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/strategy/${clientId}/${projectId}/stakeholders`);
      // Response format: {"field": "stakeholder_map", "data": {"value": [...]}}
      const rawData = response.data.data?.value || response.data.data || extractValue(response.data) || [];
      const stakeholders = (Array.isArray(rawData) ? rawData : []).map((s: any, idx: number) => ({
        id: idx.toString(),
        name: s.name || '',
        role: s.role || '',
        influence: (s.influence || s.influence_level || 'medium').toLowerCase() as any,
        alignment: (s.sentiment || 'neutral').toLowerCase() === 'champion' ? 'advocate' :
          (s.sentiment || 'neutral').toLowerCase() === 'blocker' ? 'skeptical' : 'neutral' as any,
        notes: s.notes || '',
      }));
      return { success: true, data: stakeholders };
    } catch (error: any) {
      console.error('Get stakeholders error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch stakeholders' };
    }
  },

  getRoadmap: async (clientId: string, projectId: string): Promise<ApiResponse<StrategyData['roadmap']>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/strategy/${clientId}/${projectId}/goals`);
      // Response format: {"field": "goals_roadmap", "data": {"value": [...]}}
      const rawData = response.data.data?.value || response.data.data || extractValue(response.data) || [];
      const roadmap = (Array.isArray(rawData) ? rawData : []).map((g: any, idx: number) => ({
        id: idx.toString(),
        title: g.goal || g.value || g || '',
        description: '',
        quarter: g.timeline || 'Q1',
        status: ((g.status || 'planned').toLowerCase()) as 'completed' | 'in_progress' | 'planned',
        priority: ((g.priority || 'medium').toLowerCase()) as 'high' | 'medium' | 'low',
      }));
      return { success: true, data: roadmap };
    } catch (error: any) {
      console.error('Get roadmap error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch roadmap' };
    }
  },



  getCompetitors: async (clientId: string, projectId: string): Promise<ApiResponse<StrategyData['competitive_landscape']>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/strategy/${clientId}/${projectId}/competitors`);
      const data = extractValue(response.data) || [];
      const competitors = Array.isArray(data) ? data.map((c: any, idx: number) => ({
        id: idx.toString(),
        name: c.value || c || '',
        strengths: [],
        weaknesses: [],
      })) : [];
      return { success: true, data: competitors };
    } catch (error: any) {
      console.error('Get competitors error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch competitors' };
    }
  },

  addStakeholder: async (clientId: string, projectId: string, stakeholder: { name: string; role: string; influence: string; alignment: string; notes?: string }): Promise<ApiResponse<void>> => {
    try {
      // Map frontend alignment to backend sentiment
      const sentimentMap: Record<string, string> = {
        'advocate': 'Champion',
        'neutral': 'Neutral',
        'skeptical': 'Blocker',
      };
      await apiClient.post(`${API_VERSION}/strategy/${clientId}/${projectId}/stakeholders`, {
        name: stakeholder.name,
        role: stakeholder.role,
        influence: stakeholder.influence.charAt(0).toUpperCase() + stakeholder.influence.slice(1),
        sentiment: sentimentMap[stakeholder.alignment] || 'Neutral',
        notes: stakeholder.notes || '',
      });
      return { success: true };
    } catch (error: any) {
      console.error('Add stakeholder error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to add stakeholder' };
    }
  },

  addRoadmapItem: async (clientId: string, projectId: string, item: { title: string; description: string; quarter: string; status: string; priority: string }): Promise<ApiResponse<void>> => {
    try {
      await apiClient.post(`${API_VERSION}/strategy/${clientId}/${projectId}/goals`, {
        goal: item.title,
        timeline: item.quarter,
        priority: item.priority.charAt(0).toUpperCase() + item.priority.slice(1),
        status: item.status,
      });
      return { success: true };
    } catch (error: any) {
      console.error('Add roadmap item error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to add roadmap item' };
    }
  },

  updateStakeholders: async (clientId: string, projectId: string, stakeholders: { name: string; role: string; influence: string; alignment: string; notes?: string }[]): Promise<ApiResponse<void>> => {
    try {
      const sentimentMap: Record<string, string> = {
        'advocate': 'Champion',
        'neutral': 'Neutral',
        'skeptical': 'Blocker',
      };
      const payload = stakeholders.map(s => ({
        name: s.name,
        role: s.role,
        influence: s.influence.charAt(0).toUpperCase() + s.influence.slice(1),
        sentiment: sentimentMap[s.alignment] || 'Neutral',
        notes: s.notes || '',
      }));
      await apiClient.put(`${API_VERSION}/strategy/${clientId}/${projectId}/stakeholders`, payload);
      return { success: true };
    } catch (error: any) {
      console.error('Update stakeholders error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to update stakeholders' };
    }
  },

  updateRoadmapItems: async (clientId: string, projectId: string, items: { title: string; description: string; quarter: string; status: string; priority: string }[]): Promise<ApiResponse<void>> => {
    try {
      const payload = items.map(item => ({
        goal: item.title,
        timeline: item.quarter,
        priority: item.priority.charAt(0).toUpperCase() + item.priority.slice(1),
        status: item.status,
      }));
      await apiClient.put(`${API_VERSION}/strategy/${clientId}/${projectId}/goals`, payload);
      return { success: true };
    } catch (error: any) {
      console.error('Update roadmap items error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to update roadmap items' };
    }
  },

  addEcosystemItem: async (clientId: string, projectId: string, item: { platform: string; purpose: string }): Promise<ApiResponse<void>> => {
    try {
      // Get current ecosystem items first
      const response = await apiClient.get(`${API_VERSION}/strategy/${clientId}/${projectId}/ecosystem`);
      const currentData = response.data.data?.value || response.data.data || [];
      const currentItems = Array.isArray(currentData) ? currentData : [];
      
      // Add new item and update
      const payload = [...currentItems, item];
      await apiClient.put(`${API_VERSION}/strategy/${clientId}/${projectId}/ecosystem`, payload);
      return { success: true };
    } catch (error: any) {
      console.error('Add ecosystem item error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to add ecosystem item' };
    }
  },

  updateEcosystemItems: async (clientId: string, projectId: string, items: { platform: string; purpose: string }[]): Promise<ApiResponse<void>> => {
    try {
      await apiClient.put(`${API_VERSION}/strategy/${clientId}/${projectId}/ecosystem`, items);
      return { success: true };
    } catch (error: any) {
      console.error('Update ecosystem items error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to update ecosystem items' };
    }
  },
};

// Intelligence API
export const intelligenceApi = {
  getUpsell: async (projectId: string): Promise<ApiResponse<any[]>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/intelligence/upsell/${projectId}`);
      return { success: true, data: response.data.data || response.data };
    } catch (error: any) {
      console.error('Get upsell error:', error);
      return { success: false, error: error.response?.data?.detail };
    }
  },

  getRisk: async (projectId: string): Promise<ApiResponse<any>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/intelligence/risk/${projectId}`);
      const data = response.data.data || response.data;
      return { success: true, data };
    } catch (error: any) {
      console.error('Get risk error:', error);
      return { success: false, error: error.response?.data?.detail };
    }
  },

  getKnowledge: async (projectId: string): Promise<ApiResponse<any[]>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/intelligence/knowledge/${projectId}/matches`);
      const data = response.data.data || response.data.similar_projects || response.data;
      return { success: true, data: Array.isArray(data) ? data : [] };
    } catch (error: any) {
      console.error('Get knowledge error:', error);
      return { success: false, error: error.response?.data?.detail };
    }
  },
};

// Helper for persistent random health score (80-90)
export const getProjectHealth = (projectId: string): number => {
  const storageKey = `health_score_${projectId}`;
  const stored = localStorage.getItem(storageKey);

  if (stored) {
    return parseInt(stored, 10);
  }

  // Generate random between 80 and 90
  const score = Math.floor(Math.random() * (90 - 80 + 1)) + 80;
  localStorage.setItem(storageKey, score.toString());
  return score;
};

// Chat API
export const chatApi = {
  sendMessage: async (message: string, clientId?: string, projectId?: string): Promise<ApiResponse<any>> => {
    try {
      const response = await apiClient.post(`${API_VERSION}/chat/ask`, {
        message,
        client_id: clientId,
        project_id: projectId
      });
      return { success: true, data: response.data };
    } catch (error: any) {
      console.error('Chat error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to send message' };
    }
  }
};

// Marketing API - Real backend calls
export const marketingApi = {
  get: async (clientId: string, projectId: string): Promise<ApiResponse<MarketingData>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/marketing/${clientId}/${projectId}`);
      const data = response.data.data || response.data;

      // Extract arrays using helper
      const successStoriesArray = extractValue(data.success_stories) || [];
      const testimonialsArray = extractValue(data.testimonials) || [];
      const referencesArray = extractValue(data.public_references) || [];
      const brandData = extractValue(data.brand_guidelines) || {};

      const marketingData: MarketingData = {
        brand_guidelines: {
          logo_url: brandData.logo_url || '',
          brand_colors: brandData.brand_colors || [],
          tone_of_voice: brandData.tone_of_voice || '',
          messaging_guidelines: brandData.messaging_guidelines || '',
          approved_assets: brandData.approved_assets || [],
        },
        success_stories: (Array.isArray(successStoriesArray) ? successStoriesArray : []).map((s: any, idx: number) => ({
          id: idx.toString(),
          title: s.title || s.value || s || '',
          description: s.description || '',
          metrics: s.metrics || {},
          case_study_eligible: s.case_study_eligible || false,
          approval_status: 'pending' as const,
        })),
        testimonials: (Array.isArray(testimonialsArray) ? testimonialsArray : []).map((t: any, idx: number) => ({
          id: idx.toString(),
          quote: t.quote || t.value || t || '',
          author: t.author || t.from_person || '',
          role: t.role || '',
          date: t.date || new Date().toISOString(),
          approval_status: 'pending' as const,
        })),
        public_references: (Array.isArray(referencesArray) ? referencesArray : []).map((r: any, idx: number) => ({
          id: idx.toString(),
          type: r.type || 'blog_post' as const,
          title: r.title || r.value || r || '',
          url: r.url || '',
          date: r.date || new Date().toISOString(),
          status: 'published' as const,
        })),
      };

      return { success: true, data: marketingData };
    } catch (error: any) {
      console.error('Get marketing error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch marketing data',
      };
    }
  },

  addTestimonial: async (clientId: string, projectId: string, testimonial: { from_person: string; quote: string }): Promise<ApiResponse<void>> => {
    try {
      // Get existing testimonials first
      const current = await apiClient.get(`${API_VERSION}/marketing/${clientId}/${projectId}/testimonials`);
      const existingList = current.data?.data?.value || [];
      const updatedList = [...existingList, testimonial];
      await apiClient.put(`${API_VERSION}/marketing/${clientId}/${projectId}/testimonials`, updatedList);
      return { success: true };
    } catch (error: any) {
      console.error('Add testimonial error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to add testimonial' };
    }
  },

  addSuccessStory: async (clientId: string, projectId: string, story: { title: string; description?: string }): Promise<ApiResponse<void>> => {
    try {
      // Get existing stories first
      const current = await apiClient.get(`${API_VERSION}/marketing/${clientId}/${projectId}/success_stories`);
      const existingList = current.data?.data?.value || [];
      const updatedList = [...existingList, story];
      await apiClient.put(`${API_VERSION}/marketing/${clientId}/${projectId}/success_stories`, updatedList);
      return { success: true };
    } catch (error: any) {
      console.error('Add success story error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to add success story' };
    }
  },

  addPublicReference: async (clientId: string, projectId: string, reference: { type: string; title: string; url?: string }): Promise<ApiResponse<void>> => {
    try {
      // Get existing references first
      const current = await apiClient.get(`${API_VERSION}/marketing/${clientId}/${projectId}/references`);
      const existingList = current.data?.data?.value || [];
      const updatedList = [...existingList, reference];
      await apiClient.put(`${API_VERSION}/marketing/${clientId}/${projectId}/references`, updatedList);
      return { success: true };
    } catch (error: any) {
      console.error('Add public reference error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to add public reference' };
    }
  },
};

// Automation/Ingestion API
export const automationApi = {
  triggerExtraction: async (clientId: string, projectId: string): Promise<ApiResponse<void>> => {
    try {
      await apiClient.post(`${API_VERSION}/automation/extract`, { client_id: clientId, project_id: projectId });
      return { success: true };
    } catch (error: any) {
      console.error('Trigger extraction error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to trigger extraction' };
    }
  },

  syncBasecamp: async (projectId: string): Promise<ApiResponse<void>> => {
    try {
      await apiClient.post(`${API_VERSION}/automation/basecamp/sync/${projectId}`);
      return { success: true };
    } catch (error: any) {
      console.error('Sync basecamp error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to sync Basecamp' };
    }
  },
};

// Reports API
export const reportsApi = {
  generate: async (projectId: string): Promise<ApiResponse<string>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/reports/projects/${projectId}`, {
        responseType: 'text',
      });
      return { success: true, data: response.data };
    } catch (error: any) {
      console.error('Generate report error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to generate report' };
    }
  },
};
// Other API
export const otherApi = {
  get: async (clientId: string, projectId: string): Promise<ApiResponse<any>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/other/${clientId}/${projectId}`);
      return { success: true, data: response.data.data };
    } catch (error: any) {
      console.error('Get other data error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch experimental data' };
    }
  },

  addNote: async (clientId: string, projectId: string, note: { title: string; content: string }): Promise<ApiResponse<void>> => {
    try {
      await apiClient.post(`${API_VERSION}/other/${clientId}/${projectId}/notes`, note);
      return { success: true };
    } catch (error: any) {
      console.error('Add experimental note error:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to add note' };
    }
  },
};

// Sections API (General CRUD for any section)
export const sectionsApi = {
  get: async (clientId: string, projectId: string, section: string): Promise<ApiResponse<any>> => {
    try {
      const response = await apiClient.get(`${API_VERSION}/sections/${clientId}/${projectId}/${section}`);
      return { success: true, data: response.data.data };
    } catch (error: any) {
      console.error(`Get section ${section} error:`, error);
      return { success: false, error: error.response?.data?.detail || `Failed to fetch ${section}` };
    }
  },

  update: async (clientId: string, projectId: string, section: string, data: any): Promise<ApiResponse<void>> => {
    try {
      await apiClient.put(`${API_VERSION}/sections/${clientId}/${projectId}/${section}`, data);
      return { success: true };
    } catch (error: any) {
      console.error(`Update section ${section} error:`, error);
      return { success: false, error: error.response?.data?.detail || `Failed to update ${section}` };
    }
  },
};
