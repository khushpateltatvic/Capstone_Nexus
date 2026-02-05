import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { CollapsibleList } from '@/components/ui/collapsible-list';
import { useStore } from '@/store/useStore';
import { marketingApi } from '@/services/api';
import { useEditMode } from '@/hooks/useEditMode';
import type { MarketingData } from '@/types';
import {
  Megaphone,
  ChevronDown,
  ChevronUp,
  Palette,
  Trophy,
  Quote,
  Globe,
  ExternalLink,
  FileText,
  Image,
  Video,
  Newspaper,
  Share2,
  Plus,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface MarketingModuleProps {
  isExpanded: boolean;
  onToggle: () => void;
}

export function MarketingModule({ isExpanded, onToggle }: MarketingModuleProps) {
  const { selectedClient, selectedProject } = useStore();
  const [data, setData] = useState<MarketingData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('brand');
  
  // Edit mode
  const { canEdit } = useEditMode({ section: 'marketing' });
  const [isSaving, setIsSaving] = useState(false);
  
  // Add states
  const [showAddTestimonial, setShowAddTestimonial] = useState(false);
  const [showAddStory, setShowAddStory] = useState(false);
  const [showAddReference, setShowAddReference] = useState(false);
  
  const [newTestimonial, setNewTestimonial] = useState<{ from_person: string; quote: string }>({
    from_person: '',
    quote: '',
  });
  const [newStory, setNewStory] = useState<{ title: string; description: string }>({
    title: '',
    description: '',
  });
  const [newReference, setNewReference] = useState<{ type: string; title: string; url: string }>({
    type: 'blog_post',
    title: '',
    url: '',
  });
  
  const getIds = () => {
    const clientId = selectedProject?.client_id || selectedClient?.id || '';
    const projectId = selectedProject?.project_id || selectedProject?.id || '';
    return { clientId, projectId };
  };
  
  const handleAddTestimonial = async () => {
    if (!newTestimonial.from_person || !newTestimonial.quote) return;
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId) return;
    
    setIsSaving(true);
    try {
      const result = await marketingApi.addTestimonial(clientId, projectId, newTestimonial);
      if (result.success) {
        setNewTestimonial({ from_person: '', quote: '' });
        setShowAddTestimonial(false);
        loadData();
      }
    } finally {
      setIsSaving(false);
    }
  };
  
  const handleAddStory = async () => {
    if (!newStory.title) return;
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId) return;
    
    setIsSaving(true);
    try {
      const result = await marketingApi.addSuccessStory(clientId, projectId, newStory);
      if (result.success) {
        setNewStory({ title: '', description: '' });
        setShowAddStory(false);
        loadData();
      }
    } finally {
      setIsSaving(false);
    }
  };
  
  const handleAddReference = async () => {
    if (!newReference.title || !newReference.type) return;
    const { clientId, projectId } = getIds();
    if (!clientId || !projectId) return;
    
    setIsSaving(true);
    try {
      const result = await marketingApi.addPublicReference(clientId, projectId, newReference);
      if (result.success) {
        setNewReference({ type: 'blog_post', title: '', url: '' });
        setShowAddReference(false);
        loadData();
      }
    } finally {
      setIsSaving(false);
    }
  };

  useEffect(() => {
    if (selectedClient && selectedProject) {
      loadData();
    }
  }, [selectedClient, selectedProject]);

  const loadData = async () => {
    if (!selectedClient || !selectedProject) return;
    setIsLoading(true);
    try {
      // Use client_id and project_id for backend compatibility
      const clientId = selectedProject.client_id || selectedClient.id;
      const projectId = selectedProject.project_id || selectedProject.id;
      
      const response = await marketingApi.get(clientId, projectId);
      if (response.success && response.data) {
        setData(response.data);
      }
    } catch (error) {
      console.error('Failed to load marketing data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getApprovalStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return 'bg-emerald-100 text-emerald-700 border-emerald-200';
      case 'pending': return 'bg-amber-100 text-amber-700 border-amber-200';
      case 'published': return 'bg-blue-100 text-blue-700 border-blue-200';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const getReferenceTypeIcon = (type: string) => {
    switch (type) {
      case 'press_release': return <Newspaper className="w-4 h-4" />;
      case 'blog_post': return <FileText className="w-4 h-4" />;
      case 'social_media': return <Share2 className="w-4 h-4" />;
      case 'event': return <Video className="w-4 h-4" />;
      default: return <Globe className="w-4 h-4" />;
    }
  };

  if (isLoading) {
    return (
      <Card className="module-section">
        <CardHeader className="module-header">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-[#faab00]/10 flex items-center justify-center">
              <Megaphone className="w-5 h-5 text-[#faab00]" />
            </div>
            <div>
              <CardTitle className="text-lg font-semibold text-gray-900">Marketing</CardTitle>
              <p className="text-sm text-gray-500">Marketing Team Focus</p>
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
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#faab00] to-[#ffc94d] flex items-center justify-center">
            <Megaphone className="w-5 h-5 text-white" />
          </div>
          <div>
            <CardTitle className="text-lg font-semibold text-gray-900">Marketing</CardTitle>
            <p className="text-sm text-gray-500">Marketing Team Focus</p>
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
              <TabsTrigger value="brand" className="text-sm">
                <Palette className="w-4 h-4 mr-2" />
                Brand
              </TabsTrigger>
              <TabsTrigger value="success" className="text-sm">
                <Trophy className="w-4 h-4 mr-2" />
                Success
              </TabsTrigger>
              <TabsTrigger value="testimonials" className="text-sm">
                <Quote className="w-4 h-4 mr-2" />
                Testimonials
              </TabsTrigger>
              <TabsTrigger value="references" className="text-sm">
                <Globe className="w-4 h-4 mr-2" />
                References
              </TabsTrigger>
            </TabsList>

            <TabsContent value="brand">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Brand Colors */}
                <div className="bg-gray-50 rounded-xl p-5">
                  <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
                    <Palette className="w-4 h-4 mr-2 text-[#321a75]" />
                    Brand Colors
                  </h4>
                  <div className="flex flex-wrap gap-3">
                    {data.brand_guidelines.brand_colors.map((color, index) => (
                      <div key={index} className="flex flex-col items-center">
                        <div
                          className="w-16 h-16 rounded-xl shadow-sm border border-gray-200"
                          style={{ backgroundColor: color }}
                        />
                        <span className="text-xs text-gray-500 mt-1">{color}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Tone of Voice */}
                <div className="bg-gray-50 rounded-xl p-5">
                  <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
                    <Megaphone className="w-4 h-4 mr-2 text-[#00c3c4]" />
                    Tone of Voice
                  </h4>
                  <p className="text-sm text-gray-600">{data.brand_guidelines.tone_of_voice}</p>
                </div>

                {/* Messaging Guidelines */}
                <div className="bg-gray-50 rounded-xl p-5 md:col-span-2">
                  <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
                    <FileText className="w-4 h-4 mr-2 text-[#faab00]" />
                    Messaging Guidelines
                  </h4>
                  <p className="text-sm text-gray-600">{data.brand_guidelines.messaging_guidelines}</p>
                </div>

                {/* Approved Assets */}
                <div className="bg-gray-50 rounded-xl p-5 md:col-span-2">
                  <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
                    <Image className="w-4 h-4 mr-2 text-[#321a75]" />
                    Approved Assets
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {data.brand_guidelines.approved_assets.map((asset, index) => (
                      <Badge key={index} variant="secondary" className="bg-white">
                        {asset}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="success">
              {canEdit && (
                <div className="mb-4">
                  {!showAddStory ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowAddStory(true)}
                      className="flex items-center gap-2"
                    >
                      <Plus className="w-4 h-4" />
                      Add Success Story
                    </Button>
                  ) : (
                    <div className="p-4 bg-gray-50 rounded-lg border space-y-3">
                      <Input
                        placeholder="Title"
                        value={newStory.title}
                        onChange={(e) => setNewStory({ ...newStory, title: e.target.value })}
                      />
                      <Input
                        placeholder="Description"
                        value={newStory.description}
                        onChange={(e) => setNewStory({ ...newStory, description: e.target.value })}
                      />
                      <div className="flex gap-2">
                        <Button size="sm" onClick={handleAddStory} disabled={isSaving}>
                          {isSaving ? 'Adding...' : 'Add'}
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => setShowAddStory(false)}>
                          Cancel
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              )}
              <CollapsibleList
                items={data.success_stories}
                renderItem={(story) => (
                  <div
                    key={story.id}
                    className="p-4 rounded-xl bg-gray-50 border border-gray-100"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-4">
                        <div className="w-10 h-10 rounded-lg bg-[#faab00]/10 flex items-center justify-center text-[#faab00]">
                          <Trophy className="w-5 h-5" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            <h4 className="font-semibold text-gray-900">{story.title}</h4>
                            <Badge variant="outline" className={cn('text-xs', getApprovalStatusColor(story.approval_status))}>
                              {story.approval_status}
                            </Badge>
                            {story.case_study_eligible && (
                              <Badge variant="secondary" className="bg-emerald-100 text-emerald-700 text-xs">
                                Case Study Eligible
                              </Badge>
                            )}
                          </div>
                          <p className="text-sm text-gray-600 mt-1">{story.description}</p>
                          <div className="flex flex-wrap gap-3 mt-3">
                            {Object.entries(story.metrics).map(([key, value]) => (
                              <div key={key} className="bg-white px-3 py-1.5 rounded-lg border border-gray-200">
                                <span className="text-xs text-gray-500 capitalize">{key.replace('_', ' ')}</span>
                                <p className="text-sm font-semibold text-gray-900">{value}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                initialDisplayCount={3}
                maxHeight="400px"
              />
            </TabsContent>

            <TabsContent value="testimonials">
              {canEdit && (
                <div className="mb-4">
                  {!showAddTestimonial ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowAddTestimonial(true)}
                      className="flex items-center gap-2"
                    >
                      <Plus className="w-4 h-4" />
                      Add Testimonial
                    </Button>
                  ) : (
                    <div className="p-4 bg-gray-50 rounded-lg border space-y-3">
                      <Input
                        placeholder="Person Name"
                        value={newTestimonial.from_person}
                        onChange={(e) => setNewTestimonial({ ...newTestimonial, from_person: e.target.value })}
                      />
                      <Input
                        placeholder="Quote"
                        value={newTestimonial.quote}
                        onChange={(e) => setNewTestimonial({ ...newTestimonial, quote: e.target.value })}
                      />
                      <div className="flex gap-2">
                        <Button size="sm" onClick={handleAddTestimonial} disabled={isSaving}>
                          {isSaving ? 'Adding...' : 'Add'}
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => setShowAddTestimonial(false)}>
                          Cancel
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              )}
              <CollapsibleList
                items={data.testimonials}
                renderItem={(testimonial) => (
                  <div
                    key={testimonial.id}
                    className="p-5 rounded-xl bg-gradient-to-br from-gray-50 to-gray-100 border border-gray-100"
                  >
                    <div className="flex items-start space-x-1 mb-4">
                      <Quote className="w-6 h-6 text-[#321a75]/30" />
                    </div>
                    <p className="text-gray-700 italic mb-4 leading-relaxed">
                      &ldquo;{testimonial.quote}&rdquo;
                    </p>
                    <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                      <div>
                        <p className="font-semibold text-gray-900">{testimonial.author}</p>
                        <p className="text-sm text-gray-500">{testimonial.role}</p>
                      </div>
                      <div className="text-right">
                        <Badge variant="outline" className={cn('text-xs', getApprovalStatusColor(testimonial.approval_status))}>
                          {testimonial.approval_status}
                        </Badge>
                        <p className="text-xs text-gray-400 mt-1">{testimonial.date}</p>
                      </div>
                    </div>
                  </div>
                )}
                initialDisplayCount={4}
                maxHeight="400px"
                className="grid grid-cols-1 md:grid-cols-2 gap-4"
              />
            </TabsContent>

            <TabsContent value="references">
              {canEdit && (
                <div className="mb-4">
                  {!showAddReference ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowAddReference(true)}
                      className="flex items-center gap-2"
                    >
                      <Plus className="w-4 h-4" />
                      Add Public Reference
                    </Button>
                  ) : (
                    <div className="p-4 bg-gray-50 rounded-lg border space-y-3">
                      <Input
                        placeholder="Title"
                        value={newReference.title}
                        onChange={(e) => setNewReference({ ...newReference, title: e.target.value })}
                      />
                      <select
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                        value={newReference.type}
                        onChange={(e) => setNewReference({ ...newReference, type: e.target.value })}
                      >
                        <option value="blog_post">Blog Post</option>
                        <option value="press_release">Press Release</option>
                        <option value="social_media">Social Media</option>
                        <option value="event">Event</option>
                      </select>
                      <Input
                        placeholder="URL (optional)"
                        value={newReference.url}
                        onChange={(e) => setNewReference({ ...newReference, url: e.target.value })}
                      />
                      <div className="flex gap-2">
                        <Button size="sm" onClick={handleAddReference} disabled={isSaving}>
                          {isSaving ? 'Adding...' : 'Add'}
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => setShowAddReference(false)}>
                          Cancel
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              )}
              <CollapsibleList
                items={data.public_references}
                renderItem={(reference) => (
                  <div
                    key={reference.id}
                    className="p-4 rounded-xl bg-gray-50 border border-gray-100 flex items-center justify-between"
                  >
                    <div className="flex items-start space-x-4">
                      <div className="w-10 h-10 rounded-lg bg-[#321a75]/10 flex items-center justify-center text-[#321a75]">
                        {getReferenceTypeIcon(reference.type)}
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <h4 className="font-semibold text-gray-900">{reference.title}</h4>
                          <Badge variant="outline" className={cn(
                            'text-xs',
                            reference.status === 'published' && 'bg-blue-100 text-blue-700 border-blue-200',
                            reference.status === 'planned' && 'bg-purple-100 text-purple-700 border-purple-200',
                          )}>
                            {reference.status}
                          </Badge>
                        </div>
                        <div className="flex items-center space-x-3 mt-2 text-sm text-gray-500">
                          <span className="capitalize">{reference.type.replace('_', ' ')}</span>
                          <span>•</span>
                          <span>{reference.date}</span>
                        </div>
                      </div>
                    </div>
                    {reference.url && (
                      <a
                        href={reference.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-2 rounded-lg bg-white border border-gray-200 hover:border-[#321a75]/30 transition-colors"
                      >
                        <ExternalLink className="w-4 h-4 text-gray-500" />
                      </a>
                    )}
                  </div>
                )}
                initialDisplayCount={5}
                maxHeight="400px"
              />
            </TabsContent>
          </Tabs>
        </CardContent>
      )}
    </Card>
  );
}
