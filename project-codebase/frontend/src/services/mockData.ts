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

// Mock Current User
export const currentUser: User = {
  id: '1',
  email: 'admin@tatvic.com',
  name: 'Alex Morgan',
  role: 'admin',
  avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Alex',
  department: 'Management',
};

// Mock Users
export const users: User[] = [
  currentUser,
  {
    id: '2',
    email: 'tech@tatvic.com',
    name: 'Sarah Chen',
    role: 'lead',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah',
    department: 'Engineering',
  },
  {
    id: '3',
    email: 'pm@tatvic.com',
    name: 'Mike Johnson',
    role: 'lead',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Mike',
    department: 'Project Management',
  },
  {
    id: '4',
    email: 'strategy@tatvic.com',
    name: 'Emily Davis',
    role: 'analyst',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Emily',
    department: 'Strategy',
  },
  {
    id: '5',
    email: 'marketing@tatvic.com',
    name: 'Raj Patel',
    role: 'analyst',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Raj',
    department: 'Marketing',
  },
];

// Mock Clients
export const clients: Client[] = [
  {
    id: 'icici-lombard',
    name: 'ICICI Lombard',
    industry: 'Insurance',
    health_score: 92,
    logo: 'https://ui-avatars.com/api/?name=ICICI&background=321a75&color=fff',
    website: 'https://www.icicilombard.com',
    projects: [],
  },
  {
    id: 'flipkart',
    name: 'Flipkart',
    industry: 'E-commerce',
    health_score: 88,
    logo: 'https://ui-avatars.com/api/?name=Flipkart&background=faab00&color=fff',
    website: 'https://www.flipkart.com',
    projects: [],
  },
  {
    id: 'airtel',
    name: 'Airtel',
    industry: 'Telecommunications',
    health_score: 85,
    logo: 'https://ui-avatars.com/api/?name=Airtel&background=ef4444&color=fff',
    website: 'https://www.airtel.in',
    projects: [],
  },
  {
    id: 'tatvic-internal',
    name: 'Tatvic Internal',
    industry: 'Technology',
    health_score: 95,
    logo: 'https://ui-avatars.com/api/?name=Tatvic&background=00c3c4&color=fff',
    website: 'https://www.tatvic.com',
    projects: [],
  },
];

// Mock Projects
export const projects: Project[] = [
  {
    id: '41106708',
    client_id: 'icici-lombard',
    name: 'GA4 Migration & Analytics',
    description: 'Complete migration from Universal Analytics to GA4 with enhanced ecommerce tracking',
    department: 'Data Engineering',
    assigned_users: ['1', '2', '3'],
    created_at: '2023-06-15T00:00:00Z',
    updated_at: '2024-01-28T00:00:00Z',
    health_score: 94,
    status: 'active',
  },
  {
    id: '41106709',
    client_id: 'icici-lombard',
    name: 'Conversion Rate Optimization',
    description: 'A/B testing and personalization program for insurance funnel optimization',
    department: 'Strategy',
    assigned_users: ['1', '4'],
    created_at: '2023-08-01T00:00:00Z',
    updated_at: '2024-01-25T00:00:00Z',
    health_score: 89,
    status: 'active',
  },
  {
    id: '52207801',
    client_id: 'flipkart',
    name: 'BigQuery Data Warehouse',
    description: 'Enterprise data warehouse implementation with real-time analytics',
    department: 'Data Engineering',
    assigned_users: ['2', '3'],
    created_at: '2023-09-10T00:00:00Z',
    updated_at: '2024-01-30T00:00:00Z',
    health_score: 91,
    status: 'active',
  },
  {
    id: '63308901',
    client_id: 'airtel',
    name: 'Customer Journey Analytics',
    description: 'Cross-channel customer journey mapping and attribution modeling',
    department: 'Analytics',
    assigned_users: ['1', '4', '5'],
    created_at: '2023-11-20T00:00:00Z',
    updated_at: '2024-01-29T00:00:00Z',
    health_score: 87,
    status: 'active',
  },
];

// Link projects to clients
clients.forEach(client => {
  client.projects = projects.filter(p => p.client_id === client.id);
});

