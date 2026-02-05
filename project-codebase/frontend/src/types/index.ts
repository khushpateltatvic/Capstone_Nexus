// Nexus Dashboard Types

// Backend role hierarchy
export type UserRole = 'trainee' | 'analyst' | 'lead' | 'head' | 'admin' | 'director' | 'tech' | 'pm' | 'strategy' | 'marketing' | 'viewer' | 'management';

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  job_title?: string;
  avatar?: string;
  department?: string;
}

export interface Project {
  id: string;
  project_id?: string;
  client_id: string;
  name: string;
  description?: string;
  department: string;
  assigned_users: string[] | number;
  created_at: string;
  updated_at: string;
  health_score: number;
  status: 'active' | 'on_hold' | 'completed' | 'at_risk';
}

export interface Client {
  id: string;
  name: string;
  industry: string;
  logo?: string;
  website?: string;
  health_score: number;
  projects: Project[];
}

// Section Permissions
export type PermissionLevel = 'NONE' | 'VIEW' | 'EDIT' | 'ADMIN' | 'FULL';

export interface SectionPermissions {
  universal: PermissionLevel;
  operations: PermissionLevel;
  technical: PermissionLevel;
  commercial: PermissionLevel;
  strategy: PermissionLevel;
  marketing: PermissionLevel;
}

// Module 1: Universal Context
export interface UniversalContext {
  client_profile: ClientProfile;
  internal_squad: SquadMember[];
  poc_map: POCContact[];
  communication_hygiene: CommunicationHygiene;
  ai_summary: string;
  timeline: TimelineEvent[];
  engagement_type?: string;
  important_notes: string[];
  google_workspace: string[];
}

export interface ClientProfile {
  name: string;
  industry: string;
  health_score: number;
  account_tier: 'enterprise' | 'premium' | 'standard';
  contract_start: string;
  contract_end: string;
  account_manager: string;
}

export interface SquadMember {
  id: string;
  name: string;
  role: string;
  email: string;
  avatar?: string;
  department: string;
}

export interface POCContact {
  id: string;
  name: string;
  role: string;
  email: string;
  phone?: string;
  is_primary: boolean;
  influence_level: 'high' | 'medium' | 'low';
}

export interface CommunicationHygiene {
  last_meeting: string;
  last_email: string;
  response_time_avg: string;
  meetings_this_month: number;
  emails_this_month: number;
  health_status: 'excellent' | 'good' | 'needs_attention' | 'critical';
}

export interface TimelineEvent {
  id: string;
  date: string;
  event: string;
  significance: 'high' | 'medium' | 'low';
  category: 'milestone' | 'issue' | 'achievement' | 'communication';
}

// Module 2: Operations & Status
export interface OperationsData {
  traffic_light: TrafficLightStatus;
  tasks: TasksData;
  blockers: Blocker[];
  interactions: Interaction[];
  engagement_status?: string;
}

export interface TrafficLightStatus {
  status: 'red' | 'yellow' | 'green';
  reason: string;
  updated_at: string;
  updated_by: string;
}

export interface TasksData {
  upcoming: Task[];
  ongoing: Task[];
  completed: Task[];
}

export interface Task {
  id: string;
  title: string;
  description?: string;
  assignee?: string;
  due_date?: string;
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'in_progress' | 'completed';
  created_at: string;
}

export interface Blocker {
  id: string;
  description: string;
  severity: 'high' | 'medium' | 'low';
  reported_by: string;
  reported_at: string;
  resolved_at?: string;
  status: 'active' | 'resolved';
}

export interface Interaction {
  id: string;
  date: string;
  type: 'meeting' | 'email' | 'call' | 'chat';
  summary: string;
  participants: string[];
  recording_url?: string;
}

// Module 3: Technical Details
export interface TechnicalData {
  tech_stack: TechStackItem[];
  credentials: Credential[];
  implementations: Implementation[];
  experiments: Experiment[];
}

export interface TechStackItem {
  id: string;
  technology: string;
  category: string;
  version?: string;
  status: 'active' | 'planned' | 'deprecated';
  notes?: string;
}

export interface Credential {
  id: string;
  system: string;
  url?: string;
  username?: string;
  status: 'active' | 'expired' | 'pending';
  last_verified?: string;
  notes?: string;
}

export interface Implementation {
  id: string;
  title: string;
  description: string;
  date: string;
  implemented_by: string;
  category: string;
  impact?: string;
}

