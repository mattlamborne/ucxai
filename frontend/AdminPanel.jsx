import React, { useState, useEffect } from 'react';

/**
 * Admin Panel for UCX AI Chatbot
 * Manage documents, upload files, and test the chatbot
 *
 * Usage in your Lovable app:
 * <AdminPanel apiUrl="https://your-api-url.com" />
 */

const AdminPanel = ({ apiUrl = 'http://localhost:8000' }) => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [documents, setDocuments] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState('');
  const [testMessage, setTestMessage] = useState('');
  const [testResponse, setTestResponse] = useState(null);
  const [activeTab, setActiveTab] = useState('documents'); // documents, upload, test

  // Check if already logged in (stored in sessionStorage)
  useEffect(() => {
    const stored = sessionStorage.getItem('admin_auth');
    if (stored) {
      try {
        const auth = JSON.parse(stored);
        setIsLoggedIn(true);
        setUsername(auth.username);
        loadDocuments();
      } catch (e) {
        sessionStorage.removeItem('admin_auth');
      }
    }
  }, []);

  const handleLogin = async (e) => {
    e.preventDefault();

    try {
      // Store credentials for API calls
      const auth = btoa(`${username}:${password}`);
      sessionStorage.setItem('admin_auth', JSON.stringify({ username, auth }));

      // Test the credentials by fetching documents
      const response = await fetch(`${apiUrl}/api/documents`, {
        headers: {
          'Authorization': `Basic ${auth}`
        }
      });

      if (response.ok) {
        setIsLoggedIn(true);
        loadDocuments();
      } else {
        alert('Invalid credentials');
        sessionStorage.removeItem('admin_auth');
      }
    } catch (error) {
      alert('Login failed: ' + error.message);
    }
  };

  const handleLogout = () => {
    sessionStorage.removeItem('admin_auth');
    setIsLoggedIn(false);
    setUsername('');
    setPassword('');
  };

  const getAuthHeader = () => {
    const stored = sessionStorage.getItem('admin_auth');
    if (stored) {
      const { auth } = JSON.parse(stored);
      return { 'Authorization': `Basic ${auth}` };
    }
    return {};
  };

  const loadDocuments = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/documents`, {
        headers: getAuthHeader()
      });

      if (response.ok) {
        const data = await response.json();
        setDocuments(data.documents || []);
      }
    } catch (error) {
      console.error('Error loading documents:', error);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsUploading(true);
    setUploadProgress(`Uploading ${file.name}...`);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${apiUrl}/api/documents/upload`, {
        method: 'POST',
        headers: getAuthHeader(),
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        setUploadProgress(`✅ Uploaded: ${file.name}`);
        setTimeout(() => {
          setUploadProgress('');
          loadDocuments();
        }, 2000);
      } else {
        const error = await response.json();
        setUploadProgress(`❌ Error: ${error.detail}`);
      }
    } catch (error) {
      setUploadProgress(`❌ Error: ${error.message}`);
    } finally {
      setIsUploading(false);
      e.target.value = ''; // Reset file input
    }
  };

  const handleDeleteDocument = async (docId, title) => {
    if (!confirm(`Delete "${title}"?`)) return;

    try {
      const response = await fetch(`${apiUrl}/api/documents/${docId}`, {
        method: 'DELETE',
        headers: getAuthHeader()
      });

      if (response.ok) {
        loadDocuments();
      } else {
        alert('Failed to delete document');
      }
    } catch (error) {
      alert('Error: ' + error.message);
    }
  };

  const handleTestChat = async (e) => {
    e.preventDefault();
    if (!testMessage.trim()) return;

    setTestResponse({ loading: true });

    try {
      const response = await fetch(`${apiUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        },
        body: JSON.stringify({
          message: testMessage,
          use_rag: true
        })
      });

      if (response.ok) {
        const data = await response.json();
        setTestResponse(data);
      } else {
        setTestResponse({ error: 'Failed to get response' });
      }
    } catch (error) {
      setTestResponse({ error: error.message });
    }
  };

  // Login screen
  if (!isLoggedIn) {
    return (
      <div style={styles.container}>
        <div style={styles.loginBox}>
          <h2 style={styles.title}>🔐 Admin Login</h2>
          <form onSubmit={handleLogin} style={styles.form}>
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={styles.input}
              required
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={styles.input}
              required
            />
            <button type="submit" style={styles.button}>
              Login
            </button>
          </form>
        </div>
      </div>
    );
  }

  // Main admin panel
  return (
    <div style={styles.container}>
      <div style={styles.panel}>
        {/* Header */}
        <div style={styles.header}>
          <h2 style={styles.title}>🤖 UCX AI Admin Panel</h2>
          <div style={styles.headerRight}>
            <span style={styles.username}>👤 {username}</span>
            <button onClick={handleLogout} style={styles.logoutButton}>
              Logout
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div style={styles.tabs}>
          <button
            onClick={() => setActiveTab('documents')}
            style={{
              ...styles.tab,
              ...(activeTab === 'documents' ? styles.tabActive : {})
            }}
          >
            📚 Documents ({documents.length})
          </button>
          <button
            onClick={() => setActiveTab('upload')}
            style={{
              ...styles.tab,
              ...(activeTab === 'upload' ? styles.tabActive : {})
            }}
          >
            ⬆️ Upload
          </button>
          <button
            onClick={() => setActiveTab('test')}
            style={{
              ...styles.tab,
              ...(activeTab === 'test' ? styles.tabActive : {})
            }}
          >
            🧪 Test Chat
          </button>
        </div>

        {/* Content */}
        <div style={styles.content}>
          {/* Documents Tab */}
          {activeTab === 'documents' && (
            <div>
              <div style={styles.sectionHeader}>
                <h3>Uploaded Documents</h3>
                <button onClick={loadDocuments} style={styles.refreshButton}>
                  🔄 Refresh
                </button>
              </div>
              {documents.length === 0 ? (
                <p style={styles.emptyState}>No documents uploaded yet</p>
              ) : (
                <table style={styles.table}>
                  <thead>
                    <tr>
                      <th style={styles.th}>Title</th>
                      <th style={styles.th}>Type</th>
                      <th style={styles.th}>Source</th>
                      <th style={styles.th}>Uploaded</th>
                      <th style={styles.th}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {documents.map((doc) => (
                      <tr key={doc.id} style={styles.tr}>
                        <td style={styles.td}>{doc.title}</td>
                        <td style={styles.td}>
                          <span style={styles.badge}>{doc.doc_type}</span>
                        </td>
                        <td style={styles.td}>{doc.source}</td>
                        <td style={styles.td}>
                          {new Date(doc.created_at).toLocaleDateString()}
                        </td>
                        <td style={styles.td}>
                          <button
                            onClick={() => handleDeleteDocument(doc.id, doc.title)}
                            style={styles.deleteButton}
                          >
                            🗑️
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {/* Upload Tab */}
          {activeTab === 'upload' && (
            <div>
              <h3>Upload Documents</h3>
              <div style={styles.uploadBox}>
                <p>Upload PDFs, DOCX, TXT, or MD files to train your chatbot</p>
                <input
                  type="file"
                  onChange={handleFileUpload}
                  accept=".pdf,.docx,.txt,.md"
                  style={styles.fileInput}
                  disabled={isUploading}
                />
                {uploadProgress && (
                  <p style={styles.uploadProgress}>{uploadProgress}</p>
                )}
                {isUploading && <p style={styles.uploading}>Processing...</p>}
              </div>
              <div style={styles.infoBox}>
                <h4>Supported Formats:</h4>
                <ul>
                  <li>📄 PDF (.pdf)</li>
                  <li>📝 Word (.docx)</li>
                  <li>📃 Text (.txt)</li>
                  <li>📋 Markdown (.md)</li>
                </ul>
                <p><strong>Note:</strong> Large files may take a minute to process</p>
              </div>
            </div>
          )}

          {/* Test Chat Tab */}
          {activeTab === 'test' && (
            <div>
              <h3>Test Your Chatbot</h3>
              <form onSubmit={handleTestChat} style={styles.testForm}>
                <textarea
                  value={testMessage}
                  onChange={(e) => setTestMessage(e.target.value)}
                  placeholder="Ask a question about your uploaded documents..."
                  style={styles.textarea}
                  rows={3}
                />
                <button
                  type="submit"
                  style={styles.testButton}
                  disabled={!testMessage.trim() || testResponse?.loading}
                >
                  {testResponse?.loading ? 'Thinking...' : 'Send'}
                </button>
              </form>
              {testResponse && !testResponse.loading && (
                <div style={styles.responseBox}>
                  {testResponse.error ? (
                    <p style={styles.error}>Error: {testResponse.error}</p>
                  ) : (
                    <>
                      <h4>Response:</h4>
                      <p style={styles.response}>{testResponse.response}</p>
                      {testResponse.sources_used && testResponse.sources_used.length > 0 && (
                        <div style={styles.sources}>
                          <strong>Sources used:</strong>
                          <ul>
                            {testResponse.sources_used.map((source, i) => (
                              <li key={i}>{source}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      <small style={styles.meta}>
                        Model: {testResponse.model_used} | Tokens: {testResponse.tokens_used}
                      </small>
                    </>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Styles
const styles = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#f5f5f5',
    padding: '20px',
    fontFamily: 'system-ui, -apple-system, sans-serif',
  },
  loginBox: {
    maxWidth: '400px',
    margin: '100px auto',
    backgroundColor: 'white',
    padding: '40px',
    borderRadius: '12px',
    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
  },
  panel: {
    maxWidth: '1200px',
    margin: '0 auto',
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
    overflow: 'hidden',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '20px 30px',
    borderBottom: '1px solid #e0e0e0',
    backgroundColor: '#007bff',
    color: 'white',
  },
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '15px',
  },
  title: {
    margin: 0,
    fontSize: '24px',
  },
  username: {
    fontSize: '14px',
  },
  logoutButton: {
    padding: '8px 16px',
    backgroundColor: 'rgba(255,255,255,0.2)',
    border: 'none',
    borderRadius: '6px',
    color: 'white',
    cursor: 'pointer',
    fontSize: '14px',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '15px',
  },
  input: {
    padding: '12px',
    border: '1px solid #ddd',
    borderRadius: '6px',
    fontSize: '14px',
  },
  button: {
    padding: '12px',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '16px',
    fontWeight: '600',
  },
  tabs: {
    display: 'flex',
    borderBottom: '1px solid #e0e0e0',
    backgroundColor: '#f8f9fa',
  },
  tab: {
    flex: 1,
    padding: '15px',
    border: 'none',
    background: 'none',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '500',
    transition: 'background 0.2s',
  },
  tabActive: {
    backgroundColor: 'white',
    borderBottom: '3px solid #007bff',
  },
  content: {
    padding: '30px',
  },
  sectionHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
  },
  refreshButton: {
    padding: '8px 16px',
    backgroundColor: '#28a745',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
  },
  emptyState: {
    textAlign: 'center',
    color: '#999',
    padding: '40px',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  th: {
    textAlign: 'left',
    padding: '12px',
    borderBottom: '2px solid #e0e0e0',
    backgroundColor: '#f8f9fa',
    fontWeight: '600',
  },
  tr: {
    borderBottom: '1px solid #e0e0e0',
  },
  td: {
    padding: '12px',
  },
  badge: {
    padding: '4px 8px',
    backgroundColor: '#e3f2fd',
    borderRadius: '4px',
    fontSize: '12px',
    fontWeight: '500',
    color: '#1976d2',
    textTransform: 'uppercase',
  },
  deleteButton: {
    padding: '6px 12px',
    backgroundColor: '#dc3545',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  uploadBox: {
    border: '2px dashed #ddd',
    borderRadius: '8px',
    padding: '30px',
    textAlign: 'center',
    marginBottom: '20px',
  },
  fileInput: {
    margin: '20px 0',
    padding: '10px',
    width: '100%',
  },
  uploadProgress: {
    marginTop: '10px',
    fontWeight: '600',
  },
  uploading: {
    color: '#007bff',
    fontStyle: 'italic',
  },
  infoBox: {
    backgroundColor: '#f8f9fa',
    padding: '20px',
    borderRadius: '8px',
  },
  testForm: {
    marginBottom: '20px',
  },
  textarea: {
    width: '100%',
    padding: '12px',
    border: '1px solid #ddd',
    borderRadius: '6px',
    fontSize: '14px',
    marginBottom: '10px',
    resize: 'vertical',
  },
  testButton: {
    padding: '12px 24px',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '600',
  },
  responseBox: {
    backgroundColor: '#f8f9fa',
    padding: '20px',
    borderRadius: '8px',
  },
  response: {
    marginTop: '10px',
    lineHeight: '1.6',
  },
  sources: {
    marginTop: '15px',
    padding: '10px',
    backgroundColor: '#e3f2fd',
    borderRadius: '6px',
  },
  meta: {
    display: 'block',
    marginTop: '15px',
    color: '#666',
  },
  error: {
    color: '#dc3545',
  },
};

export default AdminPanel;
