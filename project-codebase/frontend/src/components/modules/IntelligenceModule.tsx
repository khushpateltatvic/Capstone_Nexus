import { useState, useEffect } from 'react';
import { useStore } from '@/store/useStore';
import { intelligenceApi, apiClient, API_VERSION } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { RefreshCw, AlertTriangle, TrendingUp, BookOpen, BrainCircuit } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { UpsellOpportunity, RiskItem, KnowledgeItem } from '@/types';

export function IntelligenceModule() {
    const { selectedClient, selectedProject } = useStore();
    const [activeTab, setActiveTab] = useState('risk');
    const [loading, setLoading] = useState(false);

    const [upsellData, setUpsellData] = useState<UpsellOpportunity[]>([]);
    const [riskData, setRiskData] = useState<RiskItem | null>(null);
    const [knowledgeData, setKnowledgeData] = useState<KnowledgeItem[]>([]);

    useEffect(() => {
        if (selectedClient && selectedProject) {
            loadIntelligence();
        }
    }, [selectedClient, selectedProject]);

    const generateIntelligence = async (type: 'upsell' | 'risk') => {
        setLoading(true);
        try {
            const projectId = selectedProject?.id || selectedProject?.project_id;
            if (!projectId) return;

            if (type === 'risk') {
                await apiClient.post(`${API_VERSION}/intelligence/risk/${projectId}/analyze`);
            } else if (type === 'upsell') {
                await apiClient.post(`${API_VERSION}/intelligence/upsell/${projectId}/generate`);
            }

            // Reload data
            loadIntelligence();
        } catch (error) {
            console.error(`Failed to generate ${type}:`, error);
        } finally {
            setLoading(false);
        }
    };

    const loadIntelligence = async () => {
        setLoading(true);
        try {
            const clientId = selectedProject?.client_id || selectedClient?.id;
            const projectId = selectedProject?.project_id || selectedProject?.id;

            if (!clientId || !projectId) return;

            const [riskRes, upsellRes, knowledgeRes] = await Promise.all([
                intelligenceApi.getRisk(projectId),
                intelligenceApi.getUpsell(projectId),
                intelligenceApi.getKnowledge(projectId),
            ]);

            if (riskRes.success && riskRes.data && Object.keys(riskRes.data).length > 0) {
                setRiskData(riskRes.data);
            } else {
                setRiskData(null);
            }

            if (upsellRes.success) setUpsellData(Array.isArray(upsellRes.data) ? upsellRes.data : []);
            if (knowledgeRes.success) setKnowledgeData(Array.isArray(knowledgeRes.data) ? knowledgeRes.data : []);

        } catch (error) {
            console.error('Failed to load intelligence data:', error);
        } finally {
            setLoading(false);
        }
    };

    if (!selectedProject) {
        return (
            <div className="flex-1 flex items-center justify-center p-8">
                <div className="text-center">
                    <BrainCircuit className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900">Select a project</h3>
                    <p className="text-gray-500">Please select a project to view intelligence insights.</p>
                </div>
            </div>
        );
    }

    if (loading) {
        return (
            <div className="flex-1 flex items-center justify-center h-full min-h-[400px]">
                <div className="flex flex-col items-center">
                    <RefreshCw className="w-8 h-8 animate-spin text-[#321a75] mb-3" />
                    <p className="text-gray-500">Generating intelligence insights...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                        <BrainCircuit className="w-6 h-6 mr-2 text-[#321a75]" />
                        Project Intelligence
                    </h2>
                    <p className="text-gray-500 mt-1">AI-driven insights for {selectedProject.name}</p>
                </div>
            </div>

            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="grid w-full grid-cols-3 max-w-[600px] mb-6">
                    <TabsTrigger value="risk" className="flex items-center">
                        <AlertTriangle className="w-4 h-4 mr-2" />
                        Risk Analysis
                    </TabsTrigger>
                    <TabsTrigger value="upsell" className="flex items-center">
                        <TrendingUp className="w-4 h-4 mr-2" />
                        Upsell Opportunities
                    </TabsTrigger>
                    <TabsTrigger value="knowledge" className="flex items-center">
                        <BookOpen className="w-4 h-4 mr-2" />
                        Knowledge Base
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="risk" className="space-y-4">
                    {riskData ? (
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            <Card className="border-l-4 border-l-[#321a75]">
                                <CardHeader>
                                    <CardTitle className="mb-2">Risk Overview</CardTitle>
                                    <div className="flex items-center space-x-3">
                                        <Badge variant={
                                            riskData.risk_level === 'Critical' ? 'destructive' :
                                                riskData.risk_level === 'High' ? 'destructive' :
                                                    riskData.risk_level === 'Medium' ? 'outline' : 'secondary'
                                        } className="text-sm px-3 py-1">
                                            {riskData.risk_level} Risk
                                        </Badge>
                                        {riskData.sentiment && (
                                            <Badge variant="outline" className={cn(
                                                "text-sm px-3 py-1 border-2",
                                                riskData.sentiment === 'Positive' ? 'border-emerald-500 text-emerald-700 bg-emerald-50' :
                                                    riskData.sentiment === 'Negative' ? 'border-rose-500 text-rose-700 bg-rose-50' :
                                                        'border-slate-300 text-slate-600 bg-slate-50'
                                            )}>
                                                {riskData.sentiment} Sentiment
                                            </Badge>
                                        )}
                                    </div>
                                    <CardDescription className="mt-2 text-slate-500 italic">
                                        Automated strategic assessment
                                    </CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <div className={cn(
                                        "p-4 rounded-lg mb-6 border",
                                        riskData.risk_level === 'Critical' || riskData.risk_level === 'High' ? "bg-rose-50/50 border-rose-100" : "bg-slate-50 border-slate-100"
                                    )}>
                                        <p className="text-gray-800 leading-relaxed font-medium">{riskData.summary}</p>
                                    </div>
                                    <div className="space-y-4">
                                        <div>
                                            <h4 className="font-semibold text-gray-900 mb-2">Key Indicators</h4>
                                            <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                                                {riskData.indicators?.map((indicator, idx) => (
                                                    <li key={idx}>{indicator}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>

                            <Card className="bg-emerald-50/50 border-emerald-100 shadow-sm">
                                <CardHeader>
                                    <CardTitle className="text-emerald-900">Recommendations</CardTitle>
                                    <CardDescription className="text-emerald-700">Suggested mitigation strategies</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-4">
                                        {riskData.recommendations?.map((rec, idx) => (
                                            <div key={idx} className="flex items-start space-x-3 bg-white p-4 rounded-lg shadow-sm border border-emerald-100">
                                                <div className="w-6 h-6 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                                                    <span className="text-emerald-700 font-bold text-xs">{idx + 1}</span>
                                                </div>
                                                <p className="text-gray-800 text-sm">{rec}</p>
                                            </div>
                                        ))}
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                    ) : (
                        <div className="text-center py-12 bg-gray-50 rounded-lg border border-dashed border-gray-300">
                            <p className="text-gray-500 mb-4">No risk analysis data available yet.</p>
                            <Button onClick={() => generateIntelligence('risk')} className="bg-[#321a75]">
                                Generate Risk Analysis
                            </Button>
                        </div>
                    )}
                </TabsContent>

                <TabsContent value="upsell" className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 auto-rows-fr">
                        {upsellData.length > 0 ? upsellData.map((item) => (
                            <Card key={item.id} className="hover:shadow-lg transition-all duration-300 border-t-4 border-t-[#00c3c4] flex flex-col h-full">
                                <CardHeader className="pb-3 flex-shrink-0">
                                    <div className="flex justify-between items-start mb-2">
                                        <Badge variant="outline" className="text-[10px] font-bold uppercase tracking-tight max-w-[150px] truncate">
                                            {item.service_category}
                                        </Badge>
                                        <Badge className={cn(
                                            "text-[10px] px-2",
                                            item.potential_value === 'High' ? "bg-emerald-100 text-emerald-700 border-emerald-200" :
                                                item.potential_value === 'Medium' ? "bg-amber-100 text-amber-700 border-amber-200" :
                                                    "bg-slate-100 text-slate-600 border-slate-200"
                                        )}>
                                            {item.potential_value} Value
                                        </Badge>
                                    </div>
                                    <CardTitle className="text-base font-extrabold leading-tight text-[#321a75]">{item.title}</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4 flex-grow flex flex-col">
                                    <p className="text-sm text-slate-600 leading-snug">
                                        {item.description}
                                    </p>
                                    <div className="bg-slate-50 p-3 rounded-lg border border-slate-100 mt-auto">
                                        <div className="text-[10px] uppercase tracking-wider font-bold text-slate-400 mb-1">Strategic Pitch</div>
                                        <p className="text-xs text-slate-700 leading-relaxed italic line-clamp-4 hover:line-clamp-none transition-all">
                                            "{item.pitch}"
                                        </p>
                                    </div>
                                    <div className="pt-3 border-t border-slate-100">
                                        <div className="text-[10px] uppercase tracking-wider font-bold text-slate-400 mb-1">Rationale</div>
                                        <p className="text-[11px] text-slate-500 leading-tight">
                                            {item.rationale}
                                        </p>
                                    </div>
                                </CardContent>
                            </Card>
                        )) : (
                            <div className="col-span-full text-center py-12 bg-gray-50 rounded-lg border border-dashed border-gray-300">
                                <p className="text-gray-500 mb-4">No upsell opportunities identified yet.</p>
                                <Button onClick={() => generateIntelligence('upsell')} className="bg-[#321a75]">
                                    Generate Opportunities
                                </Button>
                            </div>
                        )}
                    </div>
                </TabsContent>

                <TabsContent value="knowledge" className="space-y-4">
                    <div className="space-y-4">
                        {knowledgeData.length > 0 ? knowledgeData.map((item, idx) => (
                            <Card key={idx} className="hover:border-[#321a75] transition-colors border-l-4 border-l-blue-400">
                                <CardHeader>
                                    <div className="flex items-center justify-between">
                                        <CardTitle className="text-lg text-[#321a75]">{item.title}</CardTitle>
                                        <Badge variant="secondary" className="bg-blue-50 text-blue-700">
                                            Match: {Math.round(item.relevance_score * 100)}%
                                        </Badge>
                                    </div>
                                    <CardDescription>Similar Case Study: <span className="font-semibold text-slate-900">{item.project_name}</span></CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <p className="text-sm text-gray-700 mb-4 leading-relaxed">{item.summary}</p>
                                    <div>
                                        <h5 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Transferable Insights:</h5>
                                        <div className="flex flex-wrap gap-2">
                                            {item.key_learnings?.map((learning, lIdx) => (
                                                <span key={lIdx} className="bg-blue-50/50 text-blue-700 text-[11px] px-2 py-1 rounded border border-blue-100">
                                                    {learning}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        )) : (
                            <div className="text-center py-12 bg-gray-50 rounded-lg border border-dashed border-gray-300">
                                <RefreshCw className="w-8 h-8 text-gray-300 mx-auto mb-3" />
                                <p className="text-gray-500 font-medium">No direct project matches found currently.</p>
                                <p className="text-sm text-gray-400 mt-1">AI continues to index success stories in the background.</p>
                            </div>
                        )}
                    </div>
                </TabsContent>
            </Tabs>
        </div>
    );
}