export interface Experiment {
  id: string;
  name: string;
  hypothesis: string;
  status: 'planned' | 'running' | 'completed' | 'cancelled';
  start_date?: string;
  end_date?: string;
  results?: string;
  winner?: string;
}

// Module 4: Commercial & Legal
export interface CommercialData {
  sow: SOWData;
  financial: FinancialData;
  invoices: Invoice[];
  renewals: Renewal[];
  revenue_channels: RevenueChannel[];
}

export interface SOWData {
  sow_id: string;
  title: string;
  value: number;
  currency: string;
  start_date: string;
  end_date: string;
  status: 'draft' | 'signed' | 'amendment' | 'expired';
  scope_summary: string;
  deliverables: string[];
}

export interface FinancialData {
  total_contract_value: number;
  total_billed: number;
  outstanding: number;
  burn_rate: number;
  budget_remaining: number;
  currency: string;
}

export interface Invoice {
  id: string;
  invoice_id: string;
  amount: number;
  date: string;
  due_date: string;
  status: 'pending' | 'paid' | 'overdue';
  description?: string;
}

export interface Renewal {
  id: string;
  contract_name: string;
  renewal_date: string;
  current_value: number;
  proposed_value?: number;
  status: 'upcoming' | 'in_negotiation' | 'signed' | 'at_risk';
  notes?: string;
}

export interface RevenueChannel {
  channel: string;
  amount: number;
  percentage: number;
}

// Module 5: Strategy
export interface StrategyData {
  stakeholders: Stakeholder[];
  roadmap: RoadmapItem[];
  upsell_opportunities: any[];
  competitive_landscape: Competitor[];
  ecosystem?: EcosystemItem[];
}

export interface EcosystemItem {
  platform: string;
  purpose: string;
}

export interface Stakeholder {
  id: string;
  name: string;
  role: string;
  influence: 'high' | 'medium' | 'low';
  alignment: 'advocate' | 'neutral' | 'skeptical';
  notes?: string;
}

export interface RoadmapItem {
  id: string;
  title: string;
  description: string;
  quarter: string;
  status: 'planned' | 'in_progress' | 'completed';
  priority: 'high' | 'medium' | 'low';
}



export interface Competitor {
  id: string;
  name: string;
  strengths: string[];
  weaknesses: string[];
  our_advantage?: string;
}

// Module 6: Marketing
export interface MarketingData {
  brand_guidelines: BrandGuidelines;
  success_stories: SuccessStory[];
  testimonials: Testimonial[];
  public_references: PublicReference[];
}

export interface BrandGuidelines {
  logo_url?: string;
  brand_colors: string[];
  tone_of_voice: string;
  messaging_guidelines: string;
  approved_assets: string[];
}

export interface SuccessStory {
  id: string;
  title: string;
  description: string;
  metrics: Record<string, string>;
  case_study_eligible: boolean;
  approval_status: 'pending' | 'approved' | 'published';
}

export interface Testimonial {
  id: string;
  quote: string;
  author: string;
  role: string;
  date: string;
  approval_status: 'pending' | 'approved' | 'published';
}

export interface PublicReference {
  id: string;
  type: 'press_release' | 'blog_post' | 'social_media' | 'event';
  title: string;
  url?: string;
  date: string;
  status: 'planned' | 'published';
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// Dashboard State
export interface DashboardState {
  selectedClient: Client | null;
  selectedProject: Project | null;
  expandedModules: string[];
  sidebarCollapsed: boolean;
}
// Intelligence Types
export interface RiskAnalysis {
  risk_level: 'Low' | 'Medium' | 'High' | 'Critical';
  sentiment?: 'Positive' | 'Neutral' | 'Negative';
  summary: string;
  indicators: string[];
  recommendations: string[];
  last_updated?: string;
}

export interface KnowledgeMatch {
  title: string;
  project_name: string;
  relevance_score: number;
  summary: string;
  key_learnings: string[];
}

export interface UpsellOpportunity {
  id: string;
  service_category: string;
  title: string;
  description: string;
  pitch: string;
  potential_value: 'High' | 'Medium' | 'Low';
  rationale: string;
}

export interface RiskItem {
  id: string;
  risk_level: 'High' | 'Medium' | 'Low' | 'Critical';
  sentiment?: 'Positive' | 'Neutral' | 'Negative';
  summary: string;
  indicators: string[];
  recommendations: string[];
  last_updated?: string;
}

export interface KnowledgeItem {
  id: string;
  title: string;
  project_name: string;
  relevance_score: number;
  summary: string;
  key_learnings: string[];
}