// Mock Universal Context Data
export const mockUniversalContext: UniversalContext = {
  client_profile: {
    name: 'ICICI Lombard',
    industry: 'Insurance',
    health_score: 92,
    account_tier: 'enterprise',
    contract_start: '2023-01-01',
    contract_end: '2025-12-31',
    account_manager: 'Alex Morgan',
  },
  internal_squad: [
    {
      id: '1',
      name: 'Alex Morgan',
      role: 'Account Director',
      email: 'alex@tatvic.com',
      avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Alex',
      department: 'Management',
    },
    {
      id: '2',
      name: 'Sarah Chen',
      role: 'Lead Data Engineer',
      email: 'sarah@tatvic.com',
      avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah',
      department: 'Engineering',
    },
    {
      id: '3',
      name: 'Mike Johnson',
      role: 'Project Manager',
      email: 'mike@tatvic.com',
      avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Mike',
      department: 'Project Management',
    },
    {
      id: '4',
      name: 'Emily Davis',
      role: 'Strategy Consultant',
      email: 'emily@tatvic.com',
      avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Emily',
      department: 'Strategy',
    },
  ],
  poc_map: [
    {
      id: '1',
      name: 'Rajesh Kumar',
      role: 'VP Digital Transformation',
      email: 'rajesh.kumar@icicilombard.com',
      phone: '+91 98765 43210',
      is_primary: true,
      influence_level: 'high',
    },
    {
      id: '2',
      name: 'Priya Sharma',
      role: 'Head of Marketing Analytics',
      email: 'priya.sharma@icicilombard.com',
      phone: '+91 98765 43211',
      is_primary: false,
      influence_level: 'high',
    },
    {
      id: '3',
      name: 'Amit Patel',
      role: 'IT Director',
      email: 'amit.patel@icicilombard.com',
      is_primary: false,
      influence_level: 'medium',
    },
  ],
  communication_hygiene: {
    last_meeting: '2024-01-28',
    last_email: '2024-01-30',
    response_time_avg: '4 hours',
    meetings_this_month: 8,
    emails_this_month: 47,
    health_status: 'excellent',
  },
  ai_summary: 'ICICI Lombard project is progressing excellently. GA4 migration completed ahead of schedule. Current focus on CRO program with 3 active experiments. Strong stakeholder alignment with Rajesh Kumar advocating for expansion. Renewal discussion scheduled for Q2.',
  important_notes: [
    'Contract renewal discussion scheduled for Q2 2024',
    'Client requested additional GA4 training sessions',
    'Budget increase approved for CRO experiments',
  ],
  google_workspace: [
    'https://drive.google.com/client-folder',
    'https://docs.google.com/project-charter',
    'https://calendar.google.com/weekly-sync',
  ],
  timeline: [
    {
      id: '1',
      date: '2024-01-15',
      event: 'GA4 Migration Completed',
      significance: 'high',
      category: 'milestone',
    },
    {
      id: '2',
      date: '2024-01-20',
      event: 'First CRO Experiment Launched',
      significance: 'medium',
      category: 'milestone',
    },
    {
      id: '3',
      date: '2024-01-25',
      event: 'Quarterly Business Review',
      significance: 'high',
      category: 'communication',
    },
    {
      id: '4',
      date: '2024-01-28',
      event: 'Technical Architecture Review',
      significance: 'medium',
      category: 'communication',
    },
  ],
};

