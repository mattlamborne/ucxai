import React, { useState, useRef, useEffect } from 'react';

/**
 * UCX AI Chat Widget
 * Embed this component in your Lovable website
 *
 * Usage:
 * <ChatWidget apiUrl="https://your-api-url.com" />
 */

const ChatWidget = ({ apiUrl = 'http://localhost:8000' }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [isOpen, setIsOpen] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch(`${apiUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input,
          conversation_id: conversationId,
        }),
      });

      if (!response.ok) throw new Error('Failed to send message');

      const data = await response.json();

      // Set conversation ID if first message
      if (!conversationId) {
        setConversationId(data.conversation_id);
      }

      const assistantMessage = { role: 'assistant', content: data.response };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error:', error);
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.'
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setConversationId(null);
  };

  return (
    <div style={styles.container}>
      {/* Chat Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          style={styles.chatButton}
          aria-label="Open chat"
        >
          💬
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div style={styles.chatWindow}>
          {/* Header */}
          <div style={styles.header}>
            <h3 style={styles.title}>UCX AI Assistant</h3>
            <div style={styles.headerButtons}>
              <button onClick={clearChat} style={styles.clearButton}>🔄</button>
              <button onClick={() => setIsOpen(false)} style={styles.closeButton}>✕</button>
            </div>
          </div>

          {/* Messages */}
          <div style={styles.messagesContainer}>
            {messages.length === 0 && (
              <div style={styles.welcomeMessage}>
                👋 Hi! How can I help you today?
              </div>
            )}
            {messages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  ...styles.message,
                  ...(msg.role === 'user' ? styles.userMessage : styles.assistantMessage),
                }}
              >
                {msg.content}
              </div>
            ))}
            {isLoading && (
              <div style={{ ...styles.message, ...styles.assistantMessage }}>
                <div style={styles.typingIndicator}>
                  <span>●</span>
                  <span>●</span>
                  <span>●</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form onSubmit={sendMessage} style={styles.inputContainer}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message..."
              style={styles.input}
              disabled={isLoading}
            />
            <button
              type="submit"
              style={{
                ...styles.sendButton,
                ...(isLoading || !input.trim() ? styles.sendButtonDisabled : {})
              }}
              disabled={isLoading || !input.trim()}
            >
              ➤
            </button>
          </form>
        </div>
      )}
    </div>
  );
};

// Styles
const styles = {
  container: {
    position: 'fixed',
    bottom: '20px',
    right: '20px',
    zIndex: 1000,
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  chatButton: {
    width: '60px',
    height: '60px',
    borderRadius: '50%',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    fontSize: '28px',
    cursor: 'pointer',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
    transition: 'transform 0.2s',
  },
  chatWindow: {
    width: '380px',
    height: '600px',
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  header: {
    backgroundColor: '#007bff',
    color: 'white',
    padding: '16px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    margin: 0,
    fontSize: '16px',
    fontWeight: '600',
  },
  headerButtons: {
    display: 'flex',
    gap: '8px',
  },
  clearButton: {
    background: 'rgba(255, 255, 255, 0.2)',
    border: 'none',
    color: 'white',
    fontSize: '16px',
    cursor: 'pointer',
    padding: '4px 8px',
    borderRadius: '4px',
  },
  closeButton: {
    background: 'rgba(255, 255, 255, 0.2)',
    border: 'none',
    color: 'white',
    fontSize: '18px',
    cursor: 'pointer',
    padding: '4px 8px',
    borderRadius: '4px',
  },
  messagesContainer: {
    flex: 1,
    overflowY: 'auto',
    padding: '16px',
    backgroundColor: '#f8f9fa',
  },
  welcomeMessage: {
    textAlign: 'center',
    color: '#6c757d',
    padding: '20px',
    fontSize: '14px',
  },
  message: {
    marginBottom: '12px',
    padding: '10px 14px',
    borderRadius: '12px',
    maxWidth: '80%',
    fontSize: '14px',
    lineHeight: '1.4',
    wordWrap: 'break-word',
  },
  userMessage: {
    backgroundColor: '#007bff',
    color: 'white',
    marginLeft: 'auto',
    borderBottomRightRadius: '4px',
  },
  assistantMessage: {
    backgroundColor: 'white',
    color: '#212529',
    marginRight: 'auto',
    borderBottomLeftRadius: '4px',
    boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)',
  },
  inputContainer: {
    display: 'flex',
    padding: '16px',
    backgroundColor: 'white',
    borderTop: '1px solid #e9ecef',
  },
  input: {
    flex: 1,
    padding: '10px 14px',
    border: '1px solid #dee2e6',
    borderRadius: '20px',
    fontSize: '14px',
    outline: 'none',
    marginRight: '8px',
  },
  sendButton: {
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    fontSize: '18px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: '#ccc',
    cursor: 'not-allowed',
  },
  typingIndicator: {
    display: 'flex',
    gap: '4px',
  },
};

// Add typing animation
const styleSheet = document.createElement('style');
styleSheet.textContent = `
  @keyframes typing {
    0%, 60%, 100% { opacity: 0.3; }
    30% { opacity: 1; }
  }

  .typing-indicator span {
    animation: typing 1.4s infinite;
  }

  .typing-indicator span:nth-child(2) {
    animation-delay: 0.2s;
  }

  .typing-indicator span:nth-child(3) {
    animation-delay: 0.4s;
  }

  @media (max-width: 480px) {
    .chat-window {
      width: 100vw !important;
      height: 100vh !important;
      border-radius: 0 !important;
      bottom: 0 !important;
      right: 0 !important;
    }
  }
`;
document.head.appendChild(styleSheet);

export default ChatWidget;
