"""
API Router for the OCI MCP Server
"""
from fastapi import APIRouter, Depends, HTTPException, status

from api.schemas import (
    ChatbotRequest,
    ProvisioningConfirmation,
    ProvisioningResponse,
    ResourceRecommendation,
)
from core.analyzer import ResourceAnalyzer
from core.provisioner import ResourceProvisioner
from services.oci_client import OCIClient

router = APIRouter()


@router.post("/analyze", response_model=ResourceRecommendation)
async def analyze_requirements(request: ChatbotRequest):
    """
    Analyze user requirements from chatbot conversation and recommend OCI resources
    """
    try:
        analyzer = ResourceAnalyzer()
        recommendations = analyzer.analyze_requirements(request.conversation_context)
        return ResourceRecommendation(
            request_id=request.request_id,
            recommendations=recommendations,
            message="Resource analysis completed successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing requirements: {str(e)}",
        )


@router.post("/provision", response_model=ProvisioningResponse)
async def provision_resources(confirmation: ProvisioningConfirmation):
    """
    Provision OCI resources based on confirmed recommendations
    """
    try:
        provisioner = ResourceProvisioner()
        result = provisioner.provision_resources(
            confirmation.request_id, confirmation.confirmed_resources
        )
        return ProvisioningResponse(
            request_id=confirmation.request_id,
            status="success",
            provisioned_resources=result,
            message="Resources provisioned successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error provisioning resources: {str(e)}",
        )


@router.get("/resource-types")
async def get_resource_types():
    """
    Get available OCI resource types that can be provisioned
    """
    try:
        oci_client = OCIClient()
        resource_types = oci_client.get_available_resource_types()
        return {"resource_types": resource_types}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching resource types: {str(e)}",
        )


@router.get("/compute-shapes")
async def get_compute_shapes():
    """
    Get available OCI compute shapes
    """
    try:
        oci_client = OCIClient()
        shapes = oci_client.get_compute_shapes()
        return {"compute_shapes": shapes}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching compute shapes: {str(e)}",
        )


@router.get("/status/{request_id}")
async def get_provisioning_status(request_id: str):
    """
    Get the status of a provisioning request
    """
    try:
        provisioner = ResourceProvisioner()
        status = provisioner.get_provisioning_status(request_id)
        return status
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching provisioning status: {str(e)}",
        )
