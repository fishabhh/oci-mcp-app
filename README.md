# OCI MCP Server

## Overview
The OCI MCP (Model Context Protocol) Server is a middleware component that enables intelligent cloud resource provisioning on Oracle Cloud Infrastructure (OCI) through a conversational AI interface.

## Project Architecture
The system consists of three main components:
1. **Conversational AI Chatbot**: User-facing interface for natural language interaction
2. **MCP Server**: Core middleware that processes requests and manages resource provisioning
3. **OCI Resource Management Layer**: Interfaces with OCI APIs to provision and manage cloud resources

## Key Features
- Intelligent analysis of user requirements
- Automated OCI resource recommendation
- Secure provisioning workflow
- Comprehensive error handling

## Getting Started

### Prerequisites
- Python 3.9+
- Oracle Cloud Infrastructure account
- OCI SDK for Python
- FastAPI
- Docker (optional, for containerized deployment)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd oci-mcp-server

# Set up a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure OCI credentials
# Follow instructions in docs/oci-setup.md
```

### Configuration
Copy the example configuration file and update with your settings:
```bash
cp config.example.yaml config.yaml
# Edit config.yaml with your specific settings
```

### Running the Server
```bash
python src/main.py
```

## Project Structure
```
oci-mcp-server/
├── src/                  # Source code
│   ├── api/              # API endpoints
│   ├── core/             # Core business logic
│   ├── models/           # Data models
│   ├── services/         # Service integrations
│   └── utils/            # Utility functions
├── tests/                # Test suite
├── docs/                 # Documentation
└── config.yaml           # Configuration
```

## License
[MIT License](LICENSE)
