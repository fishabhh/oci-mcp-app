# Chrome Extension Implementation Guide

This guide outlines how to implement a Chrome extension that interfaces with the OCI MCP Server to enable conversational cloud resource provisioning.

## Architecture Overview

The Chrome extension serves as the user interface layer, connecting the conversational AI with the MCP Server:

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │      │                 │
│  Chrome         │      │                 │      │  Oracle Cloud   │
│  Extension      │◄────►│  MCP Server     │◄────►│  Infrastructure │
│                 │      │                 │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

## Extension Structure

```
chrome-extension/
├── manifest.json         # Extension manifest
├── background.js         # Background script
├── popup/                # Popup UI
│   ├── popup.html        # Popup HTML
│   ├── popup.css         # Popup styles
│   └── popup.js          # Popup logic
├── content/              # Content scripts
│   ├── chat.js           # Chat interface
│   └── chat.css          # Chat styles
└── lib/                  # Libraries
    ├── api.js            # MCP API client
    └── auth.js           # Authentication
```

## Implementation Steps

### 1. Create the Manifest

```json
{
  "manifest_version": 3,
  "name": "OCI Resource Provisioning Assistant",
  "version": "1.0.0",
  "description": "Provision Oracle Cloud Infrastructure resources through natural language conversation",
  "permissions": [
    "storage",
    "activeTab"
  ],
  "host_permissions": [
    "http://localhost:8000/*",
    "https://*.example.com/*"
  ],
  "background": {
    "service_worker": "background.js"
  },
  "action": {
    "default_popup": "popup/popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["content/chat.js"],
      "css": ["content/chat.css"]
    }
  ]
}
```

### 2. Implement the API Client

```javascript
// lib/api.js
class MCPClient {
  constructor(baseUrl, token = null) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  setToken(token) {
    this.token = token;
  }

  async getHeaders() {
    const headers = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    return headers;
  }

  async analyzeRequirements(conversation) {
    const requestId = this.generateUUID();
    
    const response = await fetch(`${this.baseUrl}/api/analyze`, {
      method: 'POST',
      headers: await this.getHeaders(),
      body: JSON.stringify({
        request_id: requestId,
        conversation_context: conversation,
      }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  }

  async provisionResources(requestId, resources) {
    const response = await fetch(`${this.baseUrl}/api/provision`, {
      method: 'POST',
      headers: await this.getHeaders(),
      body: JSON.stringify({
        request_id: requestId,
        confirmed_resources: resources,
      }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  }

  async checkStatus(requestId) {
    const response = await fetch(`${this.baseUrl}/api/status/${requestId}`, {
      method: 'GET',
      headers: await this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  }

  generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }
}

export default MCPClient;
```

### 3. Implement Authentication

```javascript
// lib/auth.js
class Auth {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
    this.tokenKey = 'mcp_token';
  }

  async login(apiKey) {
    try {
      const response = await fetch(`${this.baseUrl}/api/auth`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ api_key: apiKey }),
      });

      if (!response.ok) {
        throw new Error(`Authentication failed: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.token) {
        await chrome.storage.local.set({ [this.tokenKey]: data.token });
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Authentication error:', error);
      return false;
    }
  }

  async getToken() {
    const data = await chrome.storage.local.get(this.tokenKey);
    return data[this.tokenKey];
  }

  async isAuthenticated() {
    const token = await this.getToken();
    return !!token;
  }

  async logout() {
    await chrome.storage.local.remove(this.tokenKey);
  }
}

export default Auth;
```

### 4. Implement the Background Script

```javascript
// background.js
import MCPClient from './lib/api.js';
import Auth from './lib/auth.js';

// Configuration
const MCP_SERVER_URL = 'http://localhost:8000';

// Initialize services
const auth = new Auth(MCP_SERVER_URL);
const mcpClient = new MCPClient(MCP_SERVER_URL);

// Set up message handling
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  handleMessage(request, sender)
    .then(response => sendResponse(response))
    .catch(error => sendResponse({ success: false, error: error.message }));
  
  return true; // Required for async sendResponse
});

