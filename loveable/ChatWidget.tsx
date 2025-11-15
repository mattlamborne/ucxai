/**
 * Undeniable AI Chat Widget for Loveable
 *
 * Usage in Loveable:
 *
 * import ChatWidget from './ChatWidget';
 *
 * function MyPage() {
 *   const { user } = useAuth(); // Your Loveable auth hook
 *
 *   return (
 *     <ChatWidget
 *       loveableUserId={user?.id}
 *       email={user?.email}
 *       displayName={user?.name}
 *       apiUrl="https://ucxai-production.up.railway.app"
 *     />
 *   );
 * }
 */

import React, { useState, useEffect, useRef } from 'react';
import { marked } from 'marked';

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
  loveableUserId?: string;
  email?: string;
  displayName?: string;
  apiUrl?: string;
  className?: string;
}

export default function ChatWidget({
  loveableUserId,
  email,
  displayName,
  apiUrl = 'https://ucxai-production.up.railway.app',
  className = ''
}: ChatWidgetProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Example prompts
  const examplePrompts = [
    'How do i raise prices without losing clients',
    'Help me design an irresistible high-ticket offer',
    "What's killing my profit margins right now?",
    'How can i double my LTV with my current clients'
  ];

  // Load user conversations on mount
  useEffect(() => {
    if (loveableUserId) {
      loadUserConversations();
    }
  }, [loveableUserId]);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadUserConversations = async () => {
    if (!loveableUserId) return;

    try {
      const response = await fetch(`${apiUrl}/api/users/${loveableUserId}/conversations`);
      if (response.ok) {
        const data = await response.json();
        setConversations(data.conversations || []);

        // Load most recent conversation
        if (data.conversations?.length > 0 && !currentConversationId) {
          loadConversation(data.conversations[0].conversation_id);
        }
      }
    } catch (error) {
      console.error('Error loading conversations:', error);
    }
  };

  const loadConversation = async (conversationId: string) => {
    setCurrentConversationId(conversationId);
    setMessages([]);

    try {
      const response = await fetch(`${apiUrl}/api/conversations/${conversationId}`);
      if (response.ok) {
        const data = await response.json();
        const formattedMessages = data.messages.map((msg: any) => ({
          role: msg.role,
          content: msg.content,
          timestamp: msg.created_at
        }));
        setMessages(formattedMessages);
      }
    } catch (error) {
      console.error('Error loading conversation:', error);
    }
  };

  const newConversation = () => {
    setCurrentConversationId(null);
    setMessages([]);
  };

  const sendMessage = async (messageText?: string) => {
    const message = messageText || inputValue.trim();
    if (!message || loading) return;

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
          loveable_user_id: loveableUserId,
          email,
          display_name: displayName,
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
          if (loveableUserId) {
            setTimeout(loadUserConversations, 500);
          }
        }
      } else {
        const error = await response.json();
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `Error: ${error.detail || 'Unknown error'}`
        }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Connection error: ${error}`
      }]);
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

  const deleteConversation = async (conversationId: string) => {
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
      }
    } catch (error) {
      console.error('Error deleting conversation:', error);
    }
  };

  return (
    <div className={`chat-widget ${className}`} style={styles.container}>
      {/* Sidebar */}
      {loveableUserId && sidebarOpen && (
        <div style={styles.sidebar}>
          <div style={styles.sidebarHeader}>
            <button onClick={newConversation} style={styles.newChatBtn}>
              + New chat
            </button>
          </div>

          <div style={styles.conversations}>
            {conversations.map(conv => (
              <div
                key={conv.conversation_id}
                onClick={() => loadConversation(conv.conversation_id)}
                style={{
                  ...styles.conversationItem,
                  ...(conv.conversation_id === currentConversationId ? styles.conversationItemActive : {})
                }}
              >
                <span style={styles.conversationTitle}>{conv.title}</span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteConversation(conv.conversation_id);
                  }}
                  style={styles.deleteBtn}
                  title="Delete conversation"
                >
                  ×
                </button>
              </div>
            ))}
          </div>

          <div style={styles.sidebarFooter}>
            Undeniable AI v1.0
          </div>
        </div>
      )}

      {/* Main chat area */}
      <div style={styles.main}>
        <div style={styles.chatHeader}>
          {loveableUserId && (
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              style={styles.toggleSidebar}
            >
              ☰
            </button>
          )}
          <span>Undeniable AI</span>
        </div>

        <div style={styles.messages}>
          {messages.length === 0 && (
            <div style={styles.emptyState}>
              <h1 style={styles.emptyStateTitle}>Undeniable AI</h1>
              <div style={styles.examplePrompts}>
                {examplePrompts.map((prompt, i) => (
                  <div
                    key={i}
                    onClick={() => sendMessage(prompt)}
                    style={styles.examplePrompt}
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
              style={{
                ...styles.message,
                ...(msg.role === 'assistant' ? styles.messageAssistant : {})
              }}
            >
              <div style={{
                ...styles.messageAvatar,
                ...(msg.role === 'user' ? styles.messageAvatarUser : styles.messageAvatarAssistant)
              }}>
                {msg.role === 'user' ? 'U' : 'AI'}
              </div>
              <div
                style={styles.messageContent}
                dangerouslySetInnerHTML={{
                  __html: msg.role === 'assistant'
                    ? marked.parse(msg.content)
                    : msg.content
                }}
              />
            </div>
          ))}

          {loading && (
            <div style={{ ...styles.message, ...styles.messageAssistant }}>
              <div style={{ ...styles.messageAvatar, ...styles.messageAvatarAssistant }}>
                AI
              </div>
              <div style={styles.messageContent}>
                <div style={styles.loading}></div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div style={styles.inputArea}>
          <div style={styles.inputContainer}>
            {messages.length === 0 && (
              <div style={styles.quickPrompts}>
                {examplePrompts.map((prompt, i) => (
                  <div
                    key={i}
                    onClick={() => sendMessage(prompt)}
                    style={styles.quickPrompt}
                  >
                    {prompt}
                  </div>
                ))}
              </div>
            )}

            <div style={styles.inputWrapper}>
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Message Undeniable AI..."
                disabled={loading}
                style={styles.input}
              />
              <button
                onClick={() => sendMessage()}
                disabled={loading || !inputValue.trim()}
                style={styles.sendBtn}
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

// Inline styles (ChatGPT-inspired dark theme)
const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    height: '100vh',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    backgroundColor: '#343541',
    color: '#ececf1'
  },
  sidebar: {
    width: '260px',
    backgroundColor: '#202123',
    borderRight: '1px solid #4d4d4f',
    display: 'flex',
    flexDirection: 'column'
  },
  sidebarHeader: {
    padding: '12px'
  },
  newChatBtn: {
    width: '100%',
    padding: '12px',
    background: 'transparent',
    border: '1px solid #565869',
    color: 'white',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '14px'
  },
  conversations: {
    flex: 1,
    overflowY: 'auto',
    padding: '8px'
  },
  conversationItem: {
    padding: '12px',
    margin: '4px 0',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '14px',
    transition: 'background 0.2s',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  conversationItemActive: {
    backgroundColor: '#343541'
  },
  conversationTitle: {
    flex: 1,
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis'
  },
  deleteBtn: {
    background: 'none',
    border: 'none',
    color: '#8e8ea0',
    fontSize: '20px',
    cursor: 'pointer',
    padding: '0 4px',
    marginLeft: '8px'
  },
  sidebarFooter: {
    padding: '12px',
    borderTop: '1px solid #4d4d4f',
    fontSize: '12px'
  },
  main: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#343541'
  },
  chatHeader: {
    padding: '16px 20px',
    borderBottom: '1px solid #4d4d4f',
    fontSize: '14px',
    fontWeight: 500,
    display: 'flex',
    alignItems: 'center',
    gap: '12px'
  },
  toggleSidebar: {
    background: 'none',
    border: 'none',
    color: 'white',
    fontSize: '20px',
    cursor: 'pointer',
    padding: '0'
  },
  messages: {
    flex: 1,
    overflowY: 'auto',
    padding: '20px'
  },
  message: {
    marginBottom: '24px',
    display: 'flex',
    gap: '16px'
  },
  messageAssistant: {
    backgroundColor: '#444654',
    margin: '0 -20px 24px',
    padding: '20px'
  },
  messageAvatar: {
    width: '30px',
    height: '30px',
    borderRadius: '2px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 600,
    fontSize: '14px',
    flexShrink: 0
  },
  messageAvatarUser: {
    backgroundColor: '#5436DA',
    color: 'white'
  },
  messageAvatarAssistant: {
    backgroundColor: '#19c37d',
    color: 'white'
  },
  messageContent: {
    flex: 1,
    lineHeight: 1.7,
    maxWidth: '800px'
  },
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    textAlign: 'center'
  },
  emptyStateTitle: {
    fontSize: '32px',
    marginBottom: '32px'
  },
  examplePrompts: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '12px',
    maxWidth: '800px'
  },
  examplePrompt: {
    padding: '12px 16px',
    backgroundColor: '#444654',
    border: '1px solid #565869',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'all 0.2s',
    fontSize: '14px',
    flex: 1,
    minWidth: '200px'
  },
  inputArea: {
    padding: '20px',
    backgroundColor: '#343541'
  },
  inputContainer: {
    maxWidth: '800px',
    margin: '0 auto'
  },
  quickPrompts: {
    display: 'flex',
    gap: '8px',
    marginBottom: '12px',
    flexWrap: 'wrap'
  },
  quickPrompt: {
    padding: '8px 14px',
    backgroundColor: '#40414f',
    border: '1px solid #565869',
    borderRadius: '8px',
    fontSize: '13px',
    cursor: 'pointer',
    transition: 'all 0.2s',
    flex: 1,
    minWidth: '180px',
    textAlign: 'center'
  },
  inputWrapper: {
    backgroundColor: '#40414f',
    borderRadius: '12px',
    border: '1px solid #565869',
    padding: '12px 50px 12px 16px',
    display: 'flex',
    alignItems: 'center',
    position: 'relative'
  },
  input: {
    flex: 1,
    background: 'transparent',
    border: 'none',
    color: 'white',
    fontSize: '16px',
    outline: 'none'
  },
  sendBtn: {
    position: 'absolute',
    right: '12px',
    width: '32px',
    height: '32px',
    background: 'transparent',
    border: 'none',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#8e8ea0',
    transition: 'color 0.2s'
  },
  loading: {
    display: 'inline-block',
    width: '20px',
    height: '20px',
    border: '3px solid #565869',
    borderTop: '3px solid #19c37d',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite'
  }
};
