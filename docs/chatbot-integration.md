# Chatbot Integration Guide

This guide explains how to integrate the OCI MCP Server with a conversational AI chatbot to create an intelligent cloud resource provisioning system.

## Architecture Overview

The integration architecture consists of three main components:

1. **Conversational AI Chatbot**: Handles natural language interaction with users
2. **MCP Server**: Processes resource requirements and manages provisioning
3. **OCI Resource Management Layer**: Interfaces with Oracle Cloud Infrastructure

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │      │                 │
│  Conversational │      │                 │      │  Oracle Cloud   │
│  AI Chatbot     │◄────►│  MCP Server     │◄────►│  Infrastructure │
│                 │      │                 │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

## Integration Workflow

### 1. Conversation Context Collection

The chatbot collects information from the user through natural language conversation. Key information to gather includes:

- Website/application type (static, dynamic, e-commerce, etc.)
- Expected traffic levels
- Database requirements
- Storage needs
- Budget constraints
- Performance requirements
- Scaling needs
- Region preferences

### 2. Sending Requests to MCP Server

When sufficient information has been collected, the chatbot sends a request to the MCP Server's `/api/analyze` endpoint:

```python
import requests
import uuid
from typing import List, Dict

def send_analysis_request(conversation_messages: List[Dict[str, str]]) -> Dict:
    """
    Send conversation context to MCP Server for analysis
    
    Args:
        conversation_messages: List of conversation messages
        
    Returns:
        Dictionary containing resource recommendations
    """
    # Create a request ID
    request_id = str(uuid.uuid4())
    
    # Format conversation messages
    formatted_messages = [
        {
            "role": msg["role"],
            "content": msg["content"],
            "timestamp": msg.get("timestamp")
        }
        for msg in conversation_messages
    ]
    
    # Create the request payload
    payload = {
        "request_id": request_id,
        "conversation_context": formatted_messages,
        "user_preferences": {
            "cost_optimization": "high",
            "region_preference": "us-ashburn-1"
        }
    }
    
    # Send the request to the MCP server
    response = requests.post(
        "http://mcp-server-url/api/analyze",
        json=payload
    )
    
    # Return the response
    return response.json()
```

### 3. Presenting Recommendations to the User

The chatbot presents the resource recommendations to the user in a clear, understandable format:

```python
def present_recommendations(recommendations: Dict) -> str:
    """
    Format resource recommendations for presentation to the user
    
    Args:
        recommendations: Dictionary containing resource recommendations
        
    Returns:
        Formatted message for the user
    """
    message = "Based on your requirements, I recommend the following cloud resources:\n\n"
    
    total_cost = 0
    
    for resource in recommendations["recommendations"]:
        resource_type = resource["resource_type"].capitalize()
        name = resource["name"]
        description = resource["description"]
        cost = resource.get("estimated_cost", {}).get("monthly", 0)
        total_cost += cost
        
        message += f"• {resource_type}: {name}\n"
        message += f"  {description}\n"
        message += f"  Estimated cost: ${cost:.2f}/month\n\n"
    
    message += f"Total estimated cost: ${total_cost:.2f}/month\n\n"
    message += "Would you like me to provision these resources for you?"
    
    return message
```

### 4. Confirming and Provisioning Resources

When the user confirms, the chatbot sends a provisioning request to the MCP Server:

```python
def send_provisioning_request(request_id: str, recommendations: List[Dict]) -> Dict:
    """
    Send provisioning request to MCP Server
    
    Args:
        request_id: Request ID from the analysis
        recommendations: List of recommended resources
        
    Returns:
        Dictionary containing provisioning results
    """
    # Create the request payload
    payload = {
        "request_id": request_id,
        "confirmed_resources": recommendations
    }
    
    # Send the request to the MCP server
    response = requests.post(
        "http://mcp-server-url/api/provision",
        json=payload
    )
    
    # Return the response
    return response.json()
```

### 5. Monitoring Provisioning Status

The chatbot can check the status of the provisioning process:

```python
def check_provisioning_status(request_id: str) -> Dict:
    """
    Check the status of resource provisioning
    
    Args:
        request_id: Request ID from the provisioning request
        
    Returns:
        Dictionary containing provisioning status
    """
    # Send the request to the MCP server
    response = requests.get(f"http://mcp-server-url/api/status/{request_id}")
    
    # Return the response
    return response.json()
```