// Message handler
async function handleMessage(request, sender) {
  // Initialize API client with token
  const token = await auth.getToken();
  mcpClient.setToken(token);

  switch (request.action) {
    case 'login':
      const success = await auth.login(request.apiKey);
      return { success };
      
    case 'logout':
      await auth.logout();
      return { success: true };
      
    case 'analyze_requirements':
      const analysis = await mcpClient.analyzeRequirements(request.conversation);
      return { success: true, data: analysis };
      
    case 'provision_resources':
      const provisioning = await mcpClient.provisionResources(
        request.requestId,
        request.resources
      );
      return { success: true, data: provisioning };
      
    case 'check_status':
      const status = await mcpClient.checkStatus(request.requestId);
      return { success: true, data: status };
      
    default:
      throw new Error(`Unknown action: ${request.action}`);
  }
}
```

### 5. Implement the Chat Interface

```javascript
// content/chat.js
class ChatInterface {
  constructor() {
    this.conversation = [];
    this.requestId = null;
    this.createChatUI();
    this.setupEventListeners();
  }

  createChatUI() {
    // Create chat container
    this.container = document.createElement('div');
    this.container.className = 'oci-chat-container';
    
    // Create chat header
    const header = document.createElement('div');
    header.className = 'oci-chat-header';
    header.textContent = 'OCI Resource Assistant';
    
    // Create chat messages container
    this.messagesContainer = document.createElement('div');
    this.messagesContainer.className = 'oci-chat-messages';
    
    // Create chat input
    const inputContainer = document.createElement('div');
    inputContainer.className = 'oci-chat-input-container';
    
    this.input = document.createElement('input');
    this.input.className = 'oci-chat-input';
    this.input.placeholder = 'Type your message...';
    
    const sendButton = document.createElement('button');
    sendButton.className = 'oci-chat-send-button';
    sendButton.textContent = 'Send';
    
    // Assemble UI
    inputContainer.appendChild(this.input);
    inputContainer.appendChild(sendButton);
    
    this.container.appendChild(header);
    this.container.appendChild(this.messagesContainer);
    this.container.appendChild(inputContainer);
    
    // Add to page
    document.body.appendChild(this.container);
    
    // Add initial message
    this.addMessage('assistant', 'Hello! I can help you provision Oracle Cloud resources. What are you looking to build today?');
  }

