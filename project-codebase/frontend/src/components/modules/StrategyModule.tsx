import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { CollapsibleList } from '@/components/ui/collapsible-list';
import { useEditMode } from '@/hooks/useEditMode';
import { useStore } from '@/store/useStore';
import { strategyApi } from '@/services/api';
import type { StrategyData, Stakeholder, RoadmapItem } from '@/types';
import { StakeholderMatrix } from '@/components/ui/charts';
import {
  Target,
  ChevronDown,
  ChevronUp,
  Users,
  Map as MapIcon,
  ThumbsUp,
  ThumbsDown,
  Minus,
  Calendar,
  Flag,
  Plus,
  Globe,
  Pencil,
  Trash2,
  X,
  Check,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface StrategyModuleProps {
  isExpanded: boolean;
  onToggle: () => void;
}

export function StrategyModule({ isExpanded, onToggle }: StrategyModuleProps) {
  const { selectedClient, selectedProject } = useStore();
  const [data, setData] = useState<StrategyData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('stakeholders');
  const [isSaving, setIsSaving] = useState(false);

  const loadData = useCallback(async () => {
    if (!selectedClient || !selectedProject) return;
    setIsLoading(true);
    try {
      const clientId = selectedProject.client_id || selectedClient.id;
      const projectId = selectedProject.project_id || selectedProject.id;

      const response = await strategyApi.get(clientId, projectId);

      if (response.success && response.data) {
        setData(response.data);
      }
    } catch (error) {
      console.error('Failed to load strategy data:', error);
    } finally {
      setIsLoading(false);
    }
  }, [selectedClient, selectedProject]);

  // Edit mode hook
  const { canEdit } = useEditMode({
    section: 'strategy',
    onSave: loadData,
  });

  // Add states with proper types matching the Stakeholder and RoadmapItem interfaces
  const [newStakeholder, setNewStakeholder] = useState<{ name: string; role: string; influence: 'high' | 'medium' | 'low'; alignment: 'advocate' | 'neutral' | 'skeptical'; notes: string }>({
    name: '', role: '', influence: 'medium', alignment: 'neutral', notes: ''
  });
  const [newRoadmapItem, setNewRoadmapItem] = useState<{ title: string; description: string; quarter: string; status: 'planned' | 'in_progress' | 'completed'; priority: 'high' | 'medium' | 'low' }>({
    title: '', description: '', quarter: '', status: 'planned', priority: 'medium'
  });
  const [newEcosystemItem, setNewEcosystemItem] = useState<{ platform: string; purpose: string }>({
    platform: '', purpose: ''
  });
  const [showAddStakeholder, setShowAddStakeholder] = useState(false);
  const [showAddRoadmap, setShowAddRoadmap] = useState(false);
  const [showAddEcosystem, setShowAddEcosystem] = useState(false);
  
  // Edit states
  const [editingStakeholderId, setEditingStakeholderId] = useState<string | null>(null);
  const [editingStakeholder, setEditingStakeholder] = useState<{ name: string; role: string; influence: 'high' | 'medium' | 'low'; alignment: 'advocate' | 'neutral' | 'skeptical'; notes: string } | null>(null);
  const [editingRoadmapId, setEditingRoadmapId] = useState<string | null>(null);
  const [editingRoadmapItem, setEditingRoadmapItem] = useState<{ title: string; description: string; quarter: string; status: 'planned' | 'in_progress' | 'completed'; priority: 'high' | 'medium' | 'low' } | null>(null);
  const [editingEcosystemIdx, setEditingEcosystemIdx] = useState<number | null>(null);
  const [editingEcosystemItem, setEditingEcosystemItem] = useState<{ platform: string; purpose: string } | null>(null);

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
  const handleAddStakeholder = async () => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId || !newStakeholder.name) return;

    setIsSaving(true);
    try {
      await strategyApi.addStakeholder(clientId, projectId, newStakeholder);
      setNewStakeholder({ name: '', role: '', influence: 'medium', alignment: 'neutral', notes: '' });
      setShowAddStakeholder(false);
      loadData();
    } catch (error) {
      console.error('Failed to add stakeholder:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleAddRoadmapItem = async () => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId || !newRoadmapItem.title) return;

    setIsSaving(true);
    try {
      await strategyApi.addRoadmapItem(clientId, projectId, newRoadmapItem);
      setNewRoadmapItem({ title: '', description: '', quarter: '', status: 'planned', priority: 'medium' });
      setShowAddRoadmap(false);
      loadData();
    } catch (error) {
      console.error('Failed to add roadmap item:', error);
    } finally {
      setIsSaving(false);
    }
  };

  // Edit/Delete handlers for stakeholders
  const handleEditStakeholder = (stakeholder: Stakeholder) => {
    setEditingStakeholderId(stakeholder.id);
    setEditingStakeholder({
      name: stakeholder.name,
      role: stakeholder.role,
      influence: stakeholder.influence,
      alignment: stakeholder.alignment,
      notes: stakeholder.notes || ''
    });
  };

  const handleSaveStakeholder = async () => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId || !data || !editingStakeholder) return;

    setIsSaving(true);
    try {
      const updatedStakeholders = data.stakeholders.map(s => 
        s.id === editingStakeholderId 
          ? { ...editingStakeholder, id: s.id }
          : { name: s.name, role: s.role, influence: s.influence, alignment: s.alignment, notes: s.notes || '' }
      );
      await strategyApi.updateStakeholders(clientId, projectId, updatedStakeholders);
      setEditingStakeholderId(null);
      setEditingStakeholder(null);
      loadData();
    } catch (error) {
      console.error('Failed to update stakeholder:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteStakeholder = async (stakeholderId: string) => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId || !data) return;

    setIsSaving(true);
    try {
      const updatedStakeholders = data.stakeholders
        .filter(s => s.id !== stakeholderId)
        .map(s => ({ name: s.name, role: s.role, influence: s.influence, alignment: s.alignment, notes: s.notes || '' }));
      await strategyApi.updateStakeholders(clientId, projectId, updatedStakeholders);
      loadData();
    } catch (error) {
      console.error('Failed to delete stakeholder:', error);
    } finally {
      setIsSaving(false);
    }
  };

  // Edit/Delete handlers for roadmap items
  const handleEditRoadmapItem = (item: RoadmapItem) => {
    setEditingRoadmapId(item.id);
    setEditingRoadmapItem({
      title: item.title,
      description: item.description,
      quarter: item.quarter,
      status: item.status,
      priority: item.priority
    });
  };

  const handleSaveRoadmapItem = async () => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId || !data || !editingRoadmapItem) return;

    setIsSaving(true);
    try {
      const updatedItems = data.roadmap.map(item => 
        item.id === editingRoadmapId 
          ? { ...editingRoadmapItem }
          : { title: item.title, description: item.description, quarter: item.quarter, status: item.status, priority: item.priority }
      );
      await strategyApi.updateRoadmapItems(clientId, projectId, updatedItems);
      setEditingRoadmapId(null);
      setEditingRoadmapItem(null);
      loadData();
    } catch (error) {
      console.error('Failed to update roadmap item:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteRoadmapItem = async (itemId: string) => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId || !data) return;

    setIsSaving(true);
    try {
      const updatedItems = data.roadmap
        .filter(item => item.id !== itemId)
        .map(item => ({ title: item.title, description: item.description, quarter: item.quarter, status: item.status, priority: item.priority }));
      await strategyApi.updateRoadmapItems(clientId, projectId, updatedItems);
      loadData();
    } catch (error) {
      console.error('Failed to delete roadmap item:', error);
    } finally {
      setIsSaving(false);
    }
  };

  // Add/Edit/Delete handlers for ecosystem
  const handleAddEcosystemItem = async () => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId || !newEcosystemItem.platform) return;

    setIsSaving(true);
    try {
      await strategyApi.addEcosystemItem(clientId, projectId, newEcosystemItem);
      setNewEcosystemItem({ platform: '', purpose: '' });
      setShowAddEcosystem(false);
      loadData();
    } catch (error) {
      console.error('Failed to add ecosystem item:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleEditEcosystemItem = (item: { platform: string; purpose: string }, idx: number) => {
    setEditingEcosystemIdx(idx);
    setEditingEcosystemItem({ ...item });
  };

  const handleSaveEcosystemItem = async () => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId || !data || !editingEcosystemItem || editingEcosystemIdx === null) return;

    setIsSaving(true);
    try {
      const updatedItems = (data.ecosystem || []).map((item, idx) => 
        idx === editingEcosystemIdx 
          ? { ...editingEcosystemItem }
          : { platform: item.platform, purpose: item.purpose }
      );
      await strategyApi.updateEcosystemItems(clientId, projectId, updatedItems);
      setEditingEcosystemIdx(null);
      setEditingEcosystemItem(null);
      loadData();
    } catch (error) {
      console.error('Failed to update ecosystem item:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteEcosystemItem = async (idx: number) => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId || !data) return;

    setIsSaving(true);
    try {
      const updatedItems = (data.ecosystem || [])
        .filter((_, i) => i !== idx)
        .map(item => ({ platform: item.platform, purpose: item.purpose }));
      await strategyApi.updateEcosystemItems(clientId, projectId, updatedItems);
      loadData();
    } catch (error) {
      console.error('Failed to delete ecosystem item:', error);
    } finally {
      setIsSaving(false);
    }
  };



  const getInfluenceColor = (influence: string) => {
    switch (influence) {
      case 'high': return 'bg-purple-100 text-purple-700 border-purple-200';
      case 'medium': return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'low': return 'bg-gray-100 text-gray-700 border-gray-200';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const getAlignmentIcon = (alignment: string) => {
    switch (alignment) {
      case 'advocate': return <ThumbsUp className="w-4 h-4 text-emerald-600" />;
      case 'skeptical': return <ThumbsDown className="w-4 h-4 text-red-600" />;
      case 'neutral': return <Minus className="w-4 h-4 text-gray-500" />;
      default: return null;
    }
  };

  const getAlignmentColor = (alignment: string) => {
    switch (alignment) {
      case 'advocate': return 'bg-emerald-100 text-emerald-700 border-emerald-200';
      case 'skeptical': return 'bg-red-100 text-red-700 border-red-200';
      case 'neutral': return 'bg-gray-100 text-gray-700 border-gray-200';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const getRoadmapStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-emerald-100 text-emerald-700 border-emerald-200';
      case 'in_progress': return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'planned': return 'bg-purple-100 text-purple-700 border-purple-200';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-700 border-red-200';
      case 'medium': return 'bg-amber-100 text-amber-700 border-amber-200';
      case 'low': return 'bg-blue-100 text-blue-700 border-blue-200';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  if (isLoading) {
    return (
      <Card className="module-section">
        <CardHeader className="module-header">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-[#00c3c4]/10 flex items-center justify-center">
              <Target className="w-5 h-5 text-[#00c3c4]" />
            </div>
            <div>
              <CardTitle className="text-lg font-semibold text-gray-900">Strategy</CardTitle>
              <p className="text-sm text-gray-500">Strategy/AM Focus</p>
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
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#00c3c4] to-[#00e5e6] flex items-center justify-center">
            <Target className="w-5 h-5 text-white" />
          </div>
          <div>
            <CardTitle className="text-lg font-semibold text-gray-900">Strategy</CardTitle>
            <p className="text-sm text-gray-500">Strategy/AM Focus</p>
          </div>
        </div>
        <Button variant="ghost" size="icon">
          {isExpanded ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
        </Button>
      </CardHeader>

      {isExpanded && (
        <CardContent className="p-6">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-4 mb-6">
              <TabsTrigger value="stakeholders" className="text-sm">
                <Users className="w-4 h-4 mr-2" />
                Stakeholders
              </TabsTrigger>
              <TabsTrigger value="roadmap" className="text-sm">
                <MapIcon className="w-4 h-4 mr-2" />
                Roadmap
              </TabsTrigger>
              <TabsTrigger value="ecosystem" className="text-sm">
                <Globe className="w-4 h-4 mr-2" />
                Ecosystem
              </TabsTrigger>
              <TabsTrigger value="matrix" className="text-sm">
                <Target className="w-4 h-4 mr-2" />
                Matrix
              </TabsTrigger>
            </TabsList>

            <TabsContent value="stakeholders">
              {canEdit && (
                <div className="mb-4">
                  {!showAddStakeholder ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowAddStakeholder(true)}
                      className="flex items-center gap-2"
                    >
                      <Plus className="w-4 h-4" />
                      Add Stakeholder
                    </Button>
                  ) : (
                    <div className="p-4 bg-gray-50 rounded-lg border space-y-3">
                      <div className="grid grid-cols-2 gap-3">
                        <Input
                          placeholder="Name"
                          value={newStakeholder.name}
                          onChange={(e) => setNewStakeholder({ ...newStakeholder, name: e.target.value })}
                        />
                        <Input
                          placeholder="Role"
                          value={newStakeholder.role}
                          onChange={(e) => setNewStakeholder({ ...newStakeholder, role: e.target.value })}
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <select
                          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                          value={newStakeholder.influence}
                          onChange={(e) => setNewStakeholder({ ...newStakeholder, influence: e.target.value as 'high' | 'medium' | 'low' })}
                        >
                          <option value="high">High Influence</option>
                          <option value="medium">Medium Influence</option>
                          <option value="low">Low Influence</option>
                        </select>
                        <select
                          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                          value={newStakeholder.alignment}
                          onChange={(e) => setNewStakeholder({ ...newStakeholder, alignment: e.target.value as 'advocate' | 'neutral' | 'skeptical' })}
                        >
                          <option value="advocate">Advocate</option>
                          <option value="neutral">Neutral</option>
                          <option value="skeptical">Skeptical</option>
                        </select>
                      </div>
                      <Input
                        placeholder="Notes (optional)"
                        value={newStakeholder.notes || ''}
                        onChange={(e) => setNewStakeholder({ ...newStakeholder, notes: e.target.value })}
                      />
                      <div className="flex gap-2">
                        <Button size="sm" onClick={handleAddStakeholder} disabled={isSaving}>
                          {isSaving ? 'Adding...' : 'Add'}
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => setShowAddStakeholder(false)}>
                          Cancel
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              )}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {data.stakeholders.map((stakeholder) => (
                  <div
                    key={stakeholder.id}
                    className="p-4 rounded-xl bg-gray-50 border border-gray-100 hover:border-[#321a75]/20 transition-colors"
                  >
                    {editingStakeholderId === stakeholder.id && editingStakeholder ? (
                      // Edit mode
                      <div className="space-y-3">
                        <div className="grid grid-cols-2 gap-3">
                          <Input
                            placeholder="Name"
                            value={editingStakeholder.name}
                            onChange={(e) => setEditingStakeholder({ ...editingStakeholder, name: e.target.value })}
                          />
                          <Input
                            placeholder="Role"
                            value={editingStakeholder.role}
                            onChange={(e) => setEditingStakeholder({ ...editingStakeholder, role: e.target.value })}
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <select
                            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                            value={editingStakeholder.influence}
                            onChange={(e) => setEditingStakeholder({ ...editingStakeholder, influence: e.target.value as 'high' | 'medium' | 'low' })}
                          >
                            <option value="high">High Influence</option>
                            <option value="medium">Medium Influence</option>
                            <option value="low">Low Influence</option>
                          </select>
                          <select
                            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                            value={editingStakeholder.alignment}
                            onChange={(e) => setEditingStakeholder({ ...editingStakeholder, alignment: e.target.value as 'advocate' | 'neutral' | 'skeptical' })}
                          >
                            <option value="advocate">Advocate</option>
                            <option value="neutral">Neutral</option>
                            <option value="skeptical">Skeptical</option>
                          </select>
                        </div>
                        <Input
                          placeholder="Notes (optional)"
                          value={editingStakeholder.notes || ''}
                          onChange={(e) => setEditingStakeholder({ ...editingStakeholder, notes: e.target.value })}
                        />
                        <div className="flex gap-2">
                          <Button size="sm" onClick={handleSaveStakeholder} disabled={isSaving}>
                            <Check className="w-4 h-4 mr-1" />
                            {isSaving ? 'Saving...' : 'Save'}
                          </Button>
                          <Button size="sm" variant="outline" onClick={() => { setEditingStakeholderId(null); setEditingStakeholder(null); }}>
                            <X className="w-4 h-4 mr-1" />
                            Cancel
                          </Button>
                        </div>
                      </div>
                    ) : (
                      // View mode
                      <>
                        <div className="flex items-start justify-between">
                          <div className="flex items-start space-x-3">
                            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#321a75] to-[#00c3c4] flex items-center justify-center text-white font-medium">
                              {stakeholder.name.charAt(0)}
                            </div>
                            <div>
                              <h4 className="font-semibold text-gray-900">{stakeholder.name}</h4>
                              <p className="text-sm text-gray-500">{stakeholder.role}</p>
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            {getAlignmentIcon(stakeholder.alignment)}
                            {canEdit && (
                              <>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-8 w-8"
                                  onClick={() => handleEditStakeholder(stakeholder)}
                                >
                                  <Pencil className="w-4 h-4 text-gray-500 hover:text-[#321a75]" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-8 w-8"
                                  onClick={() => handleDeleteStakeholder(stakeholder.id)}
                                  disabled={isSaving}
                                >
                                  <Trash2 className="w-4 h-4 text-gray-500 hover:text-red-500" />
                                </Button>
                              </>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center space-x-2 mt-4">
                          <Badge variant="outline" className={cn('text-xs', getInfluenceColor(stakeholder.influence))}>
                            {stakeholder.influence} influence
                          </Badge>
                          <Badge variant="outline" className={cn('text-xs', getAlignmentColor(stakeholder.alignment))}>
                            {stakeholder.alignment}
                          </Badge>
                        </div>

                        {stakeholder.notes && (
                          <p className="text-sm text-gray-600 mt-3 pt-3 border-t border-gray-200">
                            {stakeholder.notes}
                          </p>
                        )}
                      </>
                    )}
                  </div>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="roadmap">
              {canEdit && (
                <div className="mb-4">
                  {!showAddRoadmap ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowAddRoadmap(true)}
                      className="flex items-center gap-2"
                    >
                      <Plus className="w-4 h-4" />
                      Add Roadmap Item
                    </Button>
                  ) : (
                    <div className="p-4 bg-gray-50 rounded-lg border space-y-3">
                      <Input
                        placeholder="Title"
                        value={newRoadmapItem.title}
                        onChange={(e) => setNewRoadmapItem({ ...newRoadmapItem, title: e.target.value })}
                      />
                      <Input
                        placeholder="Description"
                        value={newRoadmapItem.description}
                        onChange={(e) => setNewRoadmapItem({ ...newRoadmapItem, description: e.target.value })}
                      />
                      <div className="grid grid-cols-3 gap-3">
                        <select
                          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                          value={newRoadmapItem.status}
                          onChange={(e) => setNewRoadmapItem({ ...newRoadmapItem, status: e.target.value as 'planned' | 'in_progress' | 'completed' })}
                        >
                          <option value="planned">Planned</option>
                          <option value="in_progress">In Progress</option>
                          <option value="completed">Completed</option>
                        </select>
                        <select
                          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                          value={newRoadmapItem.priority}
                          onChange={(e) => setNewRoadmapItem({ ...newRoadmapItem, priority: e.target.value as 'high' | 'medium' | 'low' })}
                        >
                          <option value="high">High Priority</option>
                          <option value="medium">Medium Priority</option>
                          <option value="low">Low Priority</option>
                        </select>
                        <Input
                          placeholder="Quarter (e.g., Q1 2024)"
                          value={newRoadmapItem.quarter}
                          onChange={(e) => setNewRoadmapItem({ ...newRoadmapItem, quarter: e.target.value })}
                        />
                      </div>
                      <div className="flex gap-2">
                        <Button size="sm" onClick={handleAddRoadmapItem} disabled={isSaving}>
                          {isSaving ? 'Adding...' : 'Add'}
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => setShowAddRoadmap(false)}>
                          Cancel
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              )}
              <CollapsibleList
                items={data.roadmap}
                renderItem={(item) => (
                  <div
                    key={item.id}
                    className="p-4 rounded-xl bg-gray-50 border border-gray-100"
                  >
                    {editingRoadmapId === item.id && editingRoadmapItem ? (
                      // Edit mode
                      <div className="space-y-3">
                        <Input
                          placeholder="Title"
                          value={editingRoadmapItem.title}
                          onChange={(e) => setEditingRoadmapItem({ ...editingRoadmapItem, title: e.target.value })}
                        />
                        <Input
                          placeholder="Description"
                          value={editingRoadmapItem.description}
                          onChange={(e) => setEditingRoadmapItem({ ...editingRoadmapItem, description: e.target.value })}
                        />
                        <div className="grid grid-cols-3 gap-3">
                          <select
                            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                            value={editingRoadmapItem.status}
                            onChange={(e) => setEditingRoadmapItem({ ...editingRoadmapItem, status: e.target.value as 'planned' | 'in_progress' | 'completed' })}
                          >
                            <option value="planned">Planned</option>
                            <option value="in_progress">In Progress</option>
                            <option value="completed">Completed</option>
                          </select>
                          <select
                            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                            value={editingRoadmapItem.priority}
                            onChange={(e) => setEditingRoadmapItem({ ...editingRoadmapItem, priority: e.target.value as 'high' | 'medium' | 'low' })}
                          >
                            <option value="high">High Priority</option>
                            <option value="medium">Medium Priority</option>
                            <option value="low">Low Priority</option>
                          </select>
                          <Input
                            placeholder="Quarter (e.g., Q1 2024)"
                            value={editingRoadmapItem.quarter}
                            onChange={(e) => setEditingRoadmapItem({ ...editingRoadmapItem, quarter: e.target.value })}
                          />
                        </div>
                        <div className="flex gap-2">
                          <Button size="sm" onClick={handleSaveRoadmapItem} disabled={isSaving}>
                            <Check className="w-4 h-4 mr-1" />
                            {isSaving ? 'Saving...' : 'Save'}
                          </Button>
                          <Button size="sm" variant="outline" onClick={() => { setEditingRoadmapId(null); setEditingRoadmapItem(null); }}>
                            <X className="w-4 h-4 mr-1" />
                            Cancel
                          </Button>
                        </div>
                      </div>
                    ) : (
                      // View mode
                      <div className="flex items-start justify-between">
                        <div className="flex items-start space-x-4">
                          <div className={cn(
                            'w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0',
                            item.status === 'completed' && 'bg-emerald-100 text-emerald-700',
                            item.status === 'in_progress' && 'bg-blue-100 text-blue-700',
                            item.status === 'planned' && 'bg-purple-100 text-purple-700',
                          )}>
                            <Flag className="w-5 h-5" />
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center space-x-2">
                              <h4 className="font-semibold text-gray-900">{item.title}</h4>
                              <Badge variant="outline" className={cn('text-xs', getRoadmapStatusColor(item.status))}>
                                {item.status.replace('_', ' ')}
                              </Badge>
                            </div>
                            <p className="text-sm text-gray-600 mt-1">{item.description}</p>
                            <div className="flex items-center space-x-3 mt-3">
                              <Badge variant="outline" className={cn('text-xs', getPriorityColor(item.priority))}>
                                {item.priority} priority
                              </Badge>
                              <span className="text-xs text-gray-500 flex items-center">
                                <Calendar className="w-3 h-3 mr-1" />
                                {item.quarter}
                              </span>
                            </div>
                          </div>
                        </div>
                        {canEdit && (
                          <div className="flex items-center space-x-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => handleEditRoadmapItem(item)}
                            >
                              <Pencil className="w-4 h-4 text-gray-500 hover:text-[#321a75]" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => handleDeleteRoadmapItem(item.id)}
                              disabled={isSaving}
                            >
                              <Trash2 className="w-4 h-4 text-gray-500 hover:text-red-500" />
                            </Button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
                initialDisplayCount={5}
                maxHeight="400px"
              />
            </TabsContent>

            <TabsContent value="ecosystem">
              {canEdit && (
                <div className="mb-4">
                  {!showAddEcosystem ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowAddEcosystem(true)}
                      className="flex items-center gap-2"
                    >
                      <Plus className="w-4 h-4" />
                      Add Ecosystem Platform
                    </Button>
                  ) : (
                    <div className="p-4 bg-gray-50 rounded-lg border space-y-3">
                      <Input
                        placeholder="Platform name"
                        value={newEcosystemItem.platform}
                        onChange={(e) => setNewEcosystemItem({ ...newEcosystemItem, platform: e.target.value })}
                      />
                      <Input
                        placeholder="Purpose"
                        value={newEcosystemItem.purpose}
                        onChange={(e) => setNewEcosystemItem({ ...newEcosystemItem, purpose: e.target.value })}
                      />
                      <div className="flex gap-2">
                        <Button size="sm" onClick={handleAddEcosystemItem} disabled={isSaving}>
                          {isSaving ? 'Adding...' : 'Add'}
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => setShowAddEcosystem(false)}>
                          Cancel
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              )}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {(data.ecosystem || []).map((item, idx) => (
                  <div key={idx} className="p-4 rounded-xl bg-gray-50 border border-gray-100">
                    {editingEcosystemIdx === idx && editingEcosystemItem ? (
                      // Edit mode
                      <div className="space-y-3">
                        <Input
                          placeholder="Platform name"
                          value={editingEcosystemItem.platform}
                          onChange={(e) => setEditingEcosystemItem({ ...editingEcosystemItem, platform: e.target.value })}
                        />
                        <Input
                          placeholder="Purpose"
                          value={editingEcosystemItem.purpose}
                          onChange={(e) => setEditingEcosystemItem({ ...editingEcosystemItem, purpose: e.target.value })}
                        />
                        <div className="flex gap-2">
                          <Button size="sm" onClick={handleSaveEcosystemItem} disabled={isSaving}>
                            <Check className="w-4 h-4 mr-1" />
                            {isSaving ? 'Saving...' : 'Save'}
                          </Button>
                          <Button size="sm" variant="outline" onClick={() => { setEditingEcosystemIdx(null); setEditingEcosystemItem(null); }}>
                            <X className="w-4 h-4 mr-1" />
                            Cancel
                          </Button>
                        </div>
                      </div>
                    ) : (
                      // View mode
                      <div className="flex items-start space-x-3">
                        <div className="w-10 h-10 rounded-lg bg-[#00c3c4]/10 flex items-center justify-center text-[#00c3c4] flex-shrink-0">
                          <Globe className="w-5 h-5" />
                        </div>
                        <div className="flex-1">
                          <h4 className="font-semibold text-gray-900 leading-tight mb-1">{item.platform}</h4>
                          <p className="text-xs text-gray-500 leading-normal">{item.purpose}</p>
                        </div>
                        {canEdit && (
                          <div className="flex items-center space-x-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => handleEditEcosystemItem(item, idx)}
                            >
                              <Pencil className="w-4 h-4 text-gray-500 hover:text-[#321a75]" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => handleDeleteEcosystemItem(idx)}
                              disabled={isSaving}
                            >
                              <Trash2 className="w-4 h-4 text-gray-500 hover:text-red-500" />
                            </Button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
                {(!data.ecosystem || data.ecosystem.length === 0) && (
                  <div className="col-span-full py-12 text-center bg-gray-50 rounded-xl border border-dashed border-gray-200">
                    <Globe className="w-10 h-10 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500">No ecosystem platforms defined</p>
                  </div>
                )}
              </div>
            </TabsContent>


            <TabsContent value="matrix">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 bg-gray-50 p-6 rounded-2xl border border-gray-100 min-h-[450px] flex flex-col">
                  <div className="mb-6 flex items-center justify-between">
                    <div>
                      <h4 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                        <Users className="w-5 h-5 text-[#00c3c4]" />
                        Stakeholder Engagement Matrix
                      </h4>
                      <p className="text-xs text-gray-500 mt-1 italic">Mapping Influence vs. Alignment</p>
                    </div>
                  </div>
                  <div className="flex-1 min-h-0 bg-white/50 rounded-xl p-4 border border-gray-200/50">
                    <StakeholderMatrix
                      data={data.stakeholders.map(s => ({
                        name: s.name,
                        role: s.role,
                        influence: s.influence === 'high' ? 3 : s.influence === 'medium' ? 2 : 1,
                        alignment: s.alignment === 'advocate' ? 3 : s.alignment === 'neutral' ? 2 : 1
                      }))}
                    />
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-gradient-to-br from-[#00c3c4] to-[#00e5e6] text-white shadow-lg">
                    <h5 className="font-bold mb-2 flex items-center gap-2">
                      <Target className="w-4 h-4" />
                      Strategic Goal
                    </h5>
                    <p className="text-sm opacity-90 leading-relaxed">
                      Focus on moving stakeholders towards the top-right quadrant (High Influence & Advocate).
                      High influence skeptics represent the greatest risk.
                    </p>
                  </div>
                  <div className="card-shadow p-6 rounded-xl bg-white border border-[#00c3c4]/10">
                    <h5 className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-4">Sentiment Mix</h5>
                    <div className="space-y-3">
                      {[
                        { label: 'Advocates', color: 'bg-emerald-500', count: data.stakeholders.filter(s => s.alignment === 'advocate').length },
                        { label: 'Neutral', color: 'bg-gray-400', count: data.stakeholders.filter(s => s.alignment === 'neutral').length },
                        { label: 'Skeptical', color: 'bg-red-500', count: data.stakeholders.filter(s => s.alignment === 'skeptical').length },
                      ].map((item, i) => (
                        <div key={i}>
                          <div className="flex justify-between text-xs mb-1">
                            <span className="font-medium text-gray-600">{item.label}</span>
                            <span className="text-gray-400 font-bold">{Math.round((item.count / data.stakeholders.length) * 100)}%</span>
                          </div>
                          <div className="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
                            <div
                              className={`h-full ${item.color} transition-all duration-1000`}
                              style={{ width: `${(item.count / data.stakeholders.length) * 100}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
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
