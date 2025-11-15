# 🔐 Admin Panel for Document Management

Manage your chatbot's knowledge base directly from your Lovable website!

## 🎯 Features

- 🔐 Secure admin login
- 📚 View all uploaded documents
- ⬆️ Upload PDFs, DOCX, TXT, MD files
- 🗑️ Delete documents
- 🧪 Test chatbot with your data
- 📊 See which sources are used in responses

## 🚀 Setup (5 minutes)

### Step 1: Set Admin Credentials

Add to your `.env` file:

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password_here
```

**IMPORTANT:** Change the default password!

### Step 2: Add Admin Panel to Lovable

Copy `frontend/AdminPanel.jsx` to your Lovable project.

In your Lovable app:

```jsx
import AdminPanel from './AdminPanel';

function AdminPage() {
  return (
    <AdminPanel apiUrl="https://your-api-url.com" />
  );
}
```

### Step 3: Protect the Route (Optional)

In Lovable, add route protection:

```jsx
import { Navigate } from 'react-router-dom';

// In your router
{
  path: '/admin',
  element: <AdminPage />,
  // Add authentication check here if needed
}
```

### Step 4: Deploy!

The admin panel will automatically:
- Ask for login on first visit
- Store session in browser
- Sync with your API endpoints
- Upload files with progress tracking

## 🎨 How It Works

1. **Login** → Admin enters username/password
2. **Session** → Credentials stored in sessionStorage (secure for session)
3. **Documents** → View, manage uploaded files
4. **Upload** → Drag/drop or select files, auto-processes
5. **Test** → Chat with AI using your documents

## 📊 Admin Panel Features

### Documents Tab
- View all uploaded documents
- See file type, upload date, source
- Delete documents with one click
- Refresh list to see new uploads

### Upload Tab
- Drag and drop files
- Supports: PDF, DOCX, TXT, MD
- Real-time upload progress
- Auto-processes and creates embeddings

### Test Chat Tab
- Ask questions to test your chatbot
- See which documents were used as sources
- View token usage and model info
- Test RAG accuracy

## 🔒 Security Notes

**Current Implementation:**
- HTTP Basic Auth (simple, good for MVP)
- Session-based in browser
- Admin credentials in .env

**For Production, Consider:**
- OAuth2/JWT tokens
- Database user management
- Password hashing (bcrypt)
- Rate limiting
- 2FA authentication
- Audit logs

## 🛠️ Customization

### Change Styling

Edit `styles` object in `AdminPanel.jsx`:

```javascript
const styles = {
  container: {
    backgroundColor: '#your-color',
    // ...
  },
  // ...
};
```

### Add More Features

The admin panel uses these API endpoints:

```javascript
GET    /api/documents           // List documents
POST   /api/documents/upload    // Upload file
POST   /api/documents/add       // Add text
DELETE /api/documents/:id       // Delete document
POST   /api/documents/search    // Search documents
POST   /api/chat                // Test chat
```

You can extend the UI to:
- Bulk upload
- Document categories
- Usage analytics
- Search history
- User management

### Mobile Responsive

The panel is mobile-friendly out of the box. Test on different screen sizes!

## 📱 Usage Examples

### Add New Document
1. Log in to admin panel
2. Click "Upload" tab
3. Select or drag file
4. Wait for processing (shows progress)
5. File is automatically chunked and embedded
6. Test it in "Test Chat" tab!

### Test Chatbot
1. Go to "Test Chat" tab
2. Type: "What information do you have about [topic]?"
3. See response with sources cited
4. Verify correct documents were used

### Manage Documents
1. "Documents" tab shows all files
2. Click 🗑️ to delete
3. Deleted documents are removed from chatbot's knowledge

## 🎯 Best Practices

1. **Upload Quality Content**
   - Well-structured documents
   - Clear, informative text
   - Avoid scanned images (use OCR first)

2. **Organize Documents**
   - Use descriptive filenames
   - Group related docs
   - Delete outdated info

3. **Test Regularly**
   - Upload new docs → test immediately
   - Ask various questions
   - Verify accuracy

4. **Secure Your Admin**
   - Use strong password
   - Don't share credentials
   - Change password regularly
   - Consider adding IP whitelist

## 🚀 Deployment

### Lovable Deployment

1. Copy `AdminPanel.jsx` to your Lovable project
2. Create admin route: `/admin`
3. Deploy your Lovable app
4. Set API URL to your deployed backend
5. Access at: `https://your-app.lovable.app/admin`

### API Deployment

Make sure your API has:
- `main_rag.py` running (not `main.py`)
- ADMIN_USERNAME and ADMIN_PASSWORD in env vars
- CORS configured for your Lovable domain
- Supabase RAG schema installed

## 🐛 Troubleshooting

**"Invalid credentials"**
- Check ADMIN_USERNAME and ADMIN_PASSWORD in `.env`
- Restart API server after changing env vars
- Clear browser sessionStorage

**"Upload fails"**
- Check file format (PDF, DOCX, TXT, MD)
- Ensure Supabase RAG schema is installed
- Check API logs for errors
- Verify file isn't corrupted

**"Documents not showing"**
- Click refresh button
- Check browser console for errors
- Verify API URL is correct
- Test API directly: `curl http://your-api/api/documents`

**"CORS errors"**
- Add your Lovable domain to ALLOWED_ORIGINS in `.env`
- Restart API server
- Clear browser cache

## 📊 Example Workflow

### Setting Up Customer Support Bot

1. **Upload FAQs**
   ```
   Upload: faq.pdf, common_issues.docx, troubleshooting.txt
   ```

2. **Test Coverage**
   ```
   Test: "How do I reset my password?"
   Test: "What are your business hours?"
   Test: "How do I contact support?"
   ```

3. **Iterate**
   ```
   - Add missing info as new docs
   - Delete outdated policies
   - Update pricing info
   ```

4. **Go Live**
   ```
   - Embed ChatWidget in your site
   - Monitor questions
   - Add docs as needed
   ```

## 🎉 You're Ready!

Your admin panel is now set up. You can:
- ✅ Log in from any browser
- ✅ Upload documents instantly
- ✅ Manage your knowledge base
- ✅ Test chatbot responses
- ✅ See real-time results

Access it at: `https://your-lovable-app.com/admin`

**Default credentials:** admin / changeme123 (CHANGE THIS!)