  setupEventListeners() {
    // Send button click
    this.container.querySelector('.oci-chat-send-button').addEventListener('click', () => {
      this.sendMessage();
    });
    
    // Enter key press
    this.input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        this.sendMessage();
      }
    });
  }

  addMessage(role, content) {
    // Create message element
    const message = document.createElement('div');
    message.className = `oci-chat-message oci-chat-message-${role}`;
    message.textContent = content;
    
    // Add to UI
    this.messagesContainer.appendChild(message);
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    
    // Add to conversation history
    this.conversation.push({ role, content });
  }

  async sendMessage() {
    const content = this.input.value.trim();
    
    if (!content) return;
    
    // Clear input
    this.input.value = '';
    
    // Add user message to chat
    this.addMessage('user', content);
    
    // Process message
    await this.processUserMessage(content);
  }

  async processUserMessage(content) {
    try {
      // If we have enough context, analyze requirements
      if (this.conversation.length >= 5 && !this.requestId) {
        this.addMessage('assistant', 'Analyzing your requirements...');
        
        const response = await chrome.runtime.sendMessage({
          action: 'analyze_requirements',
          conversation: this.conversation
        });
        
        if (!response.success) {
          throw new Error(response.error);
        }
        
        this.requestId = response.data.request_id;
        this.recommendations = response.data.recommendations;
        
        // Present recommendations
        this.presentRecommendations();
      } 
      // If we have recommendations and user confirms
      else if (this.requestId && this.recommendations && 
               (content.toLowerCase().includes('yes') || 
                content.toLowerCase().includes('confirm') || 
                content.toLowerCase().includes('proceed'))) {
        
        this.addMessage('assistant', 'Provisioning resources. This may take a few minutes...');
        
        const response = await chrome.runtime.sendMessage({
          action: 'provision_resources',
          requestId: this.requestId,
          resources: this.recommendations
        });
        
        if (!response.success) {
          throw new Error(response.error);
        }
        
        // Start checking status
        this.checkProvisioningStatus();
      } 
      // Otherwise, simulate chatbot response
      else {
        // In a real implementation, this would call an LLM API
        setTimeout(() => {
          this.addMessage('assistant', this.getSimulatedResponse(content));
        }, 1000);
      }
    } catch (error) {
      console.error('Error:', error);
      this.addMessage('assistant', `Sorry, an error occurred: ${error.message}`);
    }
  }

  presentRecommendations() {
    let message = 'Based on your requirements, I recommend the following resources:\n\n';
    
    let totalCost = 0;
    
    for (const resource of this.recommendations) {
      const cost = resource.estimated_cost?.monthly || 0;
      totalCost += cost;
      
      message += `• ${resource.name} (${resource.resource_type}): $${cost.toFixed(2)}/month\n`;
      message += `  ${resource.description}\n\n`;
    }
    
    message += `Total estimated cost: $${totalCost.toFixed(2)}/month\n\n`;
    message += 'Would you like me to provision these resources for you?';
    
    this.addMessage('assistant', message);
  }

  async checkProvisioningStatus() {
    try {
      const response = await chrome.runtime.sendMessage({
        action: 'check_status',
        requestId: this.requestId
      });
      
      if (!response.success) {
        throw new Error(response.error);
      }
      
      const status = response.data;
      
      if (status.status === 'completed') {
        this.presentCompletionStatus(status);
      } else {
        // Update progress
        this.addMessage('assistant', `Provisioning in progress: ${status.progress.toFixed(0)}% complete`);
        
        // Check again after 5 seconds
        setTimeout(() => this.checkProvisioningStatus(), 5000);
      }
    } catch (error) {
      console.error('Error checking status:', error);
      this.addMessage('assistant', `Sorry, an error occurred while checking status: ${error.message}`);
    }
  }

  presentCompletionStatus(status) {
    let message = 'Your resources have been successfully provisioned:\n\n';
    
    for (const resource of status.resources) {
      message += `• ${resource.name} (${resource.type}): ${resource.status}\n`;
      if (resource.ocid) {
        message += `  OCID: ${resource.ocid}\n`;
      }
      message += '\n';
    }
    
    message += 'You can access these resources through the OCI Console.';
    
    this.addMessage('assistant', message);
    
    // Reset for new conversation
    this.requestId = null;
    this.recommendations = null;
  }

  getSimulatedResponse(userMessage) {
    // Simple rule-based responses
    if (userMessage.toLowerCase().includes('website')) {
      return 'What kind of website are you looking to host? Is it a static site, dynamic application, or e-commerce store?';
    } else if (userMessage.toLowerCase().includes('database')) {
      return 'What type of database do you need? Oracle offers Autonomous Database, MySQL, and NoSQL options.';
    } else if (userMessage.toLowerCase().includes('traffic') || userMessage.toLowerCase().includes('visitors')) {
      return 'How much traffic do you expect? This will help me recommend the right compute resources.';
    } else if (userMessage.toLowerCase().includes('budget')) {
      return 'What\'s your monthly budget for cloud resources? I can optimize recommendations based on your budget constraints.';
    } else {
      return 'Tell me more about your requirements. What kind of cloud resources are you looking for?';
    }
  }
}

// Initialize chat interface
new ChatInterface();
```

### 6. Implement the Popup UI

```html
<!-- popup/popup.html -->
<!DOCTYPE html>
<html>
<head>
  <title>OCI Resource Assistant</title>
  <link rel="stylesheet" href="popup.css">
</head>
<body>
  <div class="container">
    <h1>OCI Resource Assistant</h1>
    
    <div id="login-form" class="form">
      <h2>Login</h2>
      <div class="form-group">
        <label for="api-key">API Key</label>
        <input type="password" id="api-key" placeholder="Enter your API key">
      </div>
      <button id="login-button">Login</button>
    </div>
    
    <div id="main-content" class="hidden">
      <h2>You are logged in</h2>
      <p>Click the button below to open the chat interface</p>
      <button id="open-chat-button">Open Chat</button>
      <button id="logout-button">Logout</button>
    </div>
    
    <div id="status-message"></div>
  </div>
  
  <script src="popup.js" type="module"></script>
