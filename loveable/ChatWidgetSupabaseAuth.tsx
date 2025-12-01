/**
 * Undeniable AI Chat Widget for Lovable with Supabase Auth
 *
 * This component integrates with your existing Lovable/Supabase setup
 * Drop-in replacement for your current chat implementation
 */

import React, { useState, useEffect, useRef } from 'react';
import { marked } from 'marked';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

interface Conversation {
  conversation_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

interface ChatWidgetProps {
  apiUrl?: string;
  className?: string;
}

export default function ChatWidget({
  apiUrl = 'https://ucxai-production.up.railway.app',
  className = ''
}: ChatWidgetProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [user, setUser] = useState<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  // Example prompts
  const examplePrompts = [
    'How do I raise prices without losing clients',
    'Help me design an irresistible high-ticket offer',
    "What's killing my profit margins right now?",
    'How can I double my LTV with my current clients'
  ];

  // Get authenticated user
  useEffect(() => {
    const getUser = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (session?.user) {
        setUser(session.user);
      }
    };
    getUser();

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user || null);
    });

    return () => subscription.unsubscribe();
  }, []);

  // Load user conversations when user is available
  useEffect(() => {
    if (user?.id) {
      loadUserConversations();
    }
  }, [user]);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadUserConversations = async () => {
    if (!user?.id) return;

    try {
      const response = await fetch(`${apiUrl}/api/users/${user.id}/conversations`);
      if (response.ok) {
        const data = await response.json();
        setConversations(data.conversations || []);

        // Load most recent conversation if none selected
        if (data.conversations?.length > 0 && !currentConversationId) {
          loadConversation(data.conversations[0].conversation_id);
        }
      }
    } catch (error) {
      console.error('Error loading conversations:', error);
      toast({
        title: 'Error',
        description: 'Failed to load conversations',
        variant: 'destructive'
      });
    }
  };

  const loadConversation = async (conversationId: string) => {
    setCurrentConversationId(conversationId);
    setMessages([]);

    try {
      const response = await fetch(`${apiUrl}/api/conversations/${conversationId}`);
      if (response.ok) {
        const data = await response.json();
        const formattedMessages = data.messages
          .filter((msg: any) => msg.role !== 'system')
          .map((msg: any) => ({
            role: msg.role,
            content: msg.content,
            timestamp: msg.created_at
          }));
        setMessages(formattedMessages);
      }
    } catch (error) {
      console.error('Error loading conversation:', error);
      toast({
        title: 'Error',
        description: 'Failed to load conversation',
        variant: 'destructive'
      });
    }
  };

  const newConversation = () => {
    setCurrentConversationId(null);
    setMessages([]);
  };

  const sendMessage = async (messageText?: string) => {
    const message = messageText || inputValue.trim();
    if (!message || loading || !user) return;

    setLoading(true);
    setInputValue('');

    // Add user message to UI
    const userMessage: Message = { role: 'user', content: message };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await fetch(`${apiUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          conversation_id: currentConversationId,
          loveable_user_id: user.id,
          email: user.email,
          display_name: user.email, // Use email as display name since no name field
          use_rag: true
        })
      });

      if (response.ok) {
        const data = await response.json();

        // Add assistant response
        const assistantMessage: Message = {
          role: 'assistant',
          content: data.response
        };
        setMessages(prev => [...prev, assistantMessage]);

        // Update conversation ID if this was a new conversation
        if (!currentConversationId) {
          setCurrentConversationId(data.conversation_id);
          // Reload conversations to update sidebar
          setTimeout(loadUserConversations, 500);
        }
      } else {
        const error = await response.json();
        toast({
          title: 'Error',
          description: error.detail || 'Failed to send message',
          variant: 'destructive'
        });
      }
    } catch (error) {
      toast({
        title: 'Connection Error',
        description: 'Failed to connect to AI service',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const deleteConversation = async (conversationId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Delete this conversation?')) return;

    try {
      const response = await fetch(`${apiUrl}/api/conversations/${conversationId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        // Reload conversations
        loadUserConversations();

        // Clear current conversation if deleted
        if (conversationId === currentConversationId) {
          newConversation();
        }

        toast({
          title: 'Success',
          description: 'Conversation deleted'
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete conversation',
        variant: 'destructive'
      });
    }
  };

  if (!user) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#343541] text-white">
        <div className="text-center">
          <h2 className="text-xl mb-4">Please log in to use the chat</h2>
          <p className="text-sm text-gray-400">Redirecting to login...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex h-screen bg-[#343541] text-white font-sans ${className}`}>
      {/* Sidebar */}
      {sidebarOpen && (
        <div className="w-64 bg-[#202123] border-r border-[#4d4d4f] flex flex-col">
          <div className="p-3">
            <button
              onClick={newConversation}
              className="w-full p-3 bg-transparent border border-[#565869] text-white rounded-md hover:bg-[#343541] transition-colors"
            >
              + New chat
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-2">
            {conversations.map(conv => (
              <div
                key={conv.conversation_id}
                onClick={() => loadConversation(conv.conversation_id)}
                className={`p-3 m-1 rounded-md cursor-pointer transition-colors flex justify-between items-center ${
                  conv.conversation_id === currentConversationId ? 'bg-[#343541]' : 'hover:bg-[#343541]'
                }`}
              >
                <span className="flex-1 text-sm truncate">{conv.title}</span>
                <button
                  onClick={(e) => deleteConversation(conv.conversation_id, e)}
                  className="text-[#8e8ea0] hover:text-white text-xl ml-2 px-1"
                  title="Delete conversation"
                >
                  ×
                </button>
              </div>
            ))}
          </div>

          <div className="p-3 border-t border-[#4d4d4f] text-xs text-gray-400">
            <p>{user.email}</p>
            <p className="mt-1">Undeniable AI v1.0</p>
          </div>
        </div>
      )}

      {/* Main chat area */}
      <div className="flex-1 flex flex-col">
        <div className="p-4 border-b border-[#4d4d4f] flex items-center gap-3">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-xl hover:text-gray-300"
          >
            ☰
          </button>
          <span className="font-medium">Undeniable AI</span>
        </div>

        <div className="flex-1 overflow-y-auto p-5">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <h1 className="text-3xl mb-8">Undeniable AI</h1>
              <div className="flex flex-wrap gap-3 max-w-3xl">
                {examplePrompts.map((prompt, i) => (
                  <div
                    key={i}
                    onClick={() => sendMessage(prompt)}
                    className="flex-1 min-w-[200px] p-3 bg-[#444654] border border-[#565869] rounded-lg cursor-pointer hover:bg-[#565869] transition-colors"
                  >
                    {prompt}
                  </div>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`mb-6 flex gap-4 ${msg.role === 'assistant' ? 'bg-[#444654] -mx-5 px-5 py-5' : ''}`}
            >
              <div
                className={`w-8 h-8 rounded-sm flex items-center justify-center flex-shrink-0 font-semibold ${
                  msg.role === 'user' ? 'bg-[#5436DA]' : 'bg-[#19c37d]'
                }`}
              >
                {msg.role === 'user' ? 'U' : 'AI'}
              </div>
              <div
                className="flex-1 max-w-3xl leading-7"
                dangerouslySetInnerHTML={{
                  __html: msg.role === 'assistant'
                    ? marked.parse(msg.content)
                    : msg.content
                }}
              />
            </div>
          ))}

          {loading && (
            <div className="mb-6 flex gap-4 bg-[#444654] -mx-5 px-5 py-5">
              <div className="w-8 h-8 rounded-sm flex items-center justify-center flex-shrink-0 font-semibold bg-[#19c37d]">
                AI
              </div>
              <div className="flex-1">
                <div className="inline-block w-5 h-5 border-2 border-[#565869] border-t-[#19c37d] rounded-full animate-spin" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="p-5 bg-[#343541]">
          <div className="max-w-3xl mx-auto">
            {messages.length === 0 && (
              <div className="flex gap-2 mb-3 flex-wrap">
                {examplePrompts.map((prompt, i) => (
                  <div
                    key={i}
                    onClick={() => sendMessage(prompt)}
                    className="flex-1 min-w-[180px] px-3 py-2 bg-[#40414f] border border-[#565869] rounded-lg text-sm cursor-pointer hover:bg-[#565869] transition-colors text-center"
                  >
                    {prompt}
                  </div>
                ))}
              </div>
            )}

            <div className="relative bg-[#40414f] rounded-xl border border-[#565869] px-4 py-3 flex items-center">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Message Undeniable AI..."
                disabled={loading}
                className="flex-1 bg-transparent border-none outline-none text-base"
              />
              <button
                onClick={() => sendMessage()}
                disabled={loading || !inputValue.trim()}
                className="ml-2 w-8 h-8 flex items-center justify-center text-[#8e8ea0] hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
