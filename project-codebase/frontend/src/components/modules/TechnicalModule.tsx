import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { CollapsibleList } from '@/components/ui/collapsible-list';
import { useEditMode } from '@/hooks/useEditMode';
import { useStore } from '@/store/useStore';
import { technicalApi } from '@/services/api';
import type { TechnicalData } from '@/types';
import {
  Code2,
  ChevronDown,
  ChevronUp,
  Database,
  Key,
  Wrench,
  FlaskConical,
  CheckCircle2,
  ExternalLink,
  Layers,
  Cpu,
  BarChart3,
  Smartphone,
  TestTube,
  Plus,
  Pencil,
  Trash2,
  X,
  Check,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface TechnicalModuleProps {
  isExpanded: boolean;
  onToggle: () => void;
}

export function TechnicalModule({ isExpanded, onToggle }: TechnicalModuleProps) {
  const { selectedClient, selectedProject } = useStore();
  const [data, setData] = useState<TechnicalData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('stack');
  const [isSaving, setIsSaving] = useState(false);

  const loadData = useCallback(async () => {
    if (!selectedClient || !selectedProject) return;
    setIsLoading(true);
    try {
      // Use client_id and project_id for backend compatibility
      const clientId = selectedProject.client_id || selectedClient.id;
      const projectId = selectedProject.project_id || selectedProject.id;

      const [techStackRes, credentialsRes, experimentsRes, implementationsRes] = await Promise.all([
        technicalApi.getTechStack(clientId, projectId),
        technicalApi.getCredentials(clientId, projectId),
        technicalApi.getExperiments(clientId, projectId),
        technicalApi.getImplementations(clientId, projectId),
      ]);

      if (techStackRes.success && credentialsRes.success && experimentsRes.success) {
        setData({
          tech_stack: techStackRes.data || [],
          credentials: credentialsRes.data || [],
          experiments: experimentsRes.data || [],
          implementations: implementationsRes.success ? (implementationsRes.data || []) : [],
        });
      }
    } catch (error) {
      console.error('Failed to load technical data:', error);
    } finally {
      setIsLoading(false);
    }
  }, [selectedClient, selectedProject]);

  // Edit mode hook
  const { canEdit } = useEditMode({
    section: 'technical',
    onSave: loadData,
  });

  // Edit states
  const [newTechItem, setNewTechItem] = useState({ technology: '', category: '', status: 'active' as const });
  const [newExperiment, setNewExperiment] = useState({ name: '', hypothesis: '', status: 'planned' as const, results: '' });
  const [newCredential, setNewCredential] = useState({ system: '', url: '', username: '', notes: '', status: 'active' as const, last_verified: '' });
  const [newImplementation, setNewImplementation] = useState({ title: '', date: '', implemented_by: '', description: '', category: 'General' });
  const [showAddTech, setShowAddTech] = useState(false);
  const [showAddExperiment, setShowAddExperiment] = useState(false);
  const [showAddCredential, setShowAddCredential] = useState(false);
  const [showAddImplementation, setShowAddImplementation] = useState(false);
  
  // Edit item states
  const [editingTechId, setEditingTechId] = useState<string | null>(null);
  const [editingCredentialId, setEditingCredentialId] = useState<string | null>(null);
  const [editingImplementationId, setEditingImplementationId] = useState<string | null>(null);
  const [editingExperimentId, setEditingExperimentId] = useState<string | null>(null);
  const [editTechItem, setEditTechItem] = useState({ technology: '', category: '', status: 'active' as const });
  const [editCredential, setEditCredential] = useState({ system: '', url: '', username: '', notes: '', status: 'active' as const, last_verified: '' });
  const [editImplementation, setEditImplementation] = useState({ title: '', date: '', implemented_by: '', description: '', category: 'General' });
  const [editExperiment, setEditExperiment] = useState({ name: '', hypothesis: '', status: 'planned' as const, results: '' });

  useEffect(() => {
    if (selectedClient && selectedProject) {
      loadData();
    }
  }, [selectedClient, selectedProject, loadData]);

  // Get IDs for API calls
  const getIds = () => {
    const clientId = selectedProject?.client_id || selectedClient?.id || '';
    const projectId = selectedProject?.project_id || selectedProject?.id || '';
    return { clientId, projectId };
  };

  // Add handlers
  const handleAddTechStack = async () => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId || !newTechItem.technology) return;

    setIsSaving(true);
    try {
      await technicalApi.addTechStackItem(clientId, projectId, newTechItem);
      setNewTechItem({ technology: '', category: '', status: 'active' });
      setShowAddTech(false);
      loadData();
    } catch (error) {
      console.error('Failed to add tech stack item:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleAddExperiment = async () => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId || !newExperiment.name) return;

    setIsSaving(true);
    try {
      await technicalApi.addExperiment(clientId, projectId, newExperiment);
      setNewExperiment({ name: '', hypothesis: '', status: 'planned', results: '' });
      setShowAddExperiment(false);
      loadData();
    } catch (error) {
      console.error('Failed to add experiment:', error);
    } finally {
      setIsSaving(false);
    }
  };

  // Add Credential handler
  const handleAddCredential = async () => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId || !newCredential.system) return;

    setIsSaving(true);
    try {
      await technicalApi.addCredential(clientId, projectId, newCredential);
      setNewCredential({ system: '', url: '', username: '', notes: '', status: 'active', last_verified: '' });
      setShowAddCredential(false);
      loadData();
    } catch (error) {
      console.error('Failed to add credential:', error);
    } finally {
      setIsSaving(false);
    }
  };

  // Add Implementation handler
  const handleAddImplementation = async () => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId || !newImplementation.title) return;

    setIsSaving(true);
    try {
      await technicalApi.addImplementation(clientId, projectId, newImplementation);
      setNewImplementation({ title: '', date: '', implemented_by: '', description: '', category: 'General' });
      setShowAddImplementation(false);
      loadData();
    } catch (error) {
      console.error('Failed to add implementation:', error);
    } finally {
      setIsSaving(false);
    }
  };

  // Update handlers
  const handleUpdateTechStack = async (id: string) => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId) return;

    setIsSaving(true);
    try {
      await technicalApi.updateTechStackItem(clientId, projectId, id, editTechItem);
      setEditingTechId(null);
      loadData();
    } catch (error) {
      console.error('Failed to update tech stack item:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleUpdateCredential = async (id: string) => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId) return;

    setIsSaving(true);
    try {
      await technicalApi.updateCredential(clientId, projectId, id, editCredential);
      setEditingCredentialId(null);
      loadData();
    } catch (error) {
      console.error('Failed to update credential:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleUpdateImplementation = async (id: string) => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId) return;

    setIsSaving(true);
    try {
      await technicalApi.updateImplementation(clientId, projectId, id, editImplementation);
      setEditingImplementationId(null);
      loadData();
    } catch (error) {
      console.error('Failed to update implementation:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleUpdateExperiment = async (id: string) => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId) return;

    setIsSaving(true);
    try {
      await technicalApi.updateExperiment(clientId, projectId, id, editExperiment);
      setEditingExperimentId(null);
      loadData();
    } catch (error) {
      console.error('Failed to update experiment:', error);
    } finally {
      setIsSaving(false);
    }
  };

  // Delete handlers
  const handleDeleteTechStack = async (id: string) => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId) return;

    if (!confirm('Are you sure you want to delete this technology?')) return;

    setIsSaving(true);
    try {
      await technicalApi.deleteTechStackItem(clientId, projectId, id);
      loadData();
    } catch (error) {
      console.error('Failed to delete tech stack item:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteCredential = async (id: string) => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId) return;

    if (!confirm('Are you sure you want to delete this credential?')) return;

    setIsSaving(true);
    try {
      await technicalApi.deleteCredential(clientId, projectId, id);
      loadData();
    } catch (error) {
      console.error('Failed to delete credential:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteImplementation = async (id: string) => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId) return;

    if (!confirm('Are you sure you want to delete this implementation?')) return;

    setIsSaving(true);
    try {
      await technicalApi.deleteImplementation(clientId, projectId, id);
      loadData();
    } catch (error) {
      console.error('Failed to delete implementation:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteExperiment = async (id: string) => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId) return;

    if (!confirm('Are you sure you want to delete this experiment?')) return;

    setIsSaving(true);
    try {
      await technicalApi.deleteExperiment(clientId, projectId, id);
      loadData();
    } catch (error) {
      console.error('Failed to delete experiment:', error);
    } finally {
      setIsSaving(false);
    }
  };

  // Start editing helpers
  const startEditingTech = (item: any) => {
    setEditingTechId(item.id);
    setEditTechItem({ technology: item.technology, category: item.category, status: item.status });
  };

  const startEditingCredential = (cred: any) => {
    setEditingCredentialId(cred.id);
    setEditCredential({ system: cred.system, url: cred.url || '', username: cred.username || '', notes: cred.notes || '', status: cred.status || 'active', last_verified: cred.last_verified || '' });
  };

  const startEditingImplementation = (impl: any) => {
    setEditingImplementationId(impl.id);
    setEditImplementation({ title: impl.title, date: impl.date || '', implemented_by: impl.implemented_by || '', description: impl.description || '', category: impl.category || 'General' });
  };

  const startEditingExperiment = (exp: any) => {
    setEditingExperimentId(exp.id);
    setEditExperiment({ name: exp.name, hypothesis: exp.hypothesis || '', status: exp.status || 'planned', results: exp.results || '' });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-emerald-100 text-emerald-700 border-emerald-200';
      case 'deprecated': return 'bg-red-100 text-red-700 border-red-200';
      case 'planned': return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'pending': return 'bg-amber-100 text-amber-700 border-amber-200';
      case 'expired': return 'bg-red-100 text-red-700 border-red-200';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case 'analytics': return <BarChart3 className="w-4 h-4" />;
      case 'tag management': return <TagsIcon className="w-4 h-4" />;
      case 'data warehouse': return <Database className="w-4 h-4" />;
      case 'visualization': return <Layers className="w-4 h-4" />;
      case 'mobile analytics': return <Smartphone className="w-4 h-4" />;
      case 'experimentation': return <TestTube className="w-4 h-4" />;
      case 'infrastructure': return <Cpu className="w-4 h-4" />;
      case 'advertising': return <ExternalLink className="w-4 h-4" />;
      default: return <Code2 className="w-4 h-4" />;
    }
  };

  if (isLoading) {
    return (
      <Card className="module-section">
        <CardHeader className="module-header">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-[#321a75]/10 flex items-center justify-center">
              <Code2 className="w-5 h-5 text-[#321a75]" />
            </div>
            <div>
              <CardTitle className="text-lg font-semibold text-gray-900">Technical Details</CardTitle>
              <p className="text-sm text-gray-500">Tech Focus</p>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-8">
          <div className="flex items-center justify-center">
            <div className="animate-pulse text-gray-400">Loading...</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data) return null;

  return (
    <Card className="module-section overflow-hidden">
      <CardHeader className="module-header" onClick={onToggle}>
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#321a75] to-[#4a2d99] flex items-center justify-center">
            <Code2 className="w-5 h-5 text-white" />
          </div>
          <div>
            <CardTitle className="text-lg font-semibold text-gray-900">Technical Details</CardTitle>
            <p className="text-sm text-gray-500">Tech Focus</p>
          </div>
        </div>
        <Button variant="ghost" size="icon">
          {isExpanded ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
        </Button>
      </CardHeader>

      {isExpanded && (
        <CardContent className="p-6">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-5 mb-6">
              <TabsTrigger value="stack" className="text-sm">
                <Database className="w-4 h-4 mr-2" />
                Tech Stack
              </TabsTrigger>
              <TabsTrigger value="credentials" className="text-sm">
                <Key className="w-4 h-4 mr-2" />
                Credentials
              </TabsTrigger>
              <TabsTrigger value="implementations" className="text-sm">
                <Wrench className="w-4 h-4 mr-2" />
                Implementations
              </TabsTrigger>
              <TabsTrigger value="experiments" className="text-sm">
                <FlaskConical className="w-4 h-4 mr-2" />
                Experiments
              </TabsTrigger>
              <TabsTrigger value="analytics" className="text-sm">
                <BarChart3 className="w-4 h-4 mr-2" />
                Analytics
              </TabsTrigger>
            </TabsList>

            <TabsContent value="stack">
              {/* Add Tech Stack Button */}
              {canEdit && (
                <div className="mb-4">
                  {showAddTech ? (
                    <div className="p-4 bg-gray-50 rounded-xl border border-gray-200">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                        <Input
                          value={newTechItem.technology}
                          onChange={(e) => setNewTechItem({ ...newTechItem, technology: e.target.value })}
                          placeholder="Technology name"
                        />
                        <Input
                          value={newTechItem.category}
                          onChange={(e) => setNewTechItem({ ...newTechItem, category: e.target.value })}
                          placeholder="Category (e.g., Analytics)"
                        />
                        <select
                          value={newTechItem.status}
                          onChange={(e) => setNewTechItem({ ...newTechItem, status: e.target.value as any })}
                          className="h-10 px-3 border rounded-md bg-white"
                        >
                          <option value="active">Active</option>
                          <option value="planned">Planned</option>
                          <option value="deprecated">Deprecated</option>
                        </select>
                      </div>
                      <div className="flex gap-2">
                        <Button onClick={handleAddTechStack} size="sm" className="bg-[#321a75] hover:bg-[#4a2d99]" disabled={isSaving}>
                          <Plus className="h-4 w-4 mr-1" /> {isSaving ? 'Adding...' : 'Add'}
                        </Button>
                        <Button onClick={() => setShowAddTech(false)} variant="outline" size="sm">
                          Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <Button onClick={() => setShowAddTech(true)} variant="outline" className="w-full">
                      <Plus className="h-4 w-4 mr-2" /> Add Technology
                    </Button>
                  )}
                </div>
              )}
              <CollapsibleList
                items={data.tech_stack}
                renderItem={(item) => (
                  <div
                    key={item.id}
                    className="p-4 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors border border-gray-100"
                  >
                    {editingTechId === item.id ? (
                      // Edit mode
                      <div className="space-y-3">
                        <Input
                          value={editTechItem.technology}
                          onChange={(e) => setEditTechItem({ ...editTechItem, technology: e.target.value })}
                          placeholder="Technology name"
                        />
                        <Input
                          value={editTechItem.category}
                          onChange={(e) => setEditTechItem({ ...editTechItem, category: e.target.value })}
                          placeholder="Category"
                        />
                        <select
                          value={editTechItem.status}
                          onChange={(e) => setEditTechItem({ ...editTechItem, status: e.target.value as any })}
                          className="h-10 w-full px-3 border rounded-md bg-white"
                        >
                          <option value="active">Active</option>
                          <option value="planned">Planned</option>
                          <option value="deprecated">Deprecated</option>
                        </select>
                        <div className="flex gap-2">
                          <Button onClick={() => handleUpdateTechStack(item.id)} size="sm" className="bg-[#321a75] hover:bg-[#4a2d99]" disabled={isSaving}>
                            <Check className="h-4 w-4 mr-1" /> {isSaving ? 'Saving...' : 'Save'}
                          </Button>
                          <Button onClick={() => setEditingTechId(null)} variant="outline" size="sm">
                            <X className="h-4 w-4 mr-1" /> Cancel
                          </Button>
                        </div>
                      </div>
                    ) : (
                      // View mode
                      <>
                        <div className="flex items-start justify-between mb-3">
                          <div className="w-10 h-10 rounded-lg bg-[#321a75]/10 flex items-center justify-center text-[#321a75]">
                            {getCategoryIcon(item.category)}
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className={cn('text-xs', getStatusColor(item.status))}>
                              {item.status}
                            </Badge>
                            {canEdit && (
                              <div className="flex gap-1">
                                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => startEditingTech(item)}>
                                  <Pencil className="h-3.5 w-3.5 text-gray-500 hover:text-[#321a75]" />
                                </Button>
                                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => handleDeleteTechStack(item.id)}>
                                  <Trash2 className="h-3.5 w-3.5 text-gray-500 hover:text-red-500" />
                                </Button>
                              </div>
                            )}
                          </div>
                        </div>
                        <h4 className="font-semibold text-gray-900 mb-1">{item.technology}</h4>
                        <p className="text-xs text-gray-500 mb-2">{item.category}</p>
                        {item.version && (
                          <p className="text-xs text-gray-400">Version: {item.version}</p>
                        )}
                        {item.notes && (
                          <p className="text-xs text-gray-500 mt-2 pt-2 border-t border-gray-200">{item.notes}</p>
                        )}
                      </>
                    )}
                  </div>
                )}
                initialDisplayCount={6}
                maxHeight="500px"
                itemsClassName="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
              />
            </TabsContent>

            <TabsContent value="credentials">
              {/* Add Credential Button */}
              {canEdit && (
                <div className="mb-4">
                  {showAddCredential ? (
                    <div className="p-4 bg-gray-50 rounded-xl border border-gray-200">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <Input
                          value={newCredential.system}
                          onChange={(e) => setNewCredential({ ...newCredential, system: e.target.value })}
                          placeholder="System name (e.g., Google Analytics)"
                        />
                        <Input
                          value={newCredential.url}
                          onChange={(e) => setNewCredential({ ...newCredential, url: e.target.value })}
                          placeholder="URL or contact email"
                        />
                        <Input
                          value={newCredential.username}
                          onChange={(e) => setNewCredential({ ...newCredential, username: e.target.value })}
                          placeholder="Access level or username"
                        />
                        <Input
                          value={newCredential.notes}
                          onChange={(e) => setNewCredential({ ...newCredential, notes: e.target.value })}
                          placeholder="Notes (optional)"
                        />
                      </div>
                      <div className="flex gap-2">
                        <Button onClick={handleAddCredential} size="sm" className="bg-[#321a75] hover:bg-[#4a2d99]" disabled={isSaving}>
                          <Plus className="h-4 w-4 mr-1" /> {isSaving ? 'Adding...' : 'Add'}
                        </Button>
                        <Button onClick={() => setShowAddCredential(false)} variant="outline" size="sm">
                          Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <Button onClick={() => setShowAddCredential(true)} variant="outline" className="w-full">
                      <Plus className="h-4 w-4 mr-2" /> Add Credential
                    </Button>
                  )}
                </div>
              )}
              {data.credentials.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Key className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <p>No credentials have been documented yet.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {data.credentials.map((cred) => (
                    <div
                      key={cred.id}
                      className="p-4 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors border border-gray-100"
                    >
                      {editingCredentialId === cred.id ? (
                        // Edit mode
                        <div className="space-y-3">
                          <Input
                            value={editCredential.system}
                            onChange={(e) => setEditCredential({ ...editCredential, system: e.target.value })}
                            placeholder="System name"
                          />
                          <Input
                            value={editCredential.url}
                            onChange={(e) => setEditCredential({ ...editCredential, url: e.target.value })}
                            placeholder="URL or contact"
                          />
                          <Input
                            value={editCredential.username}
                            onChange={(e) => setEditCredential({ ...editCredential, username: e.target.value })}
                            placeholder="Access level"
                          />
                          <Input
                            value={editCredential.notes}
                            onChange={(e) => setEditCredential({ ...editCredential, notes: e.target.value })}
                            placeholder="Notes"
                          />
                          <div className="flex gap-2">
                            <Button onClick={() => handleUpdateCredential(cred.id)} size="sm" className="bg-[#321a75] hover:bg-[#4a2d99]" disabled={isSaving}>
                              <Check className="h-4 w-4 mr-1" /> {isSaving ? 'Saving...' : 'Save'}
                            </Button>
                            <Button onClick={() => setEditingCredentialId(null)} variant="outline" size="sm">
                              <X className="h-4 w-4 mr-1" /> Cancel
                            </Button>
                          </div>
                        </div>
                      ) : (
                        // View mode
                        <>
                          <div className="flex items-center justify-between gap-3 mb-3">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 rounded-lg bg-[#faab00]/10 flex items-center justify-center text-[#faab00]">
                                <Key className="w-5 h-5" />
                              </div>
                              <h4 className="font-semibold text-gray-900">{cred.system}</h4>
                            </div>
                            {canEdit && (
                              <div className="flex gap-1">
                                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => startEditingCredential(cred)}>
                                  <Pencil className="h-3.5 w-3.5 text-gray-500 hover:text-[#321a75]" />
                                </Button>
                                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => handleDeleteCredential(cred.id)}>
                                  <Trash2 className="h-3.5 w-3.5 text-gray-500 hover:text-red-500" />
                                </Button>
                              </div>
                            )}
                          </div>
                          <div className="space-y-2 pl-1">
                            {cred.url && (
                              <div className="flex items-center gap-2">
                                <span className="text-xs font-medium text-gray-500 uppercase w-16">Contact</span>
                                <a
                                  href={cred.url.includes('@') ? `mailto:${cred.url}` : (cred.url.startsWith('http') ? cred.url : `https://${cred.url}`)}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-sm text-[#00c3c4] hover:underline flex items-center"
                                >
                                  Click Here
                                  <ExternalLink className="w-3 h-3 ml-1" />
                                </a>
                              </div>
                            )}
                            {cred.username && (
                              <div className="flex items-center gap-2">
                                <span className="text-xs font-medium text-gray-500 uppercase w-16">Access</span>
                                <span className="text-sm text-gray-700 bg-gray-100 px-2 py-0.5 rounded">
                                  {cred.username}
                                </span>
                              </div>
                            )}
                          </div>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="implementations">
              {/* Add Implementation Button */}
              {canEdit && (
                <div className="mb-4">
                  {showAddImplementation ? (
                    <div className="p-4 bg-gray-50 rounded-xl border border-gray-200">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <Input
                          value={newImplementation.title}
                          onChange={(e) => setNewImplementation({ ...newImplementation, title: e.target.value })}
                          placeholder="Implementation title"
                        />
                        <Input
                          type="date"
                          value={newImplementation.date}
                          onChange={(e) => setNewImplementation({ ...newImplementation, date: e.target.value })}
                          placeholder="Date"
                        />
                        <Input
                          value={newImplementation.implemented_by}
                          onChange={(e) => setNewImplementation({ ...newImplementation, implemented_by: e.target.value })}
                          placeholder="Implemented by"
                        />
                        <Input
                          value={newImplementation.description}
                          onChange={(e) => setNewImplementation({ ...newImplementation, description: e.target.value })}
                          placeholder="Description (optional)"
                        />
                      </div>
                      <div className="flex gap-2">
                        <Button onClick={handleAddImplementation} size="sm" className="bg-[#321a75] hover:bg-[#4a2d99]" disabled={isSaving}>
                          <Plus className="h-4 w-4 mr-1" /> {isSaving ? 'Adding...' : 'Add'}
                        </Button>
                        <Button onClick={() => setShowAddImplementation(false)} variant="outline" size="sm">
                          Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <Button onClick={() => setShowAddImplementation(true)} variant="outline" className="w-full">
                      <Plus className="h-4 w-4 mr-2" /> Add Implementation
                    </Button>
                  )}
                </div>
              )}
              {data.implementations.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Wrench className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <p>No implementation logs have been recorded yet.</p>
                </div>
              ) : (
                <div className="relative max-h-[400px] overflow-y-auto pr-2">
                  {/* Timeline line */}
                  <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />
                  <div className="space-y-4">
                    {data.implementations.map((impl) => (
                      <div key={impl.id} className="relative pl-10">
                        {/* Timeline dot */}
                        <div className="absolute left-2.5 top-2 w-3 h-3 bg-[#00c3c4] rounded-full border-2 border-white shadow" />
                        <div className="p-4 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors border border-gray-100">
                          {editingImplementationId === impl.id ? (
                            // Edit mode
                            <div className="space-y-3">
                              <Input
                                value={editImplementation.title}
                                onChange={(e) => setEditImplementation({ ...editImplementation, title: e.target.value })}
                                placeholder="Title"
                              />
                              <Input
                                type="date"
                                value={editImplementation.date}
                                onChange={(e) => setEditImplementation({ ...editImplementation, date: e.target.value })}
                                placeholder="Date"
                              />
                              <Input
                                value={editImplementation.implemented_by}
                                onChange={(e) => setEditImplementation({ ...editImplementation, implemented_by: e.target.value })}
                                placeholder="Implemented by"
                              />
                              <Input
                                value={editImplementation.description}
                                onChange={(e) => setEditImplementation({ ...editImplementation, description: e.target.value })}
                                placeholder="Description"
                              />
                              <div className="flex gap-2">
                                <Button onClick={() => handleUpdateImplementation(impl.id)} size="sm" className="bg-[#321a75] hover:bg-[#4a2d99]" disabled={isSaving}>
                                  <Check className="h-4 w-4 mr-1" /> {isSaving ? 'Saving...' : 'Save'}
                                </Button>
                                <Button onClick={() => setEditingImplementationId(null)} variant="outline" size="sm">
                                  <X className="h-4 w-4 mr-1" /> Cancel
                                </Button>
                              </div>
                            </div>
                          ) : (
                            // View mode
                            <div className="flex items-start justify-between gap-4">
                              <div className="flex-1">
                                <h4 className="font-semibold text-gray-900">{impl.title}</h4>
                                {impl.implemented_by && (
                                  <p className="text-sm text-gray-600 mt-1">
                                    <span className="font-medium">Owner:</span> {impl.implemented_by}
                                  </p>
                                )}
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-gray-500 whitespace-nowrap font-medium bg-gray-100 px-2 py-1 rounded">
                                  {impl.date}
                                </span>
                                {canEdit && (
                                  <div className="flex gap-1">
                                    <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => startEditingImplementation(impl)}>
                                      <Pencil className="h-3.5 w-3.5 text-gray-500 hover:text-[#321a75]" />
                                    </Button>
                                    <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => handleDeleteImplementation(impl.id)}>
                                      <Trash2 className="h-3.5 w-3.5 text-gray-500 hover:text-red-500" />
                                    </Button>
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </TabsContent>

            <TabsContent value="experiments">
              {/* Add Experiment Button */}
              {canEdit && (
                <div className="mb-4">
                  {showAddExperiment ? (
                    <div className="p-4 bg-gray-50 rounded-xl border border-gray-200">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <Input
                          value={newExperiment.name}
                          onChange={(e) => setNewExperiment({ ...newExperiment, name: e.target.value })}
                          placeholder="Experiment name"
                        />
                        <select
                          value={newExperiment.status}
                          onChange={(e) => setNewExperiment({ ...newExperiment, status: e.target.value as any })}
                          className="h-10 px-3 border rounded-md bg-white"
                        >
                          <option value="planned">Planned</option>
                          <option value="running">Running</option>
                          <option value="completed">Completed</option>
                          <option value="cancelled">Cancelled</option>
                        </select>
                      </div>
                      <Input
                        value={newExperiment.hypothesis}
                        onChange={(e) => setNewExperiment({ ...newExperiment, hypothesis: e.target.value })}
                        placeholder="Hypothesis"
                        className="mb-4"
                      />
                      <Input
                        value={newExperiment.results}
                        onChange={(e) => setNewExperiment({ ...newExperiment, results: e.target.value })}
                        placeholder="Results (optional)"
                        className="mb-4"
                      />
                      <div className="flex gap-2">
                        <Button onClick={handleAddExperiment} size="sm" className="bg-[#321a75] hover:bg-[#4a2d99]" disabled={isSaving}>
                          <Plus className="h-4 w-4 mr-1" /> {isSaving ? 'Adding...' : 'Add'}
                        </Button>
                        <Button onClick={() => setShowAddExperiment(false)} variant="outline" size="sm">
                          Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <Button onClick={() => setShowAddExperiment(true)} variant="outline" className="w-full">
                      <Plus className="h-4 w-4 mr-2" /> Add Experiment
                    </Button>
                  )}
                </div>
              )}
              {data.experiments.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <FlaskConical className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <p>No experiment results have been logged yet.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {data.experiments.map((exp) => (
                    <div
                      key={exp.id}
                      className="p-5 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors border border-gray-100"
                    >
                      {editingExperimentId === exp.id ? (
                        // Edit mode
                        <div className="space-y-3">
                          <Input
                            value={editExperiment.name}
                            onChange={(e) => setEditExperiment({ ...editExperiment, name: e.target.value })}
                            placeholder="Experiment name"
                          />
                          <select
                            value={editExperiment.status}
                            onChange={(e) => setEditExperiment({ ...editExperiment, status: e.target.value as any })}
                            className="h-10 w-full px-3 border rounded-md bg-white"
                          >
                            <option value="planned">Planned</option>
                            <option value="running">Running</option>
                            <option value="completed">Completed</option>
                            <option value="cancelled">Cancelled</option>
                          </select>
                          <Input
                            value={editExperiment.hypothesis}
                            onChange={(e) => setEditExperiment({ ...editExperiment, hypothesis: e.target.value })}
                            placeholder="Hypothesis"
                          />
                          <Input
                            value={editExperiment.results}
                            onChange={(e) => setEditExperiment({ ...editExperiment, results: e.target.value })}
                            placeholder="Results"
                          />
                          <div className="flex gap-2">
                            <Button onClick={() => handleUpdateExperiment(exp.id)} size="sm" className="bg-[#321a75] hover:bg-[#4a2d99]" disabled={isSaving}>
                              <Check className="h-4 w-4 mr-1" /> {isSaving ? 'Saving...' : 'Save'}
                            </Button>
                            <Button onClick={() => setEditingExperimentId(null)} variant="outline" size="sm">
                              <X className="h-4 w-4 mr-1" /> Cancel
                            </Button>
                          </div>
                        </div>
                      ) : (
                        // View mode
                        <>
                          <div className="flex items-start justify-between mb-4">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 rounded-lg bg-[#321a75]/10 flex items-center justify-center text-[#321a75]">
                                <FlaskConical className="w-5 h-5" />
                              </div>
                              <h4 className="font-semibold text-gray-900 text-lg">{exp.name}</h4>
                            </div>
                            <div className="flex items-center gap-2">
                              {exp.end_date && (
                                <span className="text-xs bg-emerald-100 text-emerald-800 px-2 py-1 rounded-full whitespace-nowrap">
                                  Deployed: {exp.end_date}
                                </span>
                              )}
                              {canEdit && (
                                <div className="flex gap-1">
                                  <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => startEditingExperiment(exp)}>
                                    <Pencil className="h-3.5 w-3.5 text-gray-500 hover:text-[#321a75]" />
                                  </Button>
                                  <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => handleDeleteExperiment(exp.id)}>
                                    <Trash2 className="h-3.5 w-3.5 text-gray-500 hover:text-red-500" />
                                  </Button>
                                </div>
                              )}
                            </div>
                          </div>

                          <div className="space-y-3">
                            {/* Hypothesis */}
                            {exp.hypothesis && (
                              <div className="bg-blue-50 rounded-lg p-3 border-l-4 border-blue-400">
                                <span className="text-xs font-semibold text-blue-700 uppercase tracking-wide">Hypothesis</span>
                                <p className="text-sm text-gray-700 mt-1">{exp.hypothesis}</p>
                              </div>
                            )}

                            {/* Results */}
                            {exp.results && (
                              <div className="bg-purple-50 rounded-lg p-3 border-l-4 border-purple-400">
                                <span className="text-xs font-semibold text-purple-700 uppercase tracking-wide">Result</span>
                                <p className="text-sm text-gray-700 mt-1">{exp.results}</p>
                              </div>
                            )}

                            {/* Winner */}
                            {exp.winner && (
                              <div className="bg-emerald-50 rounded-lg p-3 border-l-4 border-emerald-400">
                                <span className="text-xs font-semibold text-emerald-700 uppercase tracking-wide">Winner</span>
                                <p className="text-sm text-gray-700 mt-1 flex items-center">
                                  <CheckCircle2 className="w-4 h-4 mr-1 text-emerald-600" />
                                  {exp.winner}
                                </p>
                              </div>
                            )}
                          </div>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </TabsContent>
            <TabsContent value="analytics">
              <div className="space-y-6">
                <div className="p-6 rounded-2xl bg-gray-50 border border-gray-100">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-lg bg-[#10b981]/10 flex items-center justify-center text-[#10b981]">
                      <CheckCircle2 className="w-5 h-5" />
                    </div>
                    <h4 className="text-lg font-semibold text-gray-900">Optimization Insight</h4>
                  </div>
                  <p className="text-gray-600">
                    You have {data.tech_stack.filter(t => t.status === 'active').length} active technologies.
                    {data.tech_stack.filter(t => t.status === 'deprecated').length > 0 ?
                      ` Consider phasing out the ${data.tech_stack.filter(t => t.status === 'deprecated').length} deprecated items to reduce technical debt.` :
                      " Your tech stack is lean and up to date."}
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="p-6 rounded-2xl bg-white border border-gray-100 shadow-sm text-center">
                    <p className="text-xs text-gray-400 uppercase font-bold tracking-wider mb-2">Active Tech</p>
                    <p className="text-4xl font-bold text-[#321a75]">{data.tech_stack.filter(t => t.status === 'active').length}</p>
                  </div>
                  <div className="p-6 rounded-2xl bg-white border border-gray-100 shadow-sm text-center">
                    <p className="text-xs text-gray-400 uppercase font-bold tracking-wider mb-2">Implementations</p>
                    <p className="text-4xl font-bold text-[#00c3c4]">{data.implementations.length}</p>
                  </div>
                  <div className="p-6 rounded-2xl bg-white border border-gray-100 shadow-sm text-center">
                    <p className="text-xs text-gray-400 uppercase font-bold tracking-wider mb-2">Experiments</p>
                    <p className="text-4xl font-bold text-[#faab00]">{data.experiments.length}</p>
                  </div>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      )}
    </Card>
  );
}

function TagsIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 5H2v7l6.29 6.29c.94.94 2.48.94 3.42 0l3.58-3.58c.94-.94.94-2.48 0-3.42L9 5Z" />
      <path d="M6 9.01V9" />
      <path d="m15 5 6.3 6.29a2.4 2.4 0 0 1 0 3.42l-3.58 3.58a2.4 2.4 0 0 1-3.42 0L8 15" />
    </svg>
  );
}