// Mock Operations Data
export const mockOperationsData: OperationsData = {
  traffic_light: {
    status: 'green',
    reason: 'All deliverables on track. No blockers identified.',
    updated_at: '2024-01-30T10:00:00Z',
    updated_by: 'Mike Johnson',
  },
  tasks: {
    upcoming: [
      {
        id: '1',
        title: 'Sprint Planning - Feb 2024',
        description: 'Plan sprints for February including CRO experiments',
        assignee: 'Mike Johnson',
        due_date: '2024-02-05',
        priority: 'high',
        status: 'pending',
        created_at: '2024-01-28T00:00:00Z',
      },
      {
        id: '2',
        title: 'Monthly Performance Report',
        description: 'Prepare analytics performance report for January',
        assignee: 'Sarah Chen',
        due_date: '2024-02-02',
        priority: 'medium',
        status: 'pending',
        created_at: '2024-01-29T00:00:00Z',
      },
    ],
    ongoing: [
      {
        id: '3',
        title: 'Checkout Funnel A/B Test',
        description: 'Testing simplified checkout flow vs current',
        assignee: 'Emily Davis',
        due_date: '2024-02-10',
        priority: 'high',
        status: 'in_progress',
        created_at: '2024-01-20T00:00:00Z',
      },
      {
        id: '4',
        title: 'BigQuery Data Pipeline Optimization',
        description: 'Optimize ETL pipelines for faster reporting',
        assignee: 'Sarah Chen',
        due_date: '2024-02-08',
        priority: 'medium',
        status: 'in_progress',
        created_at: '2024-01-22T00:00:00Z',
      },
    ],
    completed: [
      {
        id: '5',
        title: 'GA4 Migration',
        description: 'Complete migration from UA to GA4',
        assignee: 'Sarah Chen',
        due_date: '2024-01-15',
        priority: 'high',
        status: 'completed',
        created_at: '2023-12-01T00:00:00Z',
      },
    ],
  },
  blockers: [
    {
      id: '1',
      description: 'Waiting for GTM container access from IT security team',
      severity: 'medium',
      reported_by: 'Sarah Chen',
      reported_at: '2024-01-29T00:00:00Z',
      status: 'active',
    },
  ],
  interactions: [
    {
      id: '1',
      date: '2024-01-28',
      type: 'meeting',
      summary: 'Technical architecture review - discussed BigQuery optimization and upcoming CRO roadmap',
      participants: ['Rajesh Kumar', 'Alex Morgan', 'Sarah Chen'],
    },
    {
      id: '2',
      date: '2024-01-25',
      type: 'meeting',
      summary: 'Quarterly Business Review - reviewed performance metrics and discussed expansion opportunities',
      participants: ['Rajesh Kumar', 'Priya Sharma', 'Alex Morgan', 'Emily Davis'],
    },
    {
      id: '3',
      date: '2024-01-23',
      type: 'email',
      summary: 'Follow-up on GA4 migration completion and next steps',
      participants: ['Priya Sharma', 'Sarah Chen'],
    },
  ],
};

// Mock Technical Data
export const mockTechnicalData: TechnicalData = {
  tech_stack: [
    { id: '1', technology: 'Google Analytics 4', category: 'Analytics', version: 'Latest', status: 'active', notes: 'Primary analytics platform' },
    { id: '2', technology: 'Google Tag Manager', category: 'Tag Management', version: 'Latest', status: 'active', notes: 'Container ID: GTM-XXXXXX' },
    { id: '3', technology: 'BigQuery', category: 'Data Warehouse', version: 'Latest', status: 'active', notes: 'Enterprise data warehouse' },
    { id: '4', technology: 'Looker Studio', category: 'Visualization', version: 'Latest', status: 'active', notes: 'Dashboard and reporting' },
    { id: '5', technology: 'Firebase', category: 'Mobile Analytics', version: 'Latest', status: 'active', notes: 'Mobile app tracking' },
    { id: '6', technology: 'Optimizely', category: 'Experimentation', version: 'Latest', status: 'active', notes: 'A/B testing platform' },
  ],
  credentials: [
    { id: '1', system: 'Google Analytics', url: 'analytics.google.com', username: 'tatvic@icicilombard.com', status: 'active', last_verified: '2024-01-30', notes: 'Admin access granted' },
    { id: '2', system: 'GTM', url: 'tagmanager.google.com', username: 'tatvic@icicilombard.com', status: 'active', last_verified: '2024-01-30', notes: 'Publish rights' },
    { id: '3', system: 'BigQuery', url: 'console.cloud.google.com', username: 'tatvic-service@icici-project.iam', status: 'active', last_verified: '2024-01-28', notes: 'Data viewer + job user' },
    { id: '4', system: 'Optimizely', url: 'app.optimizely.com', username: 'tatvic@icicilombard.com', status: 'pending', last_verified: '2024-01-15', notes: 'Awaiting approval' },
  ],
  implementations: [
    { id: '1', title: 'GA4 Ecommerce Tracking', description: 'Complete ecommerce tracking implementation for insurance products', date: '2024-01-15', implemented_by: 'Sarah Chen', category: 'Analytics', impact: '100% transaction visibility' },
    { id: '2', title: 'Enhanced Conversions', description: 'Google Ads enhanced conversions setup', date: '2024-01-10', implemented_by: 'Sarah Chen', category: 'Advertising', impact: '15% improvement in attribution' },
    { id: '3', title: 'Server-Side GTM', description: 'SSGTM implementation for data quality', date: '2023-12-20', implemented_by: 'Sarah Chen', category: 'Infrastructure', impact: 'Reduced data loss by 8%' },
  ],
  experiments: [
    { id: '1', name: 'Checkout Funnel Simplification', hypothesis: 'Reducing form fields will increase conversion by 10%', status: 'running', start_date: '2024-01-20', end_date: '2024-02-10', results: undefined, winner: undefined },
    { id: '2', name: 'CTA Color Test', hypothesis: 'Orange CTA will outperform blue by 5%', status: 'completed', start_date: '2024-01-05', end_date: '2024-01-19', results: 'Orange outperformed by 7.2%', winner: 'Orange variant' },
    { id: '3', name: 'Homepage Hero Messaging', hypothesis: 'Benefit-focused copy will increase engagement', status: 'planned', start_date: '2024-02-01', end_date: '2024-02-15', results: undefined, winner: undefined },
  ],
};

