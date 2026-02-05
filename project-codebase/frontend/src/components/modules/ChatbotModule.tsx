import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { useStore } from '@/store/useStore';
import { chatApi } from '@/services/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Bot, Send, User, Loader2, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
}

export function ChatbotModule() {
    const { selectedClient, selectedProject } = useStore();
    const [messages, setMessages] = useState<Message[]>([
        {
            id: 'welcome',
            role: 'assistant',
            content: 'Hello! I am Nexus AI. I can help you analyze project data, identify risks, or find insights across your clients. How can I assist you today?',
            timestamp: new Date()
        }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: input,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const clientId = selectedProject?.client_id || selectedClient?.id;
            const projectId = selectedProject?.project_id || selectedProject?.id;

            const response = await chatApi.sendMessage(userMessage.content, clientId, projectId);

            if (response.success && response.data) {
                setMessages(prev => [...prev, {
                    id: (Date.now() + 1).toString(),
                    role: 'assistant',
                    content: response.data.answer,
                    timestamp: new Date()
                }]);
            } else {
                setMessages(prev => [...prev, {
                    id: (Date.now() + 1).toString(),
                    role: 'assistant',
                    content: 'I apologize, but I encountered an error processing your request. Please try again.',
                    timestamp: new Date()
                }]);
            }
        } catch (error) {
            console.error('Chat error:', error);
            setMessages(prev => [...prev, {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: 'Sorry, I am having trouble connecting to the server right now.',
                timestamp: new Date()
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-[calc(100vh-100px)] max-w-4xl mx-auto p-4">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 flex flex-col flex-1 overflow-hidden">
                {/* Chat Header */}
                <div className="p-4 border-b border-gray-100 flex items-center justify-between bg-gradient-to-r from-[#321a75]/5 to-transparent">
                    <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#321a75] to-[#00c3c4] flex items-center justify-center shadow-md">
                            <Sparkles className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <h2 className="text-lg font-bold text-gray-900">Nexus AI Assistant</h2>
                            <div className="flex items-center space-x-2 text-xs text-gray-500">
                                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                                <span>Online</span>
                                {selectedProject && (
                                    <>
                                        <span className="text-gray-300">|</span>
                                        <span>Context: {selectedProject.name}</span>
                                    </>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Messages Area */}
                <ScrollArea className="flex-1 p-4 bg-gray-50/50">
                    <div className="space-y-6 pb-4">
                        {messages.map((msg) => (
                            <div
                                key={msg.id}
                                className={cn(
                                    "flex items-start space-x-3 max-w-[85%]",
                                    msg.role === 'user' ? "ml-auto flex-row-reverse space-x-reverse" : "mr-auto"
                                )}
                            >
                                <div className={cn(
                                    "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm mt-1",
                                    msg.role === 'assistant' ? "bg-white border border-gray-100" : "bg-[#321a75] text-white"
                                )}>
                                    {msg.role === 'assistant' ? <Bot className="w-5 h-5 text-[#321a75]" /> : <User className="w-4 h-4" />}
                                </div>

                                <div className={cn(
                                    "p-4 rounded-2xl shadow-sm text-sm leading-relaxed",
                                    msg.role === 'assistant'
                                        ? "bg-white border border-gray-100 text-gray-700 rounded-tl-none"
                                        : "bg-[#321a75] text-white rounded-tr-none"
                                )}>
                                    <div className="prose prose-sm max-w-none dark:prose-invert prose-headings:text-inherit prose-p:text-inherit prose-strong:text-inherit prose-ul:text-inherit prose-ol:text-inherit">
                                        <ReactMarkdown
                                            components={{
                                                p: ({ node, ...props }: any) => <p className="mb-2 last:mb-0" {...props} />,
                                                ul: ({ node, ...props }: any) => <ul className="list-disc pl-4 mb-2 space-y-1" {...props} />,
                                                ol: ({ node, ...props }: any) => <ol className="list-decimal pl-4 mb-2 space-y-1" {...props} />,
                                                li: ({ node, ...props }: any) => <li className="mb-0.5" {...props} />,
                                                h1: ({ node, ...props }: any) => <h1 className="text-base font-bold mb-2 mt-4 first:mt-0" {...props} />,
                                                h2: ({ node, ...props }: any) => <h2 className="text-sm font-bold mb-2 mt-3 first:mt-0" {...props} />,
                                                h3: ({ node, ...props }: any) => <h3 className="text-sm font-semibold mb-1 mt-2 first:mt-0" {...props} />,
                                                strong: ({ node, ...props }: any) => <strong className="font-bold" {...props} />,
                                            }}
                                        >
                                            {msg.content}
                                        </ReactMarkdown>
                                    </div>
                                </div>
                            </div>
                        ))}
                        {isLoading && (
                            <div className="flex items-start space-x-3 mr-auto max-w-[85%]">
                                <div className="w-8 h-8 rounded-full bg-white border border-gray-100 flex items-center justify-center flex-shrink-0 shadow-sm mt-1">
                                    <Bot className="w-5 h-5 text-[#321a75]" />
                                </div>
                                <div className="bg-white border border-gray-100 p-4 rounded-2xl rounded-tl-none shadow-sm flex items-center space-x-2">
                                    <div className="w-2 h-2 bg-[#321a75]/40 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                                    <div className="w-2 h-2 bg-[#321a75]/40 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                                    <div className="w-2 h-2 bg-[#321a75]/40 rounded-full animate-bounce"></div>
                                </div>
                            </div>
                        )}
                        <div ref={scrollRef} />
                    </div>
                </ScrollArea>

                {/* Input Area */}
                <div className="p-4 bg-white border-t border-gray-100">
                    <div className="flex items-center space-x-2">
                        <Input
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
                            placeholder="Ask me anything about your projects..."
                            className="flex-1 bg-gray-50 border-gray-200 focus:bg-white transition-all h-12 rounded-xl"
                            disabled={isLoading}
                        />
                        <Button
                            onClick={handleSend}
                            disabled={!input.trim() || isLoading}
                            className="h-12 w-12 rounded-xl bg-[#321a75] hover:bg-[#2a1660] shadow-md transition-all active:scale-95"
                        >
                            {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                        </Button>
                    </div>
                    <div className="mt-2 text-center">
                        <p className="text-[10px] text-gray-400">Nexus AI can make mistakes. Consider checking important information.</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
