# Streaming API Guide

## Overview

The streaming endpoint displays "thinking" status messages before showing the AI response, creating a more engaging user experience.

## Endpoint

```
POST https://ucxai-production.up.railway.app/api/chat/stream
```

## Status Messages

The AI will display these status messages while thinking:

1. **"Searching playbooks..."** - While searching the knowledge base
2. **"Accessing call log..."** - While loading conversation history

## Message Format

The stream sends JSON objects with different types:

```javascript
// Status message (searching)
{ "type": "status", "message": "Searching playbooks..." }

// Status message (accessing history)
{ "type": "status", "message": "Accessing call log..." }

// Content start (response begins)
{ "type": "content_start" }

// Content chunk (streaming response)
{ "type": "content", "message": "Your bottleneck is..." }

// Done signal
{ "type": "done" }

// Error (if something fails)
{ "type": "error", "message": "Error description" }
```

## Frontend Integration

### Basic Example

See `test_streaming.html` for a working example.

### Key Points

1. **Display status messages** with a pulsing/animated style
2. **Remove status** when `content_start` is received
3. **Append content** as chunks arrive
4. **Clean up** when `done` is received

### Example Code

```javascript
const response = await fetch(API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        message: "How do I increase my lead to booking rate",
        loveable_user_id: "user_123",
        email: "user@example.com",
        use_rag: true
    })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();
let statusDiv = null;
let responseDiv = null;

while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
        if (line.startsWith('data: ')) {
            const parsed = JSON.parse(line.slice(6));

            if (parsed.type === 'status') {
                // Show status: "Searching playbooks..." or "Accessing call log..."
                statusDiv.textContent = parsed.message;
            } else if (parsed.type === 'content_start') {
                // Remove status, start showing response
                statusDiv.remove();
            } else if (parsed.type === 'content') {
                // Append response text
                responseDiv.textContent += parsed.message;
            } else if (parsed.type === 'done') {
                // Finished
            }
        }
    }
}
```

## Non-Streaming Endpoint

The original `/api/chat` endpoint still works if you don't want streaming:

```
POST https://ucxai-production.up.railway.app/api/chat
```

Returns a complete response immediately (no status messages).

## Testing

1. Open `test_streaming.html` in a browser
2. Enter a question or use the default
3. Watch the status messages appear:
   - "Searching playbooks..."
   - "Accessing call log..."
4. See the response stream in word-by-word

## Customizing Status Messages

To change the status messages, edit `main.py`:

```python
# Line ~498
yield f"data: {json.dumps({'type': 'status', 'message': 'Searching playbooks...'})}\n\n"

# Line ~517
yield f"data: {json.dumps({'type': 'status', 'message': 'Accessing call log...'})}\n\n"
```

You can add more status messages or change the timing by adjusting the `asyncio.sleep()` values.
