import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { EditButton, EditActions } from '@/components/ui/edit-controls';
import { useEditMode } from '@/hooks/useEditMode';
import { useStore } from '@/store/useStore';
import { universalContextApi } from '@/services/api';
import type { UniversalContext, POCContact, User } from '@/types';
import {
  Globe,
  Users,
  Phone,
  Mail,
  Calendar,
  MessageSquare,
  Clock,
  ChevronDown,
  ChevronUp,
  Building2,
  Star,
  History,
  Plus,
  Trash2,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface UniversalContextModuleProps {
  isExpanded: boolean;
  onToggle: () => void;
}

export function UniversalContextModule({ isExpanded, onToggle }: UniversalContextModuleProps) {
  const { selectedClient, selectedProject } = useStore();
  const [data, setData] = useState<UniversalContext | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [allUsers, setAllUsers] = useState<User[]>([]);
  const [openUserSelect, setOpenUserSelect] = useState(false);
  const [userSearchQuery, setUserSearchQuery] = useState('');

  const loadData = useCallback(async () => {
    if (!selectedClient || !selectedProject) return;
    setIsLoading(true);
    try {
      // Use client_id and project_id for backend compatibility
      const clientId = selectedProject.client_id || selectedClient.id;
      const projectId = selectedProject.project_id || selectedProject.id;

      const response = await universalContextApi.get(clientId, projectId);
      if (response.success && response.data) {
        setData(response.data);
      }
    } catch (error) {
      console.error('Failed to load universal context:', error);
    } finally {
      setIsLoading(false);
    }
  }, [selectedClient, selectedProject]);

  // Edit mode hook
  const { editingField, canEdit, startEdit, cancelEdit, saveField, isSaving } = useEditMode({
    section: 'universal',
    onSave: loadData,
  });

  // Edit states
  const [editSummary, setEditSummary] = useState('');
  const [editPocMap, setEditPocMap] = useState<POCContact[]>([]);
  const [newNote, setNewNote] = useState('');
  const [newWorkspaceItem, setNewWorkspaceItem] = useState('');
  const [editClientProfile, setEditClientProfile] = useState<UniversalContext['client_profile'] | null>(null);
  const [editWorkspace, setEditWorkspace] = useState<string[]>([]);
  const [editSquad, setEditSquad] = useState<UniversalContext['internal_squad']>([]);
  const [editHygiene, setEditHygiene] = useState<UniversalContext['communication_hygiene'] | null>(null);
  const [editTimeline, setEditTimeline] = useState<UniversalContext['timeline']>([]);
  const [editNotes, setEditNotes] = useState<string[]>([]);

  useEffect(() => {
    if (selectedClient && selectedProject) {
      loadData();
    }
  }, [selectedClient, selectedProject, loadData]);

  useEffect(() => {
    const loadUsers = async () => {
      const result = await universalContextApi.getUsers();
      if (result.success && result.data) {
        setAllUsers(result.data);
      }
    };
    loadUsers();
  }, []);

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
      case 'summary':
        setEditSummary(data.ai_summary);
        break;
      case 'poc':
        setEditPocMap([...data.poc_map]);
        break;
      case 'client_profile':
        setEditClientProfile({ ...data.client_profile });
        break;
      case 'workspace':
        setEditWorkspace([...data.google_workspace]);
        break;
      case 'squad':
        setEditSquad([...data.internal_squad]);
        break;
      case 'hygiene':
        setEditHygiene({ ...data.communication_hygiene });
        break;
      case 'timeline':
        setEditTimeline([...data.timeline]);
        break;
      case 'notes':
        setEditNotes([...data.important_notes]);
        break;
    }
    startEdit(field);
  };

  const handleSave = async (field: string) => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId) return;

    await saveField(async () => {
      switch (field) {
        case 'summary':
          await universalContextApi.updateSummary(clientId, projectId, editSummary);
          break;
        case 'squad':
          await universalContextApi.updateSquad(clientId, projectId, editSquad);
          break;
        case 'poc':
          // POC update logic
          break;
        case 'client_profile':
          if (editClientProfile) {
            await universalContextApi.updateClientProfile(clientId, projectId, editClientProfile);
          }
          break;
        case 'workspace':
          await universalContextApi.addGoogleWorkspace(clientId, projectId, editWorkspace);
          break;
        case 'hygiene':
          if (editHygiene) {
            await universalContextApi.updateHygiene(clientId, projectId, editHygiene);
          }
          break;
        case 'timeline':
          await universalContextApi.updateTimeline(clientId, projectId, editTimeline);
          break;
        case 'notes':
          await universalContextApi.updateImportantNotes(clientId, projectId, editNotes);
          break;
      }
    });
  };

  const handleAddSquadMember = async (user: User) => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId) return;

    const result = await universalContextApi.addSquadMember(clientId, projectId, {
      name: user.name,
      email: user.email,
      role: user.job_title || user.role,
      department: user.department || 'Engineering',
    });

    if (result.success) {
      setOpenUserSelect(false);
      setUserSearchQuery('');
      await loadData();
    }
  };

  const handleAddNote = async () => {
    if (!newNote.trim()) return;
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId) return;

    const result = await universalContextApi.addImportantNote(clientId, projectId, newNote);
    if (result.success) {
      setNewNote('');
      await loadData();
    }
  };

  const getHygieneStatusColor = (status: string) => {
    switch (status) {
      case 'excellent': return 'text-emerald-600 bg-emerald-50';
      case 'good': return 'text-blue-600 bg-blue-50';
      case 'needs_attention': return 'text-amber-600 bg-amber-50';
      case 'critical': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  if (isLoading) {
    return (
      <Card className="module-section">
        <CardHeader className="module-header">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-[#321a75]/10 flex items-center justify-center">
              <Globe className="w-5 h-5 text-[#321a75]" />
            </div>
            <div>
              <CardTitle className="text-lg font-semibold text-gray-900">Universal Context</CardTitle>
              <p className="text-sm text-gray-500">Visible to All</p>
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
            <Globe className="w-5 h-5 text-white" />
          </div>
          <div>
            <CardTitle className="text-lg font-semibold text-gray-900">Universal Context</CardTitle>
            <p className="text-sm text-gray-500">Visible to All</p>
          </div>
        </div>
        <Button variant="ghost" size="icon">
          {isExpanded ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
        </Button>
      </CardHeader>

      {isExpanded && (
        <CardContent className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Client Profile */}
            <div className="lg:col-span-1 space-y-4">
              <div className="bg-gradient-to-br from-[#321a75]/5 to-[#00c3c4]/5 rounded-xl p-5 border border-[#321a75]/10">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-bold text-gray-900">Client Profile</h3>
                  </div>
                  {editingField === 'client_profile' ? (
                    <EditActions
                      onSave={() => handleSave('client_profile')}
                      onCancel={cancelEdit}
                      isSaving={isSaving}
                    />
                  ) : (
                    <EditButton onClick={() => handleStartEdit('client_profile')} canEdit={canEdit} />
                  )}
                </div>

                {editingField === 'client_profile' && editClientProfile ? (
                  <div className="space-y-3">
                    <div>
                      <label className="text-sm text-gray-500">Company Name</label>
                      <Input
                        value={editClientProfile.name}
                        onChange={(e) => setEditClientProfile({ ...editClientProfile, name: e.target.value })}
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <label className="text-sm text-gray-500">Industry</label>
                      <Input
                        value={editClientProfile.industry}
                        onChange={(e) => setEditClientProfile({ ...editClientProfile, industry: e.target.value })}
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <label className="text-sm text-gray-500">Account Tier</label>
                      <select
                        value={editClientProfile.account_tier}
                        onChange={(e) => setEditClientProfile({ ...editClientProfile, account_tier: e.target.value as any })}
                        className="w-full mt-1 h-10 px-3 text-sm border rounded-md bg-white"
                      >
                        <option value="enterprise">Enterprise</option>
                        <option value="premium">Premium</option>
                        <option value="standard">Standard</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-sm text-gray-500">Account Manager</label>
                      <Input
                        value={editClientProfile.account_manager}
                        onChange={(e) => setEditClientProfile({ ...editClientProfile, account_manager: e.target.value })}
                        className="mt-1"
                      />
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h4 className="text-lg font-semibold text-gray-900">{data.client_profile.name}</h4>
                        <div className="flex items-center space-x-2 mt-1">
                          <Building2 className="w-4 h-4 text-gray-400" />
                          <span className="text-sm text-gray-600">{data.client_profile.industry}</span>
                        </div>
                      </div>
                      <Badge
                        variant="secondary"
                        className={cn(
                          'capitalize',
                          data.client_profile.account_tier === 'enterprise' && 'bg-purple-100 text-purple-700',
                          data.client_profile.account_tier === 'premium' && 'bg-blue-100 text-blue-700',
                          data.client_profile.account_tier === 'standard' && 'bg-gray-100 text-gray-700',
                        )}
                      >
                        {data.client_profile.account_tier}
                      </Badge>
                    </div>

                    <div className="space-y-3">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-500">Account Manager</span>
                        <span className="font-medium text-gray-900">{data.client_profile.account_manager}</span>
                      </div>

                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-500">Contract Period</span>
                        <span className="font-medium text-gray-900">
                          {data.client_profile.contract_start ? new Date(data.client_profile.contract_start).getFullYear() : 'N/A'}
                        </span>
                      </div>
                    </div>
                  </>
                )}
              </div>

              {/* Project Summary */}
              <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <Globe className="w-4 h-4 text-[#321a75]" />
                    <h4 className="font-semibold text-gray-900">Project Summary</h4>
                  </div>
                  {editingField === 'summary' ? (
                    <EditActions
                      onSave={() => handleSave('summary')}
                      onCancel={cancelEdit}
                      isSaving={isSaving}
                    />
                  ) : (
                    <EditButton onClick={() => handleStartEdit('summary')} canEdit={canEdit} />
                  )}
                </div>
                {editingField === 'summary' ? (
                  <Textarea
                    value={editSummary}
                    onChange={(e) => setEditSummary(e.target.value)}
                    className="w-full min-h-[100px] text-sm"
                    placeholder="Enter project summary..."
                  />
                ) : (
                  <p className="text-sm text-gray-600 leading-relaxed">{data.ai_summary || "No summary provided."}</p>
                )}
              </div>
              {/* Google Workspace */}
              <div className="bg-blue-50 rounded-xl border border-blue-200 p-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-gray-900 flex items-center">
                    <Globe className="w-4 h-4 mr-2 text-blue-600" />
                    Google Workspace
                  </h4>
                  {editingField === 'workspace' ? (
                    <EditActions
                      onSave={() => handleSave('workspace')}
                      onCancel={cancelEdit}
                      isSaving={isSaving}
                    />
                  ) : (
                    <EditButton onClick={() => handleStartEdit('workspace')} canEdit={canEdit} />
                  )}
                </div>
                {editingField === 'workspace' ? (
                  <div className="space-y-2">
                    {editWorkspace.map((item, idx) => (
                      <div key={idx} className="flex items-center gap-2">
                        <Input
                          value={item}
                          onChange={(e) => {
                            const updated = [...editWorkspace];
                            updated[idx] = e.target.value;
                            setEditWorkspace(updated);
                          }}
                          className="flex-1 h-8 text-sm"
                        />
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-red-500 hover:text-red-700 hover:bg-red-50"
                          onClick={() => setEditWorkspace(editWorkspace.filter((_, i) => i !== idx))}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                    <div className="flex gap-2">
                      <Input
                        value={newWorkspaceItem}
                        onChange={(e) => setNewWorkspaceItem(e.target.value)}
                        placeholder="Add workspace link..."
                        className="flex-1 h-8 text-sm"
                        onKeyPress={(e) => {
                          if (e.key === 'Enter' && newWorkspaceItem.trim()) {
                            setEditWorkspace([...editWorkspace, newWorkspaceItem.trim()]);
                            setNewWorkspaceItem('');
                          }
                        }}
                      />
                      <Button
                        size="sm"
                        onClick={() => {
                          if (newWorkspaceItem.trim()) {
                            setEditWorkspace([...editWorkspace, newWorkspaceItem.trim()]);
                            setNewWorkspaceItem('');
                          }
                        }}
                        className="h-8"
                      >
                        <Plus className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {data.google_workspace.length === 0 ? (
                      <p className="text-sm text-gray-500 italic">No workspace links yet</p>
                    ) : (
                      data.google_workspace.map((item, idx) => (
                        <div key={idx} className="text-sm text-blue-700 hover:text-blue-900 cursor-pointer truncate">
                          {item}
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>
            </div>



            {/* Internal Squad & POC Map */}
            <div className="lg:col-span-1 space-y-4">
              {/* Internal Squad */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-gray-900 flex items-center">
                    <Users className="w-4 h-4 mr-2 text-[#00c3c4]" />
                    Internal Squad
                  </h4>
                  <div className="flex items-center gap-2">
                    {editingField === 'squad' ? (
                      <EditActions
                        onSave={() => handleSave('squad')}
                        onCancel={cancelEdit}
                        isSaving={isSaving}
                      />
                    ) : (
                      <EditButton onClick={() => handleStartEdit('squad')} canEdit={canEdit} />
                    )}
                  </div>
                </div>
                {editingField === 'squad' ? (
                  <div className="space-y-2 mb-3">
                    {editSquad.map((member, idx) => (
                      <div key={member.id || idx} className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg">
                        <Avatar className="w-8 h-8">
                          <AvatarImage src={member.avatar} />
                          <AvatarFallback className="text-xs bg-gradient-to-br from-[#321a75] to-[#00c3c4] text-white">
                            {member.name.charAt(0)}
                          </AvatarFallback>
                        </Avatar>
                        <Input
                          value={member.name}
                          onChange={(e) => {
                            const updated = [...editSquad];
                            updated[idx] = { ...member, name: e.target.value };
                            setEditSquad(updated);
                          }}
                          placeholder="Name"
                          className="flex-1 h-8 text-sm"
                        />
                        <Input
                          value={member.role}
                          onChange={(e) => {
                            const updated = [...editSquad];
                            updated[idx] = { ...member, role: e.target.value };
                            setEditSquad(updated);
                          }}
                          placeholder="Role"
                          className="flex-1 h-8 text-sm"
                        />
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-red-500 hover:text-red-700 hover:bg-red-50"
                          onClick={() => setEditSquad(editSquad.filter((_, i) => i !== idx))}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                    <div className="relative">
                      <Input
                        type="text"
                        placeholder="Search and add user..."
                        value={userSearchQuery}
                        onChange={(e) => {
                          setUserSearchQuery(e.target.value);
                          setOpenUserSelect(true);
                        }}
                        onFocus={() => setOpenUserSelect(true)}
                        onBlur={() => setTimeout(() => setOpenUserSelect(false), 200)}
                        className="h-9 text-sm"
                      />
                      {openUserSelect && userSearchQuery && (
                        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                          {allUsers
                            .filter(
                              (u) =>
                                u.name.toLowerCase().includes(userSearchQuery.toLowerCase()) ||
                                u.email.toLowerCase().includes(userSearchQuery.toLowerCase())
                            )
                            .map((user) => (
                              <button
                                key={user.email}
                                type="button"
                                onClick={() => {
                                  setEditSquad([...editSquad, {
                                    id: Date.now().toString(),
                                    name: user.name,
                                    email: user.email,
                                    role: user.job_title || user.role,
                                    department: user.department || 'Engineering',
                                  }]);
                                  setUserSearchQuery('');
                                  setOpenUserSelect(false);
                                }}
                                className="w-full px-3 py-2 text-left hover:bg-gray-50 transition-colors border-b border-gray-100 last:border-0"
                              >
                                <div className="flex items-center gap-2">
                                  <Avatar className="w-6 h-6">
                                    <AvatarImage src={user.avatar} />
                                    <AvatarFallback className="text-xs bg-gradient-to-br from-[#321a75] to-[#00c3c4] text-white">
                                      {user.name.charAt(0)}
                                    </AvatarFallback>
                                  </Avatar>
                                  <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-gray-900 truncate">{user.name}</p>
                                    <p className="text-xs text-gray-500 truncate">{user.email}</p>
                                  </div>
                                </div>
                              </button>
                            ))}
                          {allUsers.filter(
                            (u) =>
                              u.name.toLowerCase().includes(userSearchQuery.toLowerCase()) ||
                              u.email.toLowerCase().includes(userSearchQuery.toLowerCase())
                          ).length === 0 && (
                            <div className="px-3 py-2 text-gray-500 text-sm">No users found</div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="relative mb-3">
                    <Input
                      type="text"
                      placeholder="Search user by name..."
                      value={userSearchQuery}
                      onChange={(e) => {
                        setUserSearchQuery(e.target.value);
                        setOpenUserSelect(true);
                      }}
                      onFocus={() => setOpenUserSelect(true)}
                      onBlur={() => setTimeout(() => setOpenUserSelect(false), 200)}
                      className="h-9 text-sm"
                    />
                    {openUserSelect && userSearchQuery && (
                      <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                        {allUsers
                          .filter(
                            (u) =>
                              u.name.toLowerCase().includes(userSearchQuery.toLowerCase()) ||
                              u.email.toLowerCase().includes(userSearchQuery.toLowerCase())
                          )
                          .map((user) => (
                            <button
                              key={user.email}
                              type="button"
                              onClick={() => handleAddSquadMember(user)}
                              className="w-full px-3 py-2 text-left hover:bg-gray-50 transition-colors border-b border-gray-100 last:border-0"
                            >
                              <div className="flex items-center gap-2">
                                <Avatar className="w-6 h-6">
                                  <AvatarImage src={user.avatar} />
                                  <AvatarFallback className="text-xs bg-gradient-to-br from-[#321a75] to-[#00c3c4] text-white">
                                    {user.name.charAt(0)}
                                  </AvatarFallback>
                                </Avatar>
                                <div className="flex-1 min-w-0">
                                  <p className="text-sm font-medium text-gray-900 truncate">{user.name}</p>
                                  <p className="text-xs text-gray-500 truncate">{user.email}</p>
                                </div>
                              </div>
                            </button>
                          ))}
                        {allUsers.filter(
                          (u) =>
                            u.name.toLowerCase().includes(userSearchQuery.toLowerCase()) ||
                            u.email.toLowerCase().includes(userSearchQuery.toLowerCase())
                        ).length === 0 && (
                            <div className="px-3 py-2 text-gray-500 text-sm">No users found</div>
                          )}
                      </div>
                    )}
                  </div>
                )}
                <ScrollArea className="h-[280px] pr-4">
                  <div className="space-y-2">
                    {data.internal_squad.map((member) => (
                      <div
                        key={member.id}
                        className="flex items-center space-x-3 p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
                      >
                        <Avatar className="w-10 h-10">
                          <AvatarImage src={member.avatar} />
                          <AvatarFallback className="bg-gradient-to-br from-[#321a75] to-[#00c3c4] text-white text-sm">
                            {member.name.charAt(0)}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-gray-900 text-sm truncate">{member.name}</p>
                          <p className="text-xs text-gray-500 truncate">{member.role}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </div>

              {/* POC Map */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-gray-900 flex items-center">
                    <Phone className="w-4 h-4 mr-2 text-[#faab00]" />
                    Client POCs
                  </h4>
                  {editingField === 'poc' ? (
                    <EditActions
                      onSave={() => handleSave('poc')}
                      onCancel={cancelEdit}
                      isSaving={isSaving}
                    />
                  ) : (
                    <EditButton onClick={() => handleStartEdit('poc')} canEdit={canEdit} />
                  )}
                </div>
                {editingField === 'poc' ? (
                  <div className="space-y-2">
                    {editPocMap.map((poc, idx) => (
                      <div key={poc.id || idx} className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg">
                        <Input
                          value={poc.name}
                          onChange={(e) => {
                            const updated = [...editPocMap];
                            updated[idx] = { ...poc, name: e.target.value };
                            setEditPocMap(updated);
                          }}
                          placeholder="Name"
                          className="flex-1 h-8 text-sm"
                        />
                        <Input
                          value={poc.role}
                          onChange={(e) => {
                            const updated = [...editPocMap];
                            updated[idx] = { ...poc, role: e.target.value };
                            setEditPocMap(updated);
                          }}
                          placeholder="Role"
                          className="flex-1 h-8 text-sm"
                        />
                        <select
                          value={poc.influence_level}
                          onChange={(e) => {
                            const updated = [...editPocMap];
                            updated[idx] = { ...poc, influence_level: e.target.value as any };
                            setEditPocMap(updated);
                          }}
                          className="h-8 px-2 text-sm border rounded-md bg-white"
                        >
                          <option value="high">High</option>
                          <option value="medium">Medium</option>
                          <option value="low">Low</option>
                        </select>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-red-500 hover:text-red-700 hover:bg-red-50"
                          onClick={() => setEditPocMap(editPocMap.filter((_, i) => i !== idx))}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full"
                      onClick={() => setEditPocMap([...editPocMap, {
                        id: Date.now().toString(),
                        name: '',
                        role: '',
                        email: '',
                        is_primary: false,
                        influence_level: 'medium'
                      }])}
                    >
                      <Plus className="h-4 w-4 mr-1" /> Add POC
                    </Button>
                  </div>
                ) : (
                  <ScrollArea className="h-[280px] pr-4">
                    <div className="space-y-2">
                      {data.poc_map.map((poc) => (
                        <div
                          key={poc.id}
                          className="flex items-center space-x-3 p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
                        >
                          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center text-gray-600 font-medium text-sm">
                            {poc.name.charAt(0)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-2">
                              <p className="font-medium text-gray-900 text-sm truncate">{poc.name}</p>
                              {poc.is_primary && (
                                <Star className="w-3 h-3 text-[#faab00] fill-[#faab00]" />
                              )}
                            </div>
                            <p className="text-xs text-gray-500 truncate">{poc.role}</p>
                          </div>
                          <Badge
                            variant="outline"
                            className={cn(
                              'text-xs',
                              poc.influence_level === 'high' && 'border-emerald-200 text-emerald-700 bg-emerald-50',
                              poc.influence_level === 'medium' && 'border-amber-200 text-amber-700 bg-amber-50',
                              poc.influence_level === 'low' && 'border-gray-200 text-gray-600 bg-gray-50',
                            )}
                          >
                            {poc.influence_level}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                )}
              </div>
            </div>

            {/* Communication Hygiene & Timeline */}
            <div className="lg:col-span-1 space-y-4">
              {/* Communication Hygiene */}
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-semibold text-gray-900 flex items-center">
                    <MessageSquare className="w-4 h-4 mr-2 text-[#321a75]" />
                    Communication Hygiene
                  </h4>
                  {editingField === 'hygiene' ? (
                    <EditActions
                      onSave={() => handleSave('hygiene')}
                      onCancel={cancelEdit}
                      isSaving={isSaving}
                    />
                  ) : (
                    <EditButton onClick={() => handleStartEdit('hygiene')} canEdit={canEdit} />
                  )}
                </div>

                {editingField === 'hygiene' && editHygiene ? (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-xs text-gray-500">Meetings this month</label>
                        <Input
                          type="number"
                          value={editHygiene.meetings_this_month}
                          onChange={(e) => setEditHygiene({ ...editHygiene, meetings_this_month: parseInt(e.target.value) || 0 })}
                          className="mt-1 h-8 text-sm"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-gray-500">Emails this month</label>
                        <Input
                          type="number"
                          value={editHygiene.emails_this_month}
                          onChange={(e) => setEditHygiene({ ...editHygiene, emails_this_month: parseInt(e.target.value) || 0 })}
                          className="mt-1 h-8 text-sm"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="text-xs text-gray-500">Last Meeting</label>
                      <Input
                        value={editHygiene.last_meeting}
                        onChange={(e) => setEditHygiene({ ...editHygiene, last_meeting: e.target.value })}
                        className="mt-1 h-8 text-sm"
                        placeholder="e.g., Jan 15, 2024"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-gray-500">Last Email</label>
                      <Input
                        value={editHygiene.last_email}
                        onChange={(e) => setEditHygiene({ ...editHygiene, last_email: e.target.value })}
                        className="mt-1 h-8 text-sm"
                        placeholder="e.g., Jan 18, 2024"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-gray-500">Avg Response Time</label>
                      <Input
                        value={editHygiene.response_time_avg}
                        onChange={(e) => setEditHygiene({ ...editHygiene, response_time_avg: e.target.value })}
                        className="mt-1 h-8 text-sm"
                        placeholder="e.g., 2 hours"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-gray-500">Health Status</label>
                      <select
                        value={editHygiene.health_status}
                        onChange={(e) => setEditHygiene({ ...editHygiene, health_status: e.target.value as any })}
                        className="w-full mt-1 h-8 px-3 text-sm border rounded-md bg-white"
                      >
                        <option value="excellent">Excellent</option>
                        <option value="good">Good</option>
                        <option value="needs_attention">Needs Attention</option>
                        <option value="critical">Critical</option>
                      </select>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div className="text-center p-3 bg-gray-50 rounded-lg">
                        <p className="text-2xl font-bold text-gray-900">{data.communication_hygiene.meetings_this_month}</p>
                        <p className="text-xs text-gray-500">Meetings this month</p>
                      </div>
                      <div className="text-center p-3 bg-gray-50 rounded-lg">
                        <p className="text-2xl font-bold text-gray-900">{data.communication_hygiene.emails_this_month}</p>
                        <p className="text-xs text-gray-500">Emails this month</p>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <div className="flex items-center justify-between text-sm">
                        <div className="flex items-center text-gray-500">
                          <Calendar className="w-4 h-4 mr-2" />
                          Last Meeting
                        </div>
                        <span className="font-medium text-gray-900">{data.communication_hygiene.last_meeting}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <div className="flex items-center text-gray-500">
                          <Mail className="w-4 h-4 mr-2" />
                          Last Email
                        </div>
                        <span className="font-medium text-gray-900">{data.communication_hygiene.last_email}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <div className="flex items-center text-gray-500">
                          <Clock className="w-4 h-4 mr-2" />
                          Avg Response Time
                        </div>
                        <span className="font-medium text-gray-900">{data.communication_hygiene.response_time_avg}</span>
                      </div>
                    </div>

                    <div className="mt-4 pt-4 border-t border-gray-100">
                      <Badge className={getHygieneStatusColor(data.communication_hygiene.health_status)}>
                        {data.communication_hygiene.health_status.replace('_', ' ')}
                      </Badge>
                    </div>
                  </>
                )}
              </div>

              {/* Timeline */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-gray-900 flex items-center">
                    <History className="w-4 h-4 mr-2 text-[#00c3c4]" />
                    Recent Timeline
                  </h4>
                  {editingField === 'timeline' ? (
                    <EditActions
                      onSave={() => handleSave('timeline')}
                      onCancel={cancelEdit}
                      isSaving={isSaving}
                    />
                  ) : (
                    <EditButton onClick={() => handleStartEdit('timeline')} canEdit={canEdit} />
                  )}
                </div>
                {editingField === 'timeline' ? (
                  <div className="space-y-2">
                    {editTimeline.map((event, idx) => (
                      <div key={event.id || idx} className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg">
                        <Input
                          type="date"
                          value={event.date}
                          onChange={(e) => {
                            const updated = [...editTimeline];
                            updated[idx] = { ...event, date: e.target.value };
                            setEditTimeline(updated);
                          }}
                          className="w-32 h-8 text-sm"
                        />
                        <Input
                          value={event.event}
                          onChange={(e) => {
                            const updated = [...editTimeline];
                            updated[idx] = { ...event, event: e.target.value };
                            setEditTimeline(updated);
                          }}
                          placeholder="Event description"
                          className="flex-1 h-8 text-sm"
                        />
                        <select
                          value={event.significance}
                          onChange={(e) => {
                            const updated = [...editTimeline];
                            updated[idx] = { ...event, significance: e.target.value as any };
                            setEditTimeline(updated);
                          }}
                          className="h-8 px-2 text-sm border rounded-md bg-white"
                        >
                          <option value="high">High</option>
                          <option value="medium">Medium</option>
                          <option value="low">Low</option>
                        </select>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-red-500 hover:text-red-700 hover:bg-red-50"
                          onClick={() => setEditTimeline(editTimeline.filter((_, i) => i !== idx))}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full"
                      onClick={() => setEditTimeline([...editTimeline, {
                        id: Date.now().toString(),
                        date: new Date().toISOString().split('T')[0],
                        event: '',
                        significance: 'medium',
                        category: 'milestone'
                      }])}
                    >
                      <Plus className="h-4 w-4 mr-1" /> Add Event
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {data.timeline.slice(0, 4).map((event) => (
                      <div key={event.id} className="flex items-start space-x-3">
                        <div className={cn(
                          'w-2 h-2 rounded-full mt-1.5 flex-shrink-0',
                          event.significance === 'high' && 'bg-red-500',
                          event.significance === 'medium' && 'bg-amber-500',
                          event.significance === 'low' && 'bg-gray-400',
                        )} />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">{event.event}</p>
                          <div className="flex items-center space-x-2 mt-0.5">
                            <span className="text-xs text-gray-500">{event.date}</span>
                            <Badge variant="outline" className="text-xs capitalize">
                              {event.category}
                            </Badge>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Important Notes */}
              <div className="bg-amber-50 rounded-xl border border-amber-200 p-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-gray-900 flex items-center">
                    <Star className="w-4 h-4 mr-2 text-amber-600" />
                    Important Notes
                  </h4>
                  {editingField === 'notes' ? (
                    <EditActions
                      onSave={() => handleSave('notes')}
                      onCancel={cancelEdit}
                      isSaving={isSaving}
                    />
                  ) : (
                    <EditButton onClick={() => handleStartEdit('notes')} canEdit={canEdit} />
                  )}
                </div>
                {editingField === 'notes' ? (
                  <div className="space-y-2">
                    {editNotes.map((note, idx) => (
                      <div key={idx} className="flex items-center gap-2">
                        <Input
                          value={note}
                          onChange={(e) => {
                            const updated = [...editNotes];
                            updated[idx] = e.target.value;
                            setEditNotes(updated);
                          }}
                          className="flex-1 h-8 text-sm"
                        />
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-red-500 hover:text-red-700 hover:bg-red-50"
                          onClick={() => setEditNotes(editNotes.filter((_, i) => i !== idx))}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                    <div className="flex gap-2">
                      <Input
                        value={newNote}
                        onChange={(e) => setNewNote(e.target.value)}
                        placeholder="Add a note..."
                        className="flex-1 h-8 text-sm"
                        onKeyPress={(e) => {
                          if (e.key === 'Enter' && newNote.trim()) {
                            setEditNotes([...editNotes, newNote.trim()]);
                            setNewNote('');
                          }
                        }}
                      />
                      <Button
                        size="sm"
                        onClick={() => {
                          if (newNote.trim()) {
                            setEditNotes([...editNotes, newNote.trim()]);
                            setNewNote('');
                          }
                        }}
                        className="h-8"
                      >
                        <Plus className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="space-y-2 mb-3">
                      {data.important_notes.length === 0 ? (
                        <p className="text-sm text-gray-500 italic">No important notes yet</p>
                      ) : (
                        data.important_notes.map((note, idx) => (
                          <div key={idx} className="flex items-start space-x-2 text-sm">
                            <span className="text-amber-600 mt-0.5">•</span>
                            <p className="flex-1 text-gray-700">{note}</p>
                          </div>
                        ))
                      )}
                    </div>
                    {canEdit && (
                      <div className="flex gap-2">
                        <Input
                          value={newNote}
                          onChange={(e) => setNewNote(e.target.value)}
                          placeholder="Add a note..."
                          className="flex-1 h-8 text-sm"
                          onKeyPress={(e) => e.key === 'Enter' && handleAddNote()}
                        />
                        <Button size="sm" onClick={handleAddNote} className="h-8">
                          <Plus className="h-4 w-4" />
                        </Button>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      )}
    </Card>
  );
}