## Chrome Extension Integration

To integrate with a Chrome extension, you'll need to implement a secure communication channel between the extension and the MCP Server.

### 1. Authentication

Implement a secure authentication mechanism:

```javascript
// Chrome extension code
async function authenticateWithMCPServer(apiKey) {
  try {
    const response = await fetch('http://mcp-server-url/api/auth', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ api_key: apiKey }),
    });
    
    const data = await response.json();
    
    if (data.token) {
      // Store the token securely
      chrome.storage.local.set({ mcp_token: data.token });
      return true;
    }
    
    return false;
  } catch (error) {
    console.error('Authentication error:', error);
    return false;
  }
}
```

### 2. Message Passing

Implement message passing between the extension and the MCP Server:

```javascript
// Chrome extension code
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'analyze_requirements') {
    analyzeRequirements(request.conversation)
      .then(result => sendResponse({ success: true, data: result }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true; // Required for async sendResponse
  }
});

async function analyzeRequirements(conversation) {
  // Get the authentication token
  const { mcp_token } = await chrome.storage.local.get('mcp_token');
  
  if (!mcp_token) {
    throw new Error('Not authenticated with MCP Server');
  }
  
  // Send the request to the MCP server
  const response = await fetch('http://mcp-server-url/api/analyze', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${mcp_token}`,
    },
    body: JSON.stringify({
      request_id: generateUUID(),
      conversation_context: conversation,
    }),
  });
  
  return await response.json();
}
```

## Security Considerations

1. **API Authentication**: Implement token-based authentication for all API calls
2. **HTTPS**: Use HTTPS for all communications
3. **Input Validation**: Validate all input from the chatbot
4. **Rate Limiting**: Implement rate limiting to prevent abuse
5. **Logging**: Log all requests and responses for auditing
6. **Error Handling**: Implement proper error handling to avoid exposing sensitive information

## Best Practices

1. **Conversation Design**: Design conversational flows that gather all necessary information
2. **Progressive Disclosure**: Present information progressively to avoid overwhelming users
3. **Clear Confirmations**: Always get clear confirmation before provisioning resources
4. **Cost Transparency**: Be transparent about costs and potential charges
5. **Status Updates**: Provide regular updates during long-running provisioning operations
6. **Error Recovery**: Design for graceful recovery from errors
7. **User Education**: Educate users about the provisioned resources

## Example Conversation Flow

```
User: I need to host a website for my small business.

Chatbot: I can help you with that. What kind of website are you looking to host?

User: It's a simple website with product information and a contact form.

Chatbot: Great. What kind of traffic do you expect for your website?

User: Probably low to moderate traffic, maybe a few hundred visitors per day.

Chatbot: Do you need a database for your website?

User: Yes, I need to store product information and customer inquiries.

Chatbot: How much storage do you think you'll need for your website content and database?

User: I don't need much, maybe 50GB should be enough for now.

Chatbot: Based on your requirements, I recommend the following cloud resources:

• Compute: WebServer
  Compute instance for hosting the website
  Estimated cost: $50.00/month

• Network: WebsiteVCN
  Virtual Cloud Network for the website
  Estimated cost: $0.00/month

• Database: WebsiteDB
  Database for the website
  Estimated cost: $900.00/month

• Storage: WebsiteStorage
  Block volume for the website
  Estimated cost: $1.28/month

Total estimated cost: $951.28/month

Would you like me to provision these resources for you?

User: Yes, please go ahead.

Chatbot: I'm provisioning the resources now. This may take a few minutes.

[After some time]

Chatbot: Your resources have been successfully provisioned. Here are the details:

• WebServer: 10.0.0.123 (webserver.example.com)
• WebsiteDB: Connection string available in the OCI Console
• WebsiteStorage: 50GB block volume attached to WebServer

You can access your resources through the OCI Console or using the provided access information.
```

## Troubleshooting

### Common Issues

1. **Authentication Failures**: Verify API keys and tokens
2. **Connection Timeouts**: Check network connectivity and firewall settings
3. **Invalid Requests**: Validate request format and required fields
4. **Provisioning Failures**: Check OCI permissions and resource limits

### Debugging

1. Check the MCP Server logs for detailed error information
2. Verify that the chatbot is sending correctly formatted requests
3. Test the API endpoints directly using a tool like Postman
4. Check the OCI Console for resource provisioning status and errors
