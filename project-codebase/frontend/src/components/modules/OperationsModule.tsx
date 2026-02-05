import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { CollapsibleList } from '@/components/ui/collapsible-list';
import { EditButton, EditActions } from '@/components/ui/edit-controls';
import { useEditMode } from '@/hooks/useEditMode';
import { useStore } from '@/store/useStore';
import { operationsApi } from '@/services/api';
import type { OperationsData, Task, Blocker, Interaction } from '@/types';
import { NexusPieChart, NexusBarChart } from '@/components/ui/charts';
import {
  Settings,
  ChevronDown,
  ChevronUp,
  TrafficCone,
  CheckCircle2,
  Clock,
  Calendar,
  MessageSquare,
  Phone,
  Mail,
  Video,
  ArrowRight,
  AlertTriangle,
  Plus,
  X,
  Pencil,
  Trash2,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface OperationsModuleProps {
  isExpanded: boolean;
  onToggle: () => void;
}

export function OperationsModule({ isExpanded, onToggle }: OperationsModuleProps) {
  const { selectedClient, selectedProject } = useStore();
  const [data, setData] = useState<OperationsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('tasks');

  const loadData = useCallback(async () => {
    if (!selectedClient || !selectedProject) return;
    setIsLoading(true);
    try {
      // Use client_id and project_id for backend compatibility
      const clientId = selectedProject.client_id || selectedClient.id;
      const projectId = selectedProject.project_id || selectedProject.id;

      const [opsRes] = await Promise.all([
        operationsApi.get(clientId, projectId),
      ]);

      if (opsRes.success && opsRes.data) {
        setData(opsRes.data);
      }
    } catch (error) {
      console.error('Failed to load operations data:', error);
    } finally {
      setIsLoading(false);
    }
  }, [selectedClient, selectedProject]);

  // Edit mode hook
  const { editingField, canEdit, startEdit, cancelEdit, saveField, isSaving } = useEditMode({
    section: 'operations',
    onSave: loadData,
  });

  // Edit states
  const [editTrafficLight, setEditTrafficLight] = useState<{ status: string; reason: string }>({ status: '', reason: '' });
  
  // Add new item states
  const [isAddingTask, setIsAddingTask] = useState<'upcoming' | 'ongoing' | null>(null);
  const [newTask, setNewTask] = useState<{ title: string; description: string; assignee: string; due_date: string; priority: 'high' | 'medium' | 'low' }>({ title: '', description: '', assignee: '', due_date: '', priority: 'medium' });
  
  const [isAddingBlocker, setIsAddingBlocker] = useState(false);
  const [newBlocker, setNewBlocker] = useState<{ description: string; severity: 'high' | 'medium' | 'low' }>({ description: '', severity: 'medium' });
  
  const [isAddingInteraction, setIsAddingInteraction] = useState(false);
  const [newInteraction, setNewInteraction] = useState<{ date: string; type: 'meeting' | 'email' | 'call' | 'chat'; summary: string; participants: string }>({ date: new Date().toISOString().split('T')[0], type: 'meeting', summary: '', participants: '' });

  // Edit existing item states
  const [editingTaskId, setEditingTaskId] = useState<string | null>(null);
  const [editingTaskCategory, setEditingTaskCategory] = useState<'upcoming' | 'ongoing' | 'completed' | null>(null);
  const [editTask, setEditTask] = useState<{ title: string; description: string; assignee: string; due_date: string; priority: 'high' | 'medium' | 'low' }>({ title: '', description: '', assignee: '', due_date: '', priority: 'medium' });

  const [editingBlockerId, setEditingBlockerId] = useState<string | null>(null);
  const [editBlocker, setEditBlocker] = useState<{ description: string; severity: 'high' | 'medium' | 'low' }>({ description: '', severity: 'medium' });

  const [editingInteractionId, setEditingInteractionId] = useState<string | null>(null);
  const [editInteraction, setEditInteraction] = useState<{ date: string; type: 'meeting' | 'email' | 'call' | 'chat'; summary: string; participants: string }>({ date: '', type: 'meeting', summary: '', participants: '' });

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

  // Edit handlers
  const handleStartEdit = (field: string) => {
    if (!data) return;

    switch (field) {
      case 'trafficLight':
        setEditTrafficLight({ status: data.traffic_light.status, reason: data.traffic_light.reason });
        break;
    }
    startEdit(field);
  };

  const handleSave = async (field: string) => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId) return;

    await saveField(async () => {
      switch (field) {
        case 'trafficLight':
          await operationsApi.updateTrafficLight(clientId, projectId, {
            status: editTrafficLight.status as 'green' | 'yellow' | 'red',
            reason: editTrafficLight.reason,
            updated_at: new Date().toISOString(),
            updated_by: 'User',
          });
          break;
      }
    });
  };

  // Add task handler
  const handleAddTask = async () => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId || !newTask.title.trim()) return;

    try {
      await operationsApi.addTask(clientId, projectId, {
        title: newTask.title,
        description: newTask.description,
        assignee: newTask.assignee,
        due_date: newTask.due_date,
        priority: newTask.priority,
        status: isAddingTask === 'upcoming' ? 'pending' : 'in_progress',
      });
      setNewTask({ title: '', description: '', assignee: '', due_date: '', priority: 'medium' });
      setIsAddingTask(null);
      loadData();
    } catch (error) {
      console.error('Failed to add task:', error);
    }
  };

  // Add blocker handler
  const handleAddBlocker = async () => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId || !newBlocker.description.trim()) return;

    try {
      await operationsApi.addBlocker(clientId, projectId, {
        description: newBlocker.description,
        severity: newBlocker.severity,
        reported_by: 'User',
        status: 'active',
      });
      setNewBlocker({ description: '', severity: 'medium' });
      setIsAddingBlocker(false);
      loadData();
    } catch (error) {
      console.error('Failed to add blocker:', error);
    }
  };

  // Add interaction handler
  const handleAddInteraction = async () => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId || !newInteraction.summary.trim()) return;

    try {
      await operationsApi.addInteraction(clientId, projectId, {
        date: newInteraction.date,
        type: newInteraction.type,
        summary: newInteraction.summary,
        participants: newInteraction.participants.split(',').map(p => p.trim()).filter(p => p),
      });
      setNewInteraction({ date: new Date().toISOString().split('T')[0], type: 'meeting', summary: '', participants: '' });
      setIsAddingInteraction(false);
      loadData();
    } catch (error) {
      console.error('Failed to add interaction:', error);
    }
  };

  // Edit task handlers
  const handleStartEditTask = (task: Task, category: 'upcoming' | 'ongoing' | 'completed') => {
    setEditingTaskId(task.id);
    setEditingTaskCategory(category);
    setEditTask({
      title: task.title,
      description: task.description || '',
      assignee: task.assignee || '',
      due_date: task.due_date || '',
      priority: task.priority,
    });
  };

  const handleCancelEditTask = () => {
    setEditingTaskId(null);
    setEditingTaskCategory(null);
    setEditTask({ title: '', description: '', assignee: '', due_date: '', priority: 'medium' });
  };

  const handleUpdateTask = async () => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId || !editingTaskId || !editTask.title.trim()) return;

    try {
      const status = editingTaskCategory === 'upcoming' ? 'pending' : editingTaskCategory === 'ongoing' ? 'in_progress' : 'completed';
      await operationsApi.updateTask(clientId, projectId, editingTaskId, {
        title: editTask.title,
        description: editTask.description,
        assignee: editTask.assignee,
        due_date: editTask.due_date,
        priority: editTask.priority,
        status,
      });
      handleCancelEditTask();
      loadData();
    } catch (error) {
      console.error('Failed to update task:', error);
    }
  };

  const handleDeleteTask = async (taskId: string, status: string) => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId) return;

    try {
      await operationsApi.deleteTask(clientId, projectId, taskId, status);
      loadData();
    } catch (error) {
      console.error('Failed to delete task:', error);
    }
  };

  // Edit blocker handlers
  const handleStartEditBlocker = (blocker: Blocker) => {
    setEditingBlockerId(blocker.id);
    setEditBlocker({
      description: blocker.description,
      severity: blocker.severity,
    });
  };

  const handleCancelEditBlocker = () => {
    setEditingBlockerId(null);
    setEditBlocker({ description: '', severity: 'medium' });
  };

  const handleUpdateBlocker = async () => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId || !editingBlockerId || !editBlocker.description.trim()) return;

    try {
      await operationsApi.updateBlocker(clientId, projectId, editingBlockerId, {
        description: editBlocker.description,
        severity: editBlocker.severity,
        status: 'active',
      });
      handleCancelEditBlocker();
      loadData();
    } catch (error) {
      console.error('Failed to update blocker:', error);
    }
  };

  const handleDeleteBlocker = async (blockerId: string) => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId) return;

    try {
      await operationsApi.deleteBlocker(clientId, projectId, blockerId);
      loadData();
    } catch (error) {
      console.error('Failed to delete blocker:', error);
    }
  };

  const handleResolveBlocker = async (blockerId: string) => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId) return;

    try {
      await operationsApi.updateBlocker(clientId, projectId, blockerId, {
        status: 'resolved',
        resolved_at: new Date().toISOString(),
      });
      loadData();
    } catch (error) {
      console.error('Failed to resolve blocker:', error);
    }
  };

  // Edit interaction handlers
  const handleStartEditInteraction = (interaction: Interaction) => {
    setEditingInteractionId(interaction.id);
    setEditInteraction({
      date: interaction.date.split('T')[0],
      type: interaction.type,
      summary: interaction.summary,
      participants: interaction.participants.join(', '),
    });
  };

  const handleCancelEditInteraction = () => {
    setEditingInteractionId(null);
    setEditInteraction({ date: '', type: 'meeting', summary: '', participants: '' });
  };

  const handleUpdateInteraction = async () => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId || !editingInteractionId || !editInteraction.summary.trim()) return;

    try {
      await operationsApi.updateInteraction(clientId, projectId, editingInteractionId, {
        date: editInteraction.date,
        type: editInteraction.type,
        summary: editInteraction.summary,
        participants: editInteraction.participants.split(',').map(p => p.trim()).filter(p => p),
      });
      handleCancelEditInteraction();
      loadData();
    } catch (error) {
      console.error('Failed to update interaction:', error);
    }
  };

  const handleDeleteInteraction = async (interactionId: string) => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId) return;

    try {
      await operationsApi.deleteInteraction(clientId, projectId, interactionId);
      loadData();
    } catch (error) {
      console.error('Failed to delete interaction:', error);
    }
  };



  const getTrafficLightColor = (status: string) => {
    switch (status) {
      case 'green': return 'bg-emerald-500';
      case 'yellow': return 'bg-amber-500';
      case 'red': return 'bg-red-500';
      default: return 'bg-gray-400';
    }
  };

  const getTrafficLightText = (status: string) => {
    switch (status) {
      case 'green': return 'On Track';
      case 'yellow': return 'At Risk';
      case 'red': return 'Critical';
      default: return 'Unknown';
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

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'bg-red-50 border-red-200 text-red-800';
      case 'medium': return 'bg-amber-50 border-amber-200 text-amber-800';
      case 'low': return 'bg-blue-50 border-blue-200 text-blue-800';
      default: return 'bg-gray-50 border-gray-200';
    }
  };

  const getInteractionIcon = (type: string) => {
    switch (type) {
      case 'meeting': return <Video className="w-4 h-4" />;
      case 'email': return <Mail className="w-4 h-4" />;
      case 'call': return <Phone className="w-4 h-4" />;
      case 'chat': return <MessageSquare className="w-4 h-4" />;
      default: return <MessageSquare className="w-4 h-4" />;
    }
  };

  if (isLoading) {
    return (
      <Card className="module-section">
        <CardHeader className="module-header">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-[#00c3c4]/10 flex items-center justify-center">
              <Settings className="w-5 h-5 text-[#00c3c4]" />
            </div>
            <div>
              <CardTitle className="text-lg font-semibold text-gray-900">Operations & Status</CardTitle>
              <p className="text-sm text-gray-500">Tech/PM Focus</p>
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
            <Settings className="w-5 h-5 text-white" />
          </div>
          <div>
            <CardTitle className="text-lg font-semibold text-gray-900">Operations & Status</CardTitle>
            <p className="text-sm text-gray-500">Tech/PM Focus</p>
          </div>
        </div>
        <Button variant="ghost" size="icon">
          {isExpanded ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
        </Button>
      </CardHeader>

      {isExpanded && (
        <CardContent className="p-6">
          {/* Traffic Light Status */}
          <div className={cn(
            'rounded-xl p-4 mb-6 flex items-center justify-between',
            getTrafficLightColor(data.traffic_light.status),
            'bg-opacity-10'
          )}>
            <div className="flex items-center space-x-4">
              <div className={cn(
                'w-12 h-12 rounded-full flex items-center justify-center',
                getTrafficLightColor(data.traffic_light.status)
              )}>
                <TrafficCone className="w-6 h-6 text-white" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Project Status</p>
                <p className={cn(
                  'text-xl font-bold',
                  data.traffic_light.status === 'green' && 'text-emerald-700',
                  data.traffic_light.status === 'yellow' && 'text-amber-700',
                  data.traffic_light.status === 'red' && 'text-red-700',
                )}>
                  {getTrafficLightText(data.traffic_light.status)}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-sm text-gray-600">{data.traffic_light.reason}</p>
                <p className="text-xs text-gray-400 mt-1">
                  Updated by {data.traffic_light.updated_by} on {new Date(data.traffic_light.updated_at).toLocaleDateString()}
                </p>
              </div>
              {editingField === 'trafficLight' ? (
                <EditActions
                  onSave={() => handleSave('trafficLight')}
                  onCancel={cancelEdit}
                  isSaving={isSaving}
                />
              ) : (
                <EditButton onClick={() => handleStartEdit('trafficLight')} canEdit={canEdit} />
              )}
            </div>
          </div>

          {/* Main Operational Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <div className="bg-white border rounded-xl p-4 shadow-sm">
              <p className="text-sm text-gray-500 mb-1">Communication Frequency</p>
              <p className="text-lg font-bold text-emerald-600">Healthy</p>
            </div>
            <div className="bg-white border rounded-xl p-4 shadow-sm">
              <p className="text-sm text-gray-500 mb-1">Pending Actions</p>
              <p className="text-lg font-bold text-amber-600">{data.tasks.upcoming.length} Tasks</p>
            </div>
            <div className="bg-white border rounded-xl p-4 shadow-sm">
              <p className="text-sm text-gray-500 mb-1">Active Blockers</p>
              <p className="text-lg font-bold text-red-600">{data.blockers.filter(b => b.status === 'active').length}</p>
            </div>
            <div className="bg-white border rounded-xl p-4 shadow-sm">
              <p className="text-sm text-gray-500 mb-1">Last Update</p>
              <p className="text-lg font-bold text-[#321a75]">{new Date(data.traffic_light.updated_at).toLocaleDateString()}</p>
            </div>
          </div>

          {/* Traffic Light Edit Mode */}
          {editingField === 'trafficLight' && (
            <div className="mb-6 p-4 bg-gray-50 rounded-xl border border-gray-200">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                  <select
                    value={editTrafficLight.status}
                    onChange={(e) => setEditTrafficLight({ ...editTrafficLight, status: e.target.value })}
                    className="w-full h-10 px-3 border rounded-md bg-white"
                  >
                    <option value="green">Green - On Track</option>
                    <option value="yellow">Yellow - At Risk</option>
                    <option value="red">Red - Critical</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Reason</label>
                  <Input
                    value={editTrafficLight.reason}
                    onChange={(e) => setEditTrafficLight({ ...editTrafficLight, reason: e.target.value })}
                    placeholder="Reason for status..."
                  />
                </div>
              </div>
            </div>
          )}

          {/* Tabs Content */}
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-4 mb-6">
              <TabsTrigger value="tasks" className="text-sm">
                Tasks ({data.tasks.upcoming.length + data.tasks.ongoing.length + data.tasks.completed.length})
              </TabsTrigger>
              <TabsTrigger value="blockers" className="text-sm">
                Blockers ({data.blockers.filter(b => b.status === 'active').length})
              </TabsTrigger>
              <TabsTrigger value="interactions" className="text-sm">
                Interactions ({data.interactions.length})
              </TabsTrigger>
              <TabsTrigger value="overview" className="text-sm">Overview</TabsTrigger>
            </TabsList>

            <TabsContent value="tasks" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Upcoming */}
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-semibold text-gray-700 flex items-center">
                      <Clock className="w-4 h-4 mr-2 text-blue-500" />
                      Upcoming
                    </h4>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="bg-blue-50 text-blue-700">
                        {data.tasks.upcoming.length}
                      </Badge>
                      {canEdit && (
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setIsAddingTask(isAddingTask === 'upcoming' ? null : 'upcoming')}
                          className="h-6 w-6 text-blue-600 hover:bg-blue-50"
                        >
                          {isAddingTask === 'upcoming' ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
                        </Button>
                      )}
                    </div>
                  </div>
                  {/* Add Task Form - Upcoming */}
                  {isAddingTask === 'upcoming' && (
                    <div className="mb-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                      <Input
                        value={newTask.title}
                        onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
                        placeholder="Task title..."
                        className="mb-2"
                      />
                      <Input
                        value={newTask.assignee}
                        onChange={(e) => setNewTask({ ...newTask, assignee: e.target.value })}
                        placeholder="Assignee..."
                        className="mb-2"
                      />
                      <Input
                        type="date"
                        value={newTask.due_date}
                        onChange={(e) => setNewTask({ ...newTask, due_date: e.target.value })}
                        className="mb-2"
                      />
                      <select
                        value={newTask.priority}
                        onChange={(e) => setNewTask({ ...newTask, priority: e.target.value as 'high' | 'medium' | 'low' })}
                        className="w-full h-9 px-3 border rounded-md bg-white mb-2 text-sm"
                      >
                        <option value="high">High Priority</option>
                        <option value="medium">Medium Priority</option>
                        <option value="low">Low Priority</option>
                      </select>
                      <Button onClick={handleAddTask} size="sm" className="w-full bg-blue-600 hover:bg-blue-700">
                        Add Task
                      </Button>
                    </div>
                  )}
                  <CollapsibleList
                    items={data.tasks.upcoming}
                    renderItem={(task) => (
                      <TaskCard 
                        key={task.id} 
                        task={task} 
                        getPriorityColor={getPriorityColor}
                        canEdit={canEdit}
                        isEditing={editingTaskId === task.id && editingTaskCategory === 'upcoming'}
                        editTask={editTask}
                        setEditTask={setEditTask}
                        onStartEdit={() => handleStartEditTask(task, 'upcoming')}
                        onCancelEdit={handleCancelEditTask}
                        onSave={handleUpdateTask}
                        onDelete={() => handleDeleteTask(task.id, 'pending')}
                      />
                    )}
                    initialDisplayCount={4}
                    maxHeight="300px"
                  />
                </div>

                {/* Ongoing */}
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-semibold text-gray-700 flex items-center">
                      <ArrowRight className="w-4 h-4 mr-2 text-amber-500" />
                      Ongoing
                    </h4>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="bg-amber-50 text-amber-700">
                        {data.tasks.ongoing.length}
                      </Badge>
                      {canEdit && (
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setIsAddingTask(isAddingTask === 'ongoing' ? null : 'ongoing')}
                          className="h-6 w-6 text-amber-600 hover:bg-amber-50"
                        >
                          {isAddingTask === 'ongoing' ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
                        </Button>
                      )}
                    </div>
                  </div>
                  {/* Add Task Form - Ongoing */}
                  {isAddingTask === 'ongoing' && (
                    <div className="mb-3 p-3 bg-amber-50 rounded-lg border border-amber-200">
                      <Input
                        value={newTask.title}
                        onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
                        placeholder="Task title..."
                        className="mb-2"
                      />
                      <Input
                        value={newTask.assignee}
                        onChange={(e) => setNewTask({ ...newTask, assignee: e.target.value })}
                        placeholder="Assignee..."
                        className="mb-2"
                      />
                      <Input
                        type="date"
                        value={newTask.due_date}
                        onChange={(e) => setNewTask({ ...newTask, due_date: e.target.value })}
                        className="mb-2"
                      />
                      <select
                        value={newTask.priority}
                        onChange={(e) => setNewTask({ ...newTask, priority: e.target.value as 'high' | 'medium' | 'low' })}
                        className="w-full h-9 px-3 border rounded-md bg-white mb-2 text-sm"
                      >
                        <option value="high">High Priority</option>
                        <option value="medium">Medium Priority</option>
                        <option value="low">Low Priority</option>
                      </select>
                      <Button onClick={handleAddTask} size="sm" className="w-full bg-amber-600 hover:bg-amber-700">
                        Add Task
                      </Button>
                    </div>
                  )}
                  <CollapsibleList
                    items={data.tasks.ongoing}
                    renderItem={(task) => (
                      <TaskCard 
                        key={task.id} 
                        task={task} 
                        getPriorityColor={getPriorityColor}
                        canEdit={canEdit}
                        isEditing={editingTaskId === task.id && editingTaskCategory === 'ongoing'}
                        editTask={editTask}
                        setEditTask={setEditTask}
                        onStartEdit={() => handleStartEditTask(task, 'ongoing')}
                        onCancelEdit={handleCancelEditTask}
                        onSave={handleUpdateTask}
                        onDelete={() => handleDeleteTask(task.id, 'in_progress')}
                      />
                    )}
                    initialDisplayCount={4}
                    maxHeight="300px"
                  />
                </div>

                {/* Completed */}
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-semibold text-gray-700 flex items-center">
                      <CheckCircle2 className="w-4 h-4 mr-2 text-emerald-500" />
                      Completed
                    </h4>
                    <Badge variant="secondary" className="bg-emerald-50 text-emerald-700">
                      {data.tasks.completed.length}
                    </Badge>
                  </div>
                  <CollapsibleList
                    items={data.tasks.completed}
                    renderItem={(task) => (
                      <TaskCard 
                        key={task.id} 
                        task={task} 
                        getPriorityColor={getPriorityColor}
                        canEdit={canEdit}
                        isEditing={editingTaskId === task.id && editingTaskCategory === 'completed'}
                        editTask={editTask}
                        setEditTask={setEditTask}
                        onStartEdit={() => handleStartEditTask(task, 'completed')}
                        onCancelEdit={handleCancelEditTask}
                        onSave={handleUpdateTask}
                        onDelete={() => handleDeleteTask(task.id, 'completed')}
                      />
                    )}
                    initialDisplayCount={4}
                    maxHeight="300px"
                  />
                </div>
              </div>
            </TabsContent>

            <TabsContent value="blockers">
              {/* Add Blocker Button */}
              {canEdit && (
                <div className="mb-4">
                  <Button
                    variant="outline"
                    onClick={() => setIsAddingBlocker(!isAddingBlocker)}
                    className="text-red-600 border-red-200 hover:bg-red-50"
                  >
                    {isAddingBlocker ? <X className="w-4 h-4 mr-2" /> : <Plus className="w-4 h-4 mr-2" />}
                    {isAddingBlocker ? 'Cancel' : 'Add Blocker'}
                  </Button>
                </div>
              )}
              
              {/* Add Blocker Form */}
              {isAddingBlocker && (
                <div className="mb-4 p-4 bg-red-50 rounded-xl border border-red-200">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                      <Input
                        value={newBlocker.description}
                        onChange={(e) => setNewBlocker({ ...newBlocker, description: e.target.value })}
                        placeholder="Describe the blocker..."
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Severity</label>
                      <select
                        value={newBlocker.severity}
                        onChange={(e) => setNewBlocker({ ...newBlocker, severity: e.target.value as 'high' | 'medium' | 'low' })}
                        className="w-full h-10 px-3 border rounded-md bg-white"
                      >
                        <option value="high">High</option>
                        <option value="medium">Medium</option>
                        <option value="low">Low</option>
                      </select>
                    </div>
                  </div>
                  <Button onClick={handleAddBlocker} size="sm" className="mt-3 bg-red-600 hover:bg-red-700">
                    Add Blocker
                  </Button>
                </div>
              )}

              {data.blockers.filter(b => b.status === 'active').length === 0 && !isAddingBlocker ? (
                <div className="text-center py-8 text-gray-500">
                  <CheckCircle2 className="w-12 h-12 mx-auto mb-3 text-emerald-500" />
                  <p>No active blockers</p>
                </div>
              ) : data.blockers.filter(b => b.status === 'active').length > 0 ? (
                <CollapsibleList
                  items={data.blockers.filter(b => b.status === 'active')}
                  renderItem={(blocker) => (
                    editingBlockerId === blocker.id ? (
                      <div key={blocker.id} className="p-4 bg-red-50 rounded-xl border border-red-200">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                            <Input
                              value={editBlocker.description}
                              onChange={(e) => setEditBlocker({ ...editBlocker, description: e.target.value })}
                              placeholder="Describe the blocker..."
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Severity</label>
                            <select
                              value={editBlocker.severity}
                              onChange={(e) => setEditBlocker({ ...editBlocker, severity: e.target.value as 'high' | 'medium' | 'low' })}
                              className="w-full h-10 px-3 border rounded-md bg-white"
                            >
                              <option value="high">High</option>
                              <option value="medium">Medium</option>
                              <option value="low">Low</option>
                            </select>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button onClick={handleUpdateBlocker} size="sm" className="bg-[#321a75] hover:bg-[#4a2d99]">
                            Save
                          </Button>
                          <Button onClick={handleCancelEditBlocker} size="sm" variant="outline">
                            Cancel
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div
                        key={blocker.id}
                        className={cn(
                          'p-4 rounded-xl border group',
                          getSeverityColor(blocker.severity)
                        )}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-start space-x-3 flex-1">
                            <AlertTriangle className="w-5 h-5 mt-0.5 flex-shrink-0" />
                            <div>
                              <p className="font-medium">{blocker.description}</p>
                              <div className="flex items-center space-x-3 mt-2 text-sm opacity-80">
                                <span>Reported by {blocker.reported_by}</span>
                                <span>•</span>
                                <span>{new Date(blocker.reported_at).toLocaleDateString()}</span>
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="capitalize">
                              {blocker.severity}
                            </Badge>
                            {canEdit && (
                              <div className="hidden group-hover:flex items-center gap-1">
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => handleResolveBlocker(blocker.id)}
                                  className="h-7 w-7 text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50"
                                  title="Mark as Resolved"
                                >
                                  <CheckCircle2 className="w-4 h-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => handleStartEditBlocker(blocker)}
                                  className="h-7 w-7 text-gray-500 hover:text-[#321a75] hover:bg-[#321a75]/10"
                                >
                                  <Pencil className="w-4 h-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => handleDeleteBlocker(blocker.id)}
                                  className="h-7 w-7 text-gray-500 hover:text-red-600 hover:bg-red-50"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )
                  )}
                  initialDisplayCount={3}
                  maxHeight="400px"
                />
              ) : null}
            </TabsContent>

            <TabsContent value="interactions">
              {/* Add Interaction Button */}
              {canEdit && (
                <div className="mb-4">
                  <Button
                    variant="outline"
                    onClick={() => setIsAddingInteraction(!isAddingInteraction)}
                    className="text-[#321a75] border-[#321a75]/20 hover:bg-[#321a75]/5"
                  >
                    {isAddingInteraction ? <X className="w-4 h-4 mr-2" /> : <Plus className="w-4 h-4 mr-2" />}
                    {isAddingInteraction ? 'Cancel' : 'Add Interaction'}
                  </Button>
                </div>
              )}
              
              {/* Add Interaction Form */}
              {isAddingInteraction && (
                <div className="mb-4 p-4 bg-[#321a75]/5 rounded-xl border border-[#321a75]/20">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                      <select
                        value={newInteraction.type}
                        onChange={(e) => setNewInteraction({ ...newInteraction, type: e.target.value as 'meeting' | 'email' | 'call' | 'chat' })}
                        className="w-full h-10 px-3 border rounded-md bg-white"
                      >
                        <option value="meeting">Meeting</option>
                        <option value="email">Email</option>
                        <option value="call">Call</option>
                        <option value="chat">Chat</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
                      <Input
                        type="date"
                        value={newInteraction.date}
                        onChange={(e) => setNewInteraction({ ...newInteraction, date: e.target.value })}
                      />
                    </div>
                  </div>
                  <div className="mb-3">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Summary</label>
                    <Input
                      value={newInteraction.summary}
                      onChange={(e) => setNewInteraction({ ...newInteraction, summary: e.target.value })}
                      placeholder="Brief summary of the interaction..."
                    />
                  </div>
                  <div className="mb-3">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Participants (comma-separated)</label>
                    <Input
                      value={newInteraction.participants}
                      onChange={(e) => setNewInteraction({ ...newInteraction, participants: e.target.value })}
                      placeholder="John Doe, Jane Smith..."
                    />
                  </div>
                  <Button onClick={handleAddInteraction} size="sm" className="bg-[#321a75] hover:bg-[#4a2d99]">
                    Add Interaction
                  </Button>
                </div>
              )}
              <CollapsibleList
                items={data.interactions}
                renderItem={(interaction) => (
                  editingInteractionId === interaction.id ? (
                    <div key={interaction.id} className="p-4 bg-[#321a75]/5 rounded-xl border border-[#321a75]/20">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                          <select
                            value={editInteraction.type}
                            onChange={(e) => setEditInteraction({ ...editInteraction, type: e.target.value as 'meeting' | 'email' | 'call' | 'chat' })}
                            className="w-full h-10 px-3 border rounded-md bg-white"
                          >
                            <option value="meeting">Meeting</option>
                            <option value="email">Email</option>
                            <option value="call">Call</option>
                            <option value="chat">Chat</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
                          <Input
                            type="date"
                            value={editInteraction.date}
                            onChange={(e) => setEditInteraction({ ...editInteraction, date: e.target.value })}
                          />
                        </div>
                      </div>
                      <div className="mb-3">
                        <label className="block text-sm font-medium text-gray-700 mb-1">Summary</label>
                        <Input
                          value={editInteraction.summary}
                          onChange={(e) => setEditInteraction({ ...editInteraction, summary: e.target.value })}
                          placeholder="Brief summary of the interaction..."
                        />
                      </div>
                      <div className="mb-3">
                        <label className="block text-sm font-medium text-gray-700 mb-1">Participants (comma-separated)</label>
                        <Input
                          value={editInteraction.participants}
                          onChange={(e) => setEditInteraction({ ...editInteraction, participants: e.target.value })}
                          placeholder="John Doe, Jane Smith..."
                        />
                      </div>
                      <div className="flex gap-2">
                        <Button onClick={handleUpdateInteraction} size="sm" className="bg-[#321a75] hover:bg-[#4a2d99]">
                          Save
                        </Button>
                        <Button onClick={handleCancelEditInteraction} size="sm" variant="outline">
                          Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div
                      key={interaction.id}
                      className="p-4 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors group"
                    >
                      <div className="flex items-start space-x-3">
                        <div className="w-10 h-10 rounded-lg bg-[#321a75]/10 flex items-center justify-center flex-shrink-0">
                          {getInteractionIcon(interaction.type)}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <Badge variant="outline" className="capitalize text-xs">
                              {interaction.type}
                            </Badge>
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-gray-500">{interaction.date}</span>
                              {canEdit && (
                                <div className="hidden group-hover:flex items-center gap-1">
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    onClick={() => handleStartEditInteraction(interaction)}
                                    className="h-6 w-6 text-gray-500 hover:text-[#321a75] hover:bg-[#321a75]/10"
                                  >
                                    <Pencil className="w-3 h-3" />
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    onClick={() => handleDeleteInteraction(interaction.id)}
                                    className="h-6 w-6 text-gray-500 hover:text-red-600 hover:bg-red-50"
                                  >
                                    <Trash2 className="w-3 h-3" />
                                  </Button>
                                </div>
                              )}
                            </div>
                          </div>
                          <p className="mt-2 text-sm text-gray-700">{interaction.summary}</p>
                          <p className="mt-1 text-xs text-gray-500">
                            Participants: {interaction.participants.join(', ')}
                          </p>
                        </div>
                      </div>
                    </div>
                  )
                )}
                initialDisplayCount={5}
                maxHeight="400px"
              />
            </TabsContent>

            <TabsContent value="overview">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="bg-gray-50 p-6 rounded-2xl border border-gray-100 flex flex-col justify-center">
                  <h4 className="text-lg font-semibold text-gray-900 mb-6 flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                    Task Progress Distribution
                  </h4>
                  <NexusPieChart
                    data={[
                      { name: 'Completed', value: data.tasks.completed.length },
                      { name: 'Ongoing', value: data.tasks.ongoing.length },
                      { name: 'Upcoming', value: data.tasks.upcoming.length },
                    ].filter(d => d.value > 0)}
                  />
                  <div className="mt-4 text-center">
                    <p className="text-sm text-gray-500 italic">
                      Overall Completion: {Math.round((data.tasks.completed.length / Math.max(1, data.tasks.completed.length + data.tasks.ongoing.length + data.tasks.upcoming.length)) * 100)}%
                    </p>
                  </div>
                </div>

                <div className="bg-gray-50 p-6 rounded-2xl border border-gray-100 flex flex-col justify-center">
                  <h4 className="text-lg font-semibold text-gray-900 mb-6 flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-red-500" />
                    Blocker Severity Profile
                  </h4>
                  <NexusBarChart
                    data={[
                      { name: 'High', value: data.blockers.filter(b => b.severity === 'high').length },
                      { name: 'Medium', value: data.blockers.filter(b => b.severity === 'medium').length },
                      { name: 'Low', value: data.blockers.filter(b => b.severity === 'low').length },
                    ]}
                    color="#ef4444"
                    label="Count"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
                <div className="text-center p-4 bg-blue-50 rounded-xl border border-blue-100">
                  <p className="text-3xl font-bold text-blue-700">{data.tasks.upcoming.length}</p>
                  <p className="text-xs text-blue-600 uppercase font-bold tracking-widest mt-1">Upcoming</p>
                </div>
                <div className="text-center p-4 bg-amber-50 rounded-xl border border-amber-100">
                  <p className="text-3xl font-bold text-amber-700">{data.tasks.ongoing.length}</p>
                  <p className="text-xs text-amber-600 uppercase font-bold tracking-widest mt-1">Ongoing</p>
                </div>
                <div className="text-center p-4 bg-emerald-50 rounded-xl border border-emerald-100">
                  <p className="text-3xl font-bold text-emerald-700">{data.tasks.completed.length}</p>
                  <p className="text-xs text-emerald-600 uppercase font-bold tracking-widest mt-1">Completed</p>
                </div>
                <div className="text-center p-4 bg-red-50 rounded-xl border border-red-100">
                  <p className="text-3xl font-bold text-red-700">{data.blockers.filter(b => b.status === 'active').length}</p>
                  <p className="text-xs text-red-600 uppercase font-bold tracking-widest mt-1">Blockers</p>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      )}
    </Card>
  );
}

function TaskCard({ 
  task, 
  getPriorityColor,
  canEdit,
  isEditing,
  editTask,
  setEditTask,
  onStartEdit,
  onCancelEdit,
  onSave,
  onDelete,
}: { 
  task: Task; 
  getPriorityColor: (p: string) => string;
  canEdit: boolean;
  isEditing: boolean;
  editTask: { title: string; description: string; assignee: string; due_date: string; priority: 'high' | 'medium' | 'low' };
  setEditTask: (task: { title: string; description: string; assignee: string; due_date: string; priority: 'high' | 'medium' | 'low' }) => void;
  onStartEdit: () => void;
  onCancelEdit: () => void;
  onSave: () => void;
  onDelete: () => void;
}) {
  if (isEditing) {
    return (
      <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
        <Input
          value={editTask.title}
          onChange={(e) => setEditTask({ ...editTask, title: e.target.value })}
          placeholder="Task title..."
          className="mb-2"
        />
        <Input
          value={editTask.assignee}
          onChange={(e) => setEditTask({ ...editTask, assignee: e.target.value })}
          placeholder="Assignee..."
          className="mb-2"
        />
        <Input
          type="date"
          value={editTask.due_date}
          onChange={(e) => setEditTask({ ...editTask, due_date: e.target.value })}
          className="mb-2"
        />
        <select
          value={editTask.priority}
          onChange={(e) => setEditTask({ ...editTask, priority: e.target.value as 'high' | 'medium' | 'low' })}
          className="w-full h-9 px-3 border rounded-md bg-white mb-2 text-sm"
        >
          <option value="high">High Priority</option>
          <option value="medium">Medium Priority</option>
          <option value="low">Low Priority</option>
        </select>
        <div className="flex gap-2">
          <Button onClick={onSave} size="sm" className="flex-1 bg-[#321a75] hover:bg-[#4a2d99]">
            Save
          </Button>
          <Button onClick={onCancelEdit} size="sm" variant="outline" className="flex-1">
            Cancel
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-3 bg-white rounded-lg border border-gray-200 hover:border-[#321a75]/30 hover:shadow-sm transition-all group">
      <div className="flex items-start justify-between mb-2">
        <p className="font-medium text-sm text-gray-900 line-clamp-2 flex-1">{task.title}</p>
        <div className="flex items-center gap-1">
          <Badge variant="outline" className={cn('text-xs capitalize', getPriorityColor(task.priority))}>
            {task.priority}
          </Badge>
          {canEdit && (
            <div className="hidden group-hover:flex items-center gap-1 ml-1">
              <Button
                variant="ghost"
                size="icon"
                onClick={(e) => { e.stopPropagation(); onStartEdit(); }}
                className="h-6 w-6 text-gray-500 hover:text-[#321a75] hover:bg-[#321a75]/10"
              >
                <Pencil className="w-3 h-3" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={(e) => { e.stopPropagation(); onDelete(); }}
                className="h-6 w-6 text-gray-500 hover:text-red-600 hover:bg-red-50"
              >
                <Trash2 className="w-3 h-3" />
              </Button>
            </div>
          )}
        </div>
      </div>
      {task.assignee && (
        <p className="text-xs text-gray-500 mb-1">Assigned to: {task.assignee}</p>
      )}
      {task.due_date && (
        <div className="flex items-center text-xs text-gray-400">
          <Calendar className="w-3 h-3 mr-1" />
          Due: {task.due_date}
        </div>
      )}
    </div>
  );
}
