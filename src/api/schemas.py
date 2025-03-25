"""
API Schemas for the OCI MCP Server
"""
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ResourceType(str, Enum):
    """Enum for OCI resource types"""
    COMPUTE = "compute"
    NETWORK = "network"
    DATABASE = "database"
    STORAGE = "storage"
    LOAD_BALANCER = "load_balancer"
    KUBERNETES = "kubernetes"


class ResourceStatus(str, Enum):
    """Enum for resource provisioning status"""
    PENDING = "pending"
    CREATING = "creating"
    ACTIVE = "active"
    FAILED = "failed"
    DELETING = "deleting"
    DELETED = "deleted"


class ConversationMessage(BaseModel):
    """Model for a single message in the conversation context"""
    role: str = Field(..., description="Role of the message sender (user or assistant)")
    content: str = Field(..., description="Content of the message")
    timestamp: Optional[str] = Field(None, description="Timestamp of the message")


class ChatbotRequest(BaseModel):
    """Model for incoming requests from the chatbot"""
    request_id: str = Field(..., description="Unique identifier for the request")
    conversation_context: List[ConversationMessage] = Field(
        ..., description="List of conversation messages providing context"
    )
    user_preferences: Optional[Dict[str, Any]] = Field(
        None, description="User preferences for resource provisioning"
    )
    existing_resources: Optional[Dict[str, Any]] = Field(
        None, description="Existing OCI resources the user already has"
    )


class OCIResource(BaseModel):
    """Model for an OCI resource recommendation or provisioned resource"""
    resource_type: ResourceType
    name: str
    description: Optional[str] = None
    specifications: Dict[str, Any]
    estimated_cost: Optional[Dict[str, Union[float, str]]] = None
    dependencies: Optional[List[str]] = None


class ResourceRecommendation(BaseModel):
    """Model for resource recommendations response"""
    request_id: str
    recommendations: List[OCIResource]
    reasoning: Optional[str] = None
    message: str


class ProvisioningConfirmation(BaseModel):
    """Model for resource provisioning confirmation"""
    request_id: str
    confirmed_resources: List[OCIResource]
    user_id: Optional[str] = None
    priority: Optional[str] = None


class ProvisionedResource(BaseModel):
    """Model for a successfully provisioned resource"""
    resource_type: ResourceType
    name: str
    ocid: str  # Oracle Cloud Identifier
    status: ResourceStatus
    details: Dict[str, Any]
    access_info: Optional[Dict[str, Any]] = None


class ProvisioningResponse(BaseModel):
    """Model for resource provisioning response"""
    request_id: str
    status: str
    provisioned_resources: List[ProvisionedResource]
    message: str
    errors: Optional[List[Dict[str, Any]]] = None


class ProvisioningStatusResponse(BaseModel):
    """Model for provisioning status response"""
    request_id: str
    status: str
    progress: float = Field(..., description="Provisioning progress percentage (0-100)")
    resources: List[Dict[str, Any]]
    started_at: str
    estimated_completion: Optional[str] = None
    message: Optional[str] = None