// Mock Commercial Data
export const mockCommercialData: CommercialData = {
  sow: {
    sow_id: 'SOW-ICICI-2023-001',
    title: 'Analytics & CRO Services 2023-2025',
    value: 450000,
    currency: 'USD',
    start_date: '2023-01-01',
    end_date: '2025-12-31',
    status: 'signed',
    scope_summary: 'Full-service analytics implementation, GA4 migration, CRO program, and ongoing optimization services',
    deliverables: ['GA4 Implementation', 'Monthly Reporting', 'CRO Program', 'Quarterly Business Reviews', 'Technical Support'],
  },
  financial: {
    total_contract_value: 450000,
    total_billed: 287500,
    outstanding: 162500,
    burn_rate: 18750,
    budget_remaining: 162500,
    currency: 'USD',
  },
  invoices: [
    { id: '1', invoice_id: 'INV-2024-001', amount: 18750, date: '2024-01-01', due_date: '2024-01-15', status: 'paid', description: 'January 2024 Services' },
    { id: '2', invoice_id: 'INV-2024-002', amount: 18750, date: '2024-01-31', due_date: '2024-02-14', status: 'paid', description: 'February 2024 Services' },
    { id: '3', invoice_id: 'INV-2024-003', amount: 18750, date: '2024-02-29', due_date: '2024-03-14', status: 'pending', description: 'March 2024 Services' },
  ],
  renewals: [
    { id: '1', contract_name: 'Analytics Support Renewal', renewal_date: '2025-12-31', current_value: 150000, proposed_value: 175000, status: 'upcoming', notes: 'Early discussions initiated' },
    { id: '2', contract_name: 'CRO Program Extension', renewal_date: '2024-06-30', current_value: 100000, proposed_value: 125000, status: 'in_negotiation', notes: 'Client interested in expanding scope' },
  ],
  revenue_channels: [
    { channel: 'Implementation Services', amount: 150000, percentage: 33.3 },
    { channel: 'Monthly Retainer', amount: 225000, percentage: 50 },
    { channel: 'CRO Services', amount: 75000, percentage: 16.7 },
  ],
};

// Mock Strategy Data
export const mockStrategyData: StrategyData = {
  stakeholders: [
    { id: '1', name: 'Rajesh Kumar', role: 'VP Digital Transformation', influence: 'high', alignment: 'advocate', notes: 'Strong champion for Tatvic, driving expansion' },
    { id: '2', name: 'Priya Sharma', role: 'Head of Marketing Analytics', influence: 'high', alignment: 'advocate', notes: 'Technical buyer, very satisfied with delivery' },
    { id: '3', name: 'Amit Patel', role: 'IT Director', influence: 'medium', alignment: 'neutral', notes: 'Security-focused, needs more convincing' },
    { id: '4', name: 'Neha Gupta', role: 'CFO', influence: 'high', alignment: 'neutral', notes: 'Price sensitive, ROI focused' },
  ],
  roadmap: [
    { id: '1', title: 'Advanced Attribution Modeling', description: 'Implement data-driven attribution across all channels', quarter: 'Q2 2024', status: 'planned', priority: 'high' },
    { id: '2', title: 'Predictive Analytics', description: 'ML-based churn prediction and LTV modeling', quarter: 'Q3 2024', status: 'planned', priority: 'high' },
    { id: '3', title: 'Real-time Personalization', description: 'CDP implementation for 1:1 personalization', quarter: 'Q4 2024', status: 'planned', priority: 'medium' },
    { id: '4', title: 'Cross-sell Optimization', description: 'Analytics-driven cross-sell recommendation engine', quarter: 'Q1 2025', status: 'planned', priority: 'medium' },
  ],
  upsell_opportunities: [
    { service_category: 'Data Marketing', title: 'CDP Implementation', description: 'Implement a Unified Customer Data Platform.', pitch: 'Leverage our CDP expertise to unify your marketing data.', potential_value: 'High', rationale: 'Strong interest from Rajesh Kumar' },
    { service_category: 'AI & ML', title: 'Advanced ML Models', description: 'Deploy predictive models for customer behavior.', pitch: 'Boost ROI with data-driven insights.', potential_value: 'Medium', rationale: 'Early discussions' },
    { service_category: 'Training', title: 'Training & Enablement', description: 'Empower your team with advanced training.', pitch: 'Upskill your internal analytics team.', potential_value: 'Low', rationale: 'Proposal submitted' },
  ],
  competitive_landscape: [
    { id: '1', name: 'Competitor A', strengths: ['Lower pricing', 'Local presence'], weaknesses: ['Limited technical expertise', 'No CRO capabilities'], our_advantage: 'Superior technical depth and proven ROI' },
    { id: '2', name: 'Competitor B', strengths: ['Big brand name', 'Full service'], weaknesses: ['Slow delivery', 'High turnover'], our_advantage: 'Agile delivery and dedicated team' },
  ],
};