</body>
</html>
```

```javascript
// popup/popup.js
document.addEventListener('DOMContentLoaded', async () => {
  const loginForm = document.getElementById('login-form');
  const mainContent = document.getElementById('main-content');
  const statusMessage = document.getElementById('status-message');
  const apiKeyInput = document.getElementById('api-key');
  const loginButton = document.getElementById('login-button');
  const logoutButton = document.getElementById('logout-button');
  const openChatButton = document.getElementById('open-chat-button');
  
  // Check if user is authenticated
  const isAuthenticated = await checkAuthentication();
  updateUI(isAuthenticated);
  
  // Login button click
  loginButton.addEventListener('click', async () => {
    const apiKey = apiKeyInput.value.trim();
    
    if (!apiKey) {
      showStatus('Please enter an API key', 'error');
      return;
    }
    
    showStatus('Logging in...', 'info');
    
    try {
      const response = await chrome.runtime.sendMessage({
        action: 'login',
        apiKey
      });
      
      if (response.success) {
        showStatus('Login successful', 'success');
        updateUI(true);
      } else {
        showStatus('Login failed', 'error');
      }
    } catch (error) {
      showStatus(`Error: ${error.message}`, 'error');
    }
  });
  
  // Logout button click
  logoutButton.addEventListener('click', async () => {
    try {
      await chrome.runtime.sendMessage({ action: 'logout' });
      showStatus('Logged out successfully', 'success');
      updateUI(false);
    } catch (error) {
      showStatus(`Error: ${error.message}`, 'error');
    }
  });
  
  // Open chat button click
  openChatButton.addEventListener('click', async () => {
    try {
      // Get the active tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      // Inject the chat script if not already injected
      await chrome.tabs.executeScript(tab.id, {
        file: 'content/chat.js'
      });
      
      // Close the popup
      window.close();
    } catch (error) {
      showStatus(`Error: ${error.message}`, 'error');
    }
  });
  
  // Helper functions
  async function checkAuthentication() {
    try {
      const data = await chrome.storage.local.get('mcp_token');
      return !!data.mcp_token;
    } catch (error) {
      console.error('Error checking authentication:', error);
      return false;
    }
  }
  
  function updateUI(isAuthenticated) {
    if (isAuthenticated) {
      loginForm.classList.add('hidden');
      mainContent.classList.remove('hidden');
    } else {
      loginForm.classList.remove('hidden');
      mainContent.classList.add('hidden');
      apiKeyInput.value = '';
    }
  }
  
  function showStatus(message, type) {
    statusMessage.textContent = message;
    statusMessage.className = `status ${type}`;
    
    // Clear status after 3 seconds
    setTimeout(() => {
      statusMessage.textContent = '';
      statusMessage.className = 'status';
    }, 3000);
  }
});
```

## Security Considerations

1. **API Key Storage**: Store API keys securely using Chrome's storage API with encryption
2. **HTTPS**: Use HTTPS for all API communications
3. **Content Security Policy**: Implement a strict CSP in the manifest
4. **Permission Scope**: Request only necessary permissions
5. **Input Validation**: Validate all user input before sending to the MCP Server

## Deployment

1. **Development Mode**:
   - Open Chrome and navigate to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked" and select the extension directory

2. **Production Deployment**:
   - Create a ZIP file of the extension directory
   - Submit to the Chrome Web Store for review
   - Provide detailed documentation for users

## Testing

1. **Unit Testing**:
   - Test API client functions
   - Test authentication flow
   - Test UI components

2. **Integration Testing**:
   - Test communication with MCP Server
   - Test end-to-end provisioning flow

3. **Security Testing**:
   - Test for XSS vulnerabilities
   - Test for secure storage of credentials
   - Test for proper HTTPS usage

## Conclusion

This Chrome extension implementation provides a user-friendly interface for interacting with the OCI MCP Server through natural language conversation. By following this guide, you can create a seamless experience for users to provision and manage Oracle Cloud Infrastructure resources directly from their browser.
