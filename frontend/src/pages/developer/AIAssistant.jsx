import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { MessageSquare, Bot, User, Trash2, Plus } from 'lucide-react';
import api from '../../api/axios';
import Swal from 'sweetalert2';

// simple markdown renderer component
const MarkdownMessage = ({ content }) => {
    const renderContent = () => {
        let html = content;

        // code blocks with triple backticks
        html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
            return `<pre class="bg-[#1A1F2E] border border-gray-700 rounded p-3 text-sm my-2 overflow-x-auto"><code class="text-gray-300">${code.trim()}</code></pre>`;
        });

        // inline code
        html = html.replace(/`([^`]+)`/g, '<code class="bg-[#1A1F2E] px-1.5 py-0.5 rounded text-sm font-mono text-orange-400">$1</code>');

        // bold
        html = html.replace(/\*\*([^*]+)\*\*/g, '<strong class="font-bold text-gray-200">$1</strong>');

        // italic
        html = html.replace(/\*([^*]+)\*/g, '<em class="italic text-gray-300">$1</em>');

        // headers
        html = html.replace(/^### (.+)$/gm, '<h3 class="text-base font-bold mt-3 mb-1 text-gray-200">$1</h3>');
        html = html.replace(/^## (.+)$/gm, '<h2 class="text-lg font-bold mt-4 mb-2 text-gray-100">$1</h2>');
        html = html.replace(/^# (.+)$/gm, '<h1 class="text-xl font-bold mt-4 mb-2 text-white">$1</h1>');

        // bullet points
        html = html.replace(/^\* (.+)$/gm, '<li class="ml-4 text-gray-300">• $1</li>');
        html = html.replace(/^- (.+)$/gm, '<li class="ml-4 text-gray-300">• $1</li>');

        // line breaks
        html = html.replace(/\n/g, '<br/>');

        return html;
    };

    return (
        <div
            className="prose prose-sm max-w-none text-gray-300"
            dangerouslySetInnerHTML={{ __html: renderContent() }}
        />
    );
};

const AIAssistant = () => {
    const { findingId } = useParams();
    const navigate = useNavigate();
    const messagesEndRef = useRef(null);

    const [conversations, setConversations] = useState([]);
    const [currentConversationId, setCurrentConversationId] = useState(null);
    const [finding, setFinding] = useState(null);
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [initializing, setInitializing] = useState(true);
    const [loadingConversations, setLoadingConversations] = useState(true);

    useEffect(() => {
        fetchConversations();
    }, []);

    useEffect(() => {
        if (findingId) {
            initializeChat();
        } else {
            setInitializing(false);
        }
    }, [findingId]);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const fetchConversations = async () => {
        try {
            const response = await api.get('/chat/conversations');
            setConversations(response.data.conversations);
        } catch (error) {
            toast.error('Failed to load conversation history');
        } finally {
            setLoadingConversations(false);
        }
    };

    const initializeChat = async () => {
        if (!findingId) {
            setInitializing(false);
            return;
        }

        try {
            const response = await api.post(`/chat/findings/${findingId}/chat/init`);

            if (response.data.messages) {
                setMessages(response.data.messages);
            } else {
                setMessages([{
                    role: 'system',
                    content: response.data.initial_message,
                    created_at: new Date().toISOString()
                }]);
            }

            setCurrentConversationId(response.data.conversation_id);
            setFinding({ id: findingId });

            // refresh conversations list to show new conversation
            fetchConversations();
        } catch (error) {
            toast.error('Failed to initialize AI assistant. Please try again.');
        } finally {
            setInitializing(false);
        }
    };

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim() || loading || !findingId) return;

        const userMessage = input.trim();
        setInput('');

        const newUserMessage = {
            role: 'user',
            content: userMessage,
            created_at: new Date().toISOString()
        };
        setMessages(prev => [...prev, newUserMessage]);
        setLoading(true);

        try {
            const response = await api.post(`/chat/findings/${findingId}/chat`, {
                message: userMessage
            });

            setMessages(prev => [...prev, {
                role: 'assistant',
                content: response.data.reply,
                created_at: new Date().toISOString()
            }]);

            // refresh conversations to update last message
            fetchConversations();
        } catch (error) {
            toast.error('Failed to send message. Please try again.');
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Sorry, I encountered an error. Please try again.',
                created_at: new Date().toISOString()
            }]);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteConversation = async (conversationId) => {
        const result = await Swal.fire({
            title: 'Delete Conversation?',
            text: 'This will permanently delete this conversation and all messages.',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#ef4444',
            cancelButtonColor: '#6b7280',
            confirmButtonText: 'Yes, delete it',
            cancelButtonText: 'Cancel',
            background: '#05080C',
            color: '#fff'
        });

        if (result.isConfirmed) {
            try {
                await api.delete(`/chat/conversations/${conversationId}`);
                toast.success('Conversation deleted');

                // removing from list
                setConversations(prev => prev.filter(c => c.conversation_id !== conversationId));

                // if deleting current conversation, clear chat
                if (currentConversationId === conversationId) {
                    navigate('/dev-dashboard/ai-assistant');
                    setMessages([]);
                    setCurrentConversationId(null);
                    setFinding(null);
                }
            } catch (error) {
                toast.error('Failed to delete conversation');
            }
        }
    };

    const handleSelectConversation = (conv) => {
        navigate(`/dev-dashboard/ai-assistant/${conv.finding_id}`);
    };

    const getSeverityColor = (severity) => {
        const colors = {
            critical: 'text-red-400',
            high: 'text-orange-400',
            medium: 'text-yellow-400',
            low: 'text-blue-400'
        };
        return colors[severity] || 'text-gray-400';
    };

    if (initializing) {
        return (
            <div className="flex items-center justify-center h-screen bg-[#0A0F16]">
                <div className="text-center">
                    <span className="loading loading-spinner loading-lg text-purple-500"></span>
                    <p className="mt-4 text-gray-400">Loading AI Assistant...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex h-screen bg-[#0A0F16]">
            {/* Left Sidebar - Conversations List */}
            <div className="w-80 bg-[#05080C] border-r border-white/10 flex flex-col">
                {/* Sidebar Header */}
                <div className="p-4 border-b border-white/10">
                    <h2 className="text-lg font-bold text-white flex items-center gap-2">
                        <Bot className="w-5 h-5 text-purple-400" />
                        AI Assistant
                    </h2>
                    <p className="text-xs text-gray-500 mt-1">Security Chat History</p>
                </div>

                {/* Conversations List */}
                <div className="flex-1 overflow-y-auto p-3 space-y-2">
                    {loadingConversations ? (
                        <div className="flex items-center justify-center py-8">
                            <span className="loading loading-spinner loading-md text-purple-500"></span>
                        </div>
                    ) : conversations.length === 0 ? (
                        <div className="text-center py-8 px-4">
                            <MessageSquare className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                            <p className="text-sm text-gray-500">No conversations yet</p>
                            <p className="text-xs text-gray-600 mt-1">Click "Ask AI" on any security finding to start</p>
                        </div>
                    ) : (
                        conversations.map((conv) => (
                            <div
                                key={conv.conversation_id}
                                className={`group p-3 rounded-lg cursor-pointer transition-all hover:bg-white/5 ${currentConversationId === conv.conversation_id
                                    ? 'bg-purple-500/10 border border-purple-500/30'
                                    : 'border border-transparent'
                                    }`}
                                onClick={() => handleSelectConversation(conv)}
                            >
                                <div className="flex items-start justify-between gap-2">
                                    <div className="flex-1 min-w-0">
                                        <h3 className="text-sm font-medium text-white truncate">
                                            {conv.finding_title}
                                        </h3>
                                        <p className={`text-xs ${getSeverityColor(conv.finding_severity)} mt-0.5`}>
                                            {conv.finding_severity?.toUpperCase()}
                                        </p>
                                        {conv.last_message && (
                                            <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                                                {conv.last_message}...
                                            </p>
                                        )}
                                        <div className="flex items-center gap-2 mt-2 text-xs text-gray-600">
                                            <MessageSquare className="w-3 h-3" />
                                            {conv.message_count} messages
                                        </div>
                                    </div>
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleDeleteConversation(conv.conversation_id);
                                        }}
                                        className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-500/20 rounded transition-all"
                                    >
                                        <Trash2 className="w-4 h-4 text-red-400" />
                                    </button>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col">
                {!findingId ? (
                    /* Empty State */
                    <div className="flex-1 flex items-center justify-center">
                        <div className="text-center max-w-md px-6">
                            <Bot className="w-20 h-20 text-purple-400 mx-auto mb-4" />
                            <h2 className="text-2xl font-bold text-white mb-2">AI Security Assistant</h2>
                            <p className="text-gray-400 mb-6">
                                Get AI-powered help fixing security vulnerabilities with context-aware suggestions
                            </p>
                            <div className="text-sm text-gray-500 space-y-2">
                                <p>• Powered by Groq Llama 3.3 70B</p>
                                <p>• RAG with OWASP/CWE knowledge base</p>
                                <p>• Code-aware recommendations</p>
                            </div>
                            <p className="text-sm text-gray-600 mt-6">
                                Select a conversation from the sidebar or click "Ask AI" on any security finding to start
                            </p>
                        </div>
                    </div>
                ) : (
                    <>
                        {/* Chat Header */}
                        <div className="bg-[#05080C] p-4 border-b border-white/10">
                            <h1 className="text-lg font-bold text-white">Security Finding Chat</h1>
                            <p className="text-sm text-purple-400">Powered by RAG + Llama 3.3 70B</p>
                        </div>

                        <div className="flex-1 overflow-y-auto p-6 space-y-6">
                            {messages.map((msg, idx) => (
                                <div key={idx} className="flex gap-3">
                                    <div className="flex-shrink-0">
                                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${msg.role === 'user'
                                            ? 'bg-purple-500/20'
                                            : 'bg-gray-700'
                                            }`}>
                                            {msg.role === 'user' ? (
                                                <User className="w-4 h-4 text-purple-400" />
                                            ) : (
                                                <Bot className="w-4 h-4 text-gray-300" />
                                            )}
                                        </div>
                                    </div>

                                    {/* Message Content */}
                                    <div className="flex-1 min-w-0">
                                        <div className="text-xs text-gray-500 mb-1">
                                            {msg.role === 'system' ? 'System' : msg.role === 'user' ? 'You' : 'AI Assistant'}
                                        </div>
                                        <div className={`${msg.role === 'user'
                                            ? 'text-gray-200'
                                            : 'text-gray-300'
                                            }`}>
                                            {msg.role === 'user' ? (
                                                <div className="whitespace-pre-wrap">{msg.content}</div>
                                            ) : (
                                                <MarkdownMessage content={msg.content} />
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}

                            {loading && (
                                <div className="flex gap-3">
                                    <div className="flex-shrink-0">
                                        <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center">
                                            <Bot className="w-4 h-4 text-gray-300 animate-pulse" />
                                        </div>
                                    </div>
                                    <div className="flex-1">
                                        <div className="text-xs text-gray-500 mb-1">AI Assistant</div>
                                        <span className="loading loading-dots loading-sm text-purple-400"></span>
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>

                        <form onSubmit={handleSend} className="bg-[#05080C] p-4 border-t border-white/10">
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    placeholder="Ask about this vulnerability..."
                                    disabled={loading}
                                    className="flex-1 px-4 py-3 bg-[#0A0F16] border border-gray-700 rounded-lg text-white placeholder-gray-600 focus:outline-none focus:border-purple-500"
                                />
                                <button
                                    type="submit"
                                    disabled={loading || !input.trim()}
                                    className="px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors"
                                >
                                    Send
                                </button>
                            </div>
                        </form>
                    </>
                )}
            </div>
        </div>
    );
};

export default AIAssistant;
