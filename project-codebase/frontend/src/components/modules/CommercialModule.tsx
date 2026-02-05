import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { CollapsibleList } from '@/components/ui/collapsible-list';
import { useEditMode } from '@/hooks/useEditMode';
import { useStore } from '@/store/useStore';
import { commercialApi } from '@/services/api';
import type { CommercialData } from '@/types';
import { NexusPieChart } from '@/components/ui/charts';
import {
  DollarSign,
  ChevronDown,
  ChevronUp,
  FileText,
  Receipt,
  Calendar,
  Lock,
  PieChart,
  Plus,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface CommercialModuleProps {
  isExpanded: boolean;
  onToggle: () => void;
}

export function CommercialModule({ isExpanded, onToggle }: CommercialModuleProps) {
  const { selectedClient, selectedProject, permissions } = useStore();
  const [data, setData] = useState<CommercialData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [isSaving, setIsSaving] = useState(false);

  const loadData = useCallback(async () => {
    if (!selectedClient || !selectedProject) return;
    setIsLoading(true);
    try {
      // Use client_id and project_id for backend compatibility
      const clientId = selectedProject.client_id || selectedClient.id;
      const projectId = selectedProject.project_id || selectedProject.id;

      const response = await commercialApi.get(clientId, projectId);
      if (response.success && response.data) {
        setData(response.data);
      }
    } catch (error) {
      console.error('Failed to load commercial data:', error);
    } finally {
      setIsLoading(false);
    }
  }, [selectedClient, selectedProject]);

  // Edit mode hook
  const { canEdit } = useEditMode({
    section: 'commercial',
    onSave: loadData,
  });

  // Edit states
  const [newInvoice, setNewInvoice] = useState({ invoice_id: '', amount: 0, date: '', due_date: '', status: 'pending' as const });
  const [showAddInvoice, setShowAddInvoice] = useState(false);

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

  const handleAddInvoice = async () => {
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId || !newInvoice.invoice_id) return;

    setIsSaving(true);
    try {
      await commercialApi.addInvoice(clientId, projectId, newInvoice);
      setNewInvoice({ invoice_id: '', amount: 0, date: '', due_date: '', status: 'pending' });
      setShowAddInvoice(false);
      loadData();
    } catch (error) {
      console.error('Failed to add invoice:', error);
    } finally {
      setIsSaving(false);
    }
  };

  // Check if user has permission to view commercial data
  const canView = permissions?.commercial !== 'NONE';

  const getInvoiceStatusColor = (status: string) => {
    switch (status) {
      case 'paid': return 'bg-emerald-100 text-emerald-700 border-emerald-200';
      case 'pending': return 'bg-amber-100 text-amber-700 border-amber-200';
      case 'overdue': return 'bg-red-100 text-red-700 border-red-200';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const getRenewalStatusColor = (status: string) => {
    switch (status) {
      case 'signed': return 'bg-emerald-100 text-emerald-700 border-emerald-200';
      case 'in_negotiation': return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'upcoming': return 'bg-purple-100 text-purple-700 border-purple-200';
      case 'at_risk': return 'bg-red-100 text-red-700 border-red-200';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const getSOWStatusColor = (status: string) => {
    switch (status) {
      case 'signed': return 'bg-emerald-100 text-emerald-700 border-emerald-200';
      case 'draft': return 'bg-gray-100 text-gray-700 border-gray-200';
      case 'amendment': return 'bg-amber-100 text-amber-700 border-amber-200';
      case 'expired': return 'bg-red-100 text-red-700 border-red-200';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const formatCurrency = (amount: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  if (!canView) {
    return (
      <Card className="module-section opacity-75">
        <CardHeader className="module-header" onClick={onToggle}>
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-gray-200 flex items-center justify-center">
              <DollarSign className="w-5 h-5 text-gray-500" />
            </div>
            <div>
              <CardTitle className="text-lg font-semibold text-gray-900">Commercial & Legal</CardTitle>
              <p className="text-sm text-gray-500">Management Focus - RESTRICTED</p>
            </div>
          </div>
          <Button variant="ghost" size="icon">
            {isExpanded ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
          </Button>
        </CardHeader>
        {isExpanded && (
          <CardContent className="p-8">
            <div className="text-center">
              <Lock className="w-12 h-12 mx-auto mb-3 text-gray-400" />
              <p className="text-gray-500">You don&apos;t have permission to view commercial data</p>
            </div>
          </CardContent>
        )}
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card className="module-section">
        <CardHeader className="module-header">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-[#faab00]/10 flex items-center justify-center">
              <DollarSign className="w-5 h-5 text-[#faab00]" />
            </div>
            <div>
              <CardTitle className="text-lg font-semibold text-gray-900">Commercial & Legal</CardTitle>
              <p className="text-sm text-gray-500">Management Focus - RESTRICTED</p>
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

  const billingProgress = (data.financial.total_billed / data.financial.total_contract_value) * 100;

  return (
    <Card className="module-section overflow-hidden border-amber-200">
      <CardHeader className="module-header bg-amber-50/50" onClick={onToggle}>
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#faab00] to-[#ffc94d] flex items-center justify-center">
            <DollarSign className="w-5 h-5 text-white" />
          </div>
          <div>
            <CardTitle className="text-lg font-semibold text-gray-900">Commercial & Legal</CardTitle>
            <p className="text-sm text-gray-500">Management Focus - RESTRICTED</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Lock className="w-4 h-4 text-amber-600" />
          <Button variant="ghost" size="icon">
            {isExpanded ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
          </Button>
        </div>
      </CardHeader>

      {isExpanded && (
        <CardContent className="p-6">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-5 mb-6">
              <TabsTrigger value="overview" className="text-sm">
                <PieChart className="w-4 h-4 mr-2" />
                Overview
              </TabsTrigger>
              <TabsTrigger value="sow" className="text-sm">
                <FileText className="w-4 h-4 mr-2" />
                SOW
              </TabsTrigger>
              <TabsTrigger value="invoices" className="text-sm">
                <Receipt className="w-4 h-4 mr-2" />
                Invoices
              </TabsTrigger>
              <TabsTrigger value="renewals" className="text-sm">
                <Calendar className="w-4 h-4 mr-2" />
                Renewals
              </TabsTrigger>
              <TabsTrigger value="analytics" className="text-sm">
                <PieChart className="w-4 h-4 mr-2" />
                Analytics
              </TabsTrigger>
            </TabsList>

            <TabsContent value="overview">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <div className="p-4 bg-gradient-to-br from-[#321a75]/5 to-[#321a75]/10 rounded-xl border border-[#321a75]/10">
                  <p className="text-sm text-gray-600 mb-1">Total Contract Value</p>
                  <p className="text-2xl font-bold text-[#321a75]">
                    {formatCurrency(data.financial.total_contract_value, data.financial.currency)}
                  </p>
                </div>
                <div className="p-4 bg-gradient-to-br from-emerald-50 to-emerald-100 rounded-xl border border-emerald-200">
                  <p className="text-sm text-gray-600 mb-1">Total Billed</p>
                  <p className="text-2xl font-bold text-emerald-700">
                    {formatCurrency(data.financial.total_billed, data.financial.currency)}
                  </p>
                </div>
                <div className="p-4 bg-gradient-to-br from-amber-50 to-amber-100 rounded-xl border border-amber-200">
                  <p className="text-sm text-gray-600 mb-1">Outstanding</p>
                  <p className="text-2xl font-bold text-amber-700">
                    {formatCurrency(data.financial.outstanding, data.financial.currency)}
                  </p>
                </div>
                <div className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl border border-blue-200">
                  <p className="text-sm text-gray-600 mb-1">Monthly Burn Rate</p>
                  <p className="text-2xl font-bold text-blue-700">
                    {formatCurrency(data.financial.burn_rate, data.financial.currency)}
                  </p>
                </div>
              </div>

              <div className="bg-gray-50 rounded-xl p-5">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-gray-900">Billing Progress</h4>
                  <span className="text-sm font-medium text-gray-700">{billingProgress.toFixed(1)}%</span>
                </div>
                <Progress value={billingProgress} className="h-3" />
                <div className="flex items-center justify-between mt-3 text-sm text-gray-500">
                  <span>Billed: {formatCurrency(data.financial.total_billed, data.financial.currency)}</span>
                  <span>Remaining: {formatCurrency(data.financial.budget_remaining, data.financial.currency)}</span>
                </div>
              </div>

              {/* Revenue Mix */}
              <div className="mt-6">
                <h4 className="font-semibold text-gray-900 mb-4">Revenue Mix</h4>
                <div className="space-y-3">
                  {data.revenue_channels.map((channel) => (
                    <div key={channel.channel} className="flex items-center">
                      <div className="w-32 text-sm text-gray-600">{channel.channel}</div>
                      <div className="flex-1 mx-4">
                        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-[#321a75] to-[#00c3c4] rounded-full"
                            style={{ width: `${channel.percentage}%` }}
                          />
                        </div>
                      </div>
                      <div className="w-24 text-right">
                        <span className="text-sm font-medium text-gray-900">
                          {formatCurrency(channel.amount, data.financial.currency)}
                        </span>
                        <span className="text-xs text-gray-500 ml-1">({channel.percentage}%)</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="sow">
              <div className="bg-gray-50 rounded-xl p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h4 className="text-lg font-semibold text-gray-900">{data.sow.title}</h4>
                    <p className="text-sm text-gray-500">{data.sow.sow_id}</p>
                  </div>
                  <Badge variant="outline" className={cn('text-sm', getSOWStatusColor(data.sow.status))}>
                    {data.sow.status}
                  </Badge>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  <div>
                    <p className="text-sm text-gray-500">Contract Value</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {formatCurrency(data.sow.value, data.sow.currency)}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Start Date</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {new Date(data.sow.start_date).toLocaleDateString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">End Date</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {new Date(data.sow.end_date).toLocaleDateString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Duration</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {Math.ceil((new Date(data.sow.end_date).getTime() - new Date(data.sow.start_date).getTime()) / (1000 * 60 * 60 * 24 * 365))} years
                    </p>
                  </div>
                </div>

                <div>
                  <p className="text-sm text-gray-500 mb-2">Scope Summary</p>
                  <p className="text-sm text-gray-700">{data.sow.scope_summary}</p>
                </div>

                <div className="mt-4">
                  <p className="text-sm text-gray-500 mb-2">Key Deliverables</p>
                  <div className="flex flex-wrap gap-2">
                    {data.sow.deliverables.map((deliverable, index) => (
                      <Badge key={index} variant="secondary" className="bg-white">
                        {deliverable}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="invoices">
              {/* Add Invoice Button */}
              {canEdit && (
                <div className="mb-4">
                  {showAddInvoice ? (
                    <div className="p-4 bg-gray-50 rounded-xl border border-gray-200">
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                        <Input
                          value={newInvoice.invoice_id}
                          onChange={(e) => setNewInvoice({ ...newInvoice, invoice_id: e.target.value })}
                          placeholder="Invoice ID"
                        />
                        <Input
                          type="number"
                          value={newInvoice.amount || ''}
                          onChange={(e) => setNewInvoice({ ...newInvoice, amount: parseFloat(e.target.value) })}
                          placeholder="Amount"
                        />
                        <Input
                          type="date"
                          value={newInvoice.due_date}
                          onChange={(e) => setNewInvoice({ ...newInvoice, due_date: e.target.value, date: e.target.value })}
                        />
                        <select
                          value={newInvoice.status}
                          onChange={(e) => setNewInvoice({ ...newInvoice, status: e.target.value as any })}
                          className="h-10 px-3 border rounded-md bg-white"
                        >
                          <option value="pending">Pending</option>
                          <option value="paid">Paid</option>
                          <option value="overdue">Overdue</option>
                        </select>
                      </div>
                      <div className="flex gap-2">
                        <Button onClick={handleAddInvoice} size="sm" className="bg-[#321a75] hover:bg-[#4a2d99]" disabled={isSaving}>
                          <Plus className="h-4 w-4 mr-1" /> {isSaving ? 'Adding...' : 'Add'}
                        </Button>
                        <Button onClick={() => setShowAddInvoice(false)} variant="outline" size="sm">
                          Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <Button onClick={() => setShowAddInvoice(true)} variant="outline" className="w-full">
                      <Plus className="h-4 w-4 mr-2" /> Add Invoice
                    </Button>
                  )}
                </div>
              )}
              <CollapsibleList
                items={data.invoices}
                renderItem={(invoice) => (
                  <div
                    key={invoice.id}
                    className="p-4 rounded-xl bg-gray-50 border border-gray-100 flex items-center justify-between"
                  >
                    <div className="flex items-center space-x-4">
                      <div className="w-10 h-10 rounded-lg bg-[#faab00]/10 flex items-center justify-center text-[#faab00]">
                        <Receipt className="w-5 h-5" />
                      </div>
                      <div>
                        <p className="font-semibold text-gray-900">{invoice.invoice_id}</p>
                        <p className="text-sm text-gray-500">{invoice.description}</p>
                        <div className="flex items-center space-x-3 mt-1 text-xs text-gray-400">
                          <span>Issued: {new Date(invoice.date).toLocaleDateString()}</span>
                          <span>Due: {new Date(invoice.due_date).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-semibold text-gray-900">
                        {formatCurrency(invoice.amount, data.financial.currency)}
                      </p>
                      <Badge variant="outline" className={cn('text-xs mt-1', getInvoiceStatusColor(invoice.status))}>
                        {invoice.status}
                      </Badge>
                    </div>
                  </div>
                )}
                initialDisplayCount={5}
                maxHeight="400px"
              />
            </TabsContent>

            <TabsContent value="renewals">
              <CollapsibleList
                items={data.renewals}
                renderItem={(renewal) => (
                  <div
                    key={renewal.id}
                    className="p-4 rounded-xl bg-gray-50 border border-gray-100"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-4">
                        <div className="w-10 h-10 rounded-lg bg-[#321a75]/10 flex items-center justify-center text-[#321a75]">
                          <Calendar className="w-5 h-5" />
                        </div>
                        <div>
                          <p className="font-semibold text-gray-900">{renewal.contract_name}</p>
                          <div className="flex items-center space-x-4 mt-2">
                            <div>
                              <p className="text-xs text-gray-500">Current Value</p>
                              <p className="text-sm font-medium text-gray-700">
                                {formatCurrency(renewal.current_value, data.financial.currency)}
                              </p>
                            </div>
                            {renewal.proposed_value && (
                              <div>
                                <p className="text-xs text-gray-500">Proposed Value</p>
                                <p className="text-sm font-medium text-emerald-700">
                                  {formatCurrency(renewal.proposed_value, data.financial.currency)}
                                </p>
                              </div>
                            )}
                          </div>
                          {renewal.notes && (
                            <p className="text-sm text-gray-500 mt-2">{renewal.notes}</p>
                          )}
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge variant="outline" className={cn('text-xs mb-2', getRenewalStatusColor(renewal.status))}>
                          {renewal.status.replace('_', ' ')}
                        </Badge>
                        <p className="text-xs text-gray-500">
                          Renewal: {new Date(renewal.renewal_date).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
                initialDisplayCount={4}
                maxHeight="400px"
              />
            </TabsContent>
            <TabsContent value="analytics">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
                <div className="bg-gray-50 p-6 rounded-2xl border border-gray-100 h-full flex flex-col justify-center">
                  <h4 className="text-lg font-semibold text-gray-900 mb-6 flex items-center gap-2">
                    <DollarSign className="w-5 h-5 text-[#faab00]" />
                    Revenue Distribution by Channel
                  </h4>
                  <NexusPieChart
                    data={data.revenue_channels.map(c => ({
                      name: c.channel,
                      value: c.amount
                    }))}
                  />
                </div>
                <div className="space-y-6">
                  <div className="p-4 rounded-xl bg-[#faab00]/5 border border-[#faab00]/10">
                    <h5 className="font-semibold text-[#faab00] mb-2 flex items-center gap-2">
                      <Receipt className="w-4 h-4" />
                      Financial Snapshot
                    </h5>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs text-gray-500 uppercase tracking-widest font-bold">Paid Ratio</p>
                        <p className="text-xl font-bold text-gray-900">
                          {Math.round((data.invoices.filter(i => i.status === 'paid').length / Math.max(1, data.invoices.length)) * 100)}%
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 uppercase tracking-widest font-bold">Overdue Count</p>
                        <p className="text-xl font-bold text-red-600">
                          {data.invoices.filter(i => i.status === 'overdue').length}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="card-shadow p-6 rounded-xl bg-white border border-gray-100">
                    <h5 className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-4 italic">Next Milestone</h5>
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-full border-4 border-emerald-500 border-r-transparent animate-spin-slow flex items-center justify-center">
                        <span className="text-xs font-bold text-emerald-600">GO</span>
                      </div>
                      <div>
                        <p className="text-sm font-bold text-gray-900">Renewal Window</p>
                        <p className="text-xs text-gray-500">
                          {data.renewals.length > 0 ?
                            `Next renewal: ${new Date(Math.min(...data.renewals.map(r => new Date(r.renewal_date).getTime()))).toLocaleDateString()}` :
                            "No upcoming renewals mapped."}
                        </p>
                      </div>
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