// Mock Marketing Data
export const mockMarketingData: MarketingData = {
  brand_guidelines: {
    logo_url: 'https://www.icicilombard.com/images/logo.png',
    brand_colors: ['#004D99', '#FF6B00', '#FFFFFF'],
    tone_of_voice: 'Professional, trustworthy, customer-centric',
    messaging_guidelines: 'Focus on customer benefits, not product features. Use simple language.',
    approved_assets: ['Brand Guidelines PDF', 'Logo Package', 'Image Library'],
  },
  success_stories: [
    { id: '1', title: 'GA4 Migration Success', description: 'Seamless migration with zero data loss and improved insights', metrics: { 'data_accuracy': '99.9%', 'reporting_speed': '3x faster' }, case_study_eligible: true, approval_status: 'approved' },
    { id: '2', title: 'CRO Program Results', description: 'First experiment delivered 7.2% conversion improvement', metrics: { 'conversion_lift': '7.2%', 'revenue_impact': '$500K' }, case_study_eligible: true, approval_status: 'pending' },
  ],
  testimonials: [
    { id: '1', quote: 'Tatvic has transformed our analytics capabilities. The team is exceptional.', author: 'Rajesh Kumar', role: 'VP Digital Transformation', date: '2024-01-15', approval_status: 'approved' },
    { id: '2', quote: 'The GA4 migration was seamless. We now have better insights than ever.', author: 'Priya Sharma', role: 'Head of Marketing Analytics', date: '2024-01-20', approval_status: 'approved' },
  ],
  public_references: [
    { id: '1', type: 'blog_post', title: 'How ICICI Lombard Transformed Their Analytics', url: '#', date: '2024-02-01', status: 'planned' },
    { id: '2', type: 'press_release', title: 'Tatvic Partners with ICICI Lombard for Enterprise Analytics', url: '#', date: '2023-06-15', status: 'published' },
  ],
};

// Default section permissions by role
export const defaultPermissions: Record<string, SectionPermissions> = {
  admin: {
    universal: 'ADMIN',
    operations: 'ADMIN',
    technical: 'ADMIN',
    commercial: 'ADMIN',
    strategy: 'ADMIN',
    marketing: 'ADMIN',
  },
  tech: {
    universal: 'VIEW',
    operations: 'EDIT',
    technical: 'ADMIN',
    commercial: 'NONE',
    strategy: 'VIEW',
    marketing: 'NONE',
  },
  pm: {
    universal: 'VIEW',
    operations: 'ADMIN',
    technical: 'VIEW',
    commercial: 'VIEW',
    strategy: 'VIEW',
    marketing: 'VIEW',
  },
  management: {
    universal: 'VIEW',
    operations: 'VIEW',
    technical: 'VIEW',
    commercial: 'ADMIN',
    strategy: 'VIEW',
    marketing: 'VIEW',
  },
  strategy: {
    universal: 'VIEW',
    operations: 'VIEW',
    technical: 'VIEW',
    commercial: 'NONE',
    strategy: 'ADMIN',
    marketing: 'EDIT',
  },
  marketing: {
    universal: 'VIEW',
    operations: 'NONE',
    technical: 'NONE',
    commercial: 'NONE',
    strategy: 'VIEW',
    marketing: 'ADMIN',
  },
  viewer: {
    universal: 'VIEW',
    operations: 'VIEW',
    technical: 'VIEW',
    commercial: 'NONE',
    strategy: 'VIEW',
    marketing: 'VIEW',
  },
};

// Get permissions for current user
export function getCurrentUserPermissions(): SectionPermissions {
  return defaultPermissions[currentUser.role] || defaultPermissions.viewer;
}
