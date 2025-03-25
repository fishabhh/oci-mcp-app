#!/usr/bin/env python3
"""
Demo workflow for the OCI MCP Server
This script demonstrates how to use the MCP server to analyze requirements and provision resources
"""
import json
import os
import sys
import uuid

# Add the parent directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
from src.api.schemas import ChatbotRequest, ConversationMessage, ProvisioningConfirmation

# Configuration
MCP_SERVER_URL = "http://localhost:8000"


def print_section(title):
    """Print a section title"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")


def simulate_conversation():
    """Simulate a conversation between a user and a chatbot"""
    print_section("Simulating Conversation")
    
    conversation = [
        ConversationMessage(
            role="user",
            content="I need to host a website for my small business. It will be a simple website with product information and a contact form."
        ),
        ConversationMessage(
            role="assistant",
            content="I can help you with that. What kind of traffic do you expect for your website?"
        ),
        ConversationMessage(
            role="user",
            content="I expect low to moderate traffic, maybe a few hundred visitors per day."
        ),
        ConversationMessage(
            role="assistant",
            content="Do you need a database for your website?"
        ),
        ConversationMessage(
            role="user",
            content="Yes, I need a small database to store product information and customer inquiries from the contact form."
        ),
        ConversationMessage(
            role="assistant",
            content="How much storage do you think you'll need for your website content and database?"
        ),
        ConversationMessage(
            role="user",
            content="I don't need much, maybe 50GB should be enough for now."
        ),
    ]
    
    # Print the conversation
    for msg in conversation:
        prefix = "User: " if msg.role == "user" else "Assistant: "
        print(f"{prefix}{msg.content}")
    
    return conversation


def analyze_requirements(conversation):
    """Send the conversation to the MCP server for analysis"""
    print_section("Analyzing Requirements")
    
    # Create a request ID
    request_id = str(uuid.uuid4())
    print(f"Request ID: {request_id}")
    
    # Create the request
    request = ChatbotRequest(
        request_id=request_id,
        conversation_context=conversation,
        user_preferences={
            "cost_optimization": "high",
            "region_preference": "us-ashburn-1",
        }
    )
    
    # Convert to JSON for printing
    request_json = json.loads(request.json())
    print("\nSending request to MCP server:")
    print(json.dumps(request_json, indent=2))
    
    try:
        # Send the request to the MCP server
        response = requests.post(
            f"{MCP_SERVER_URL}/api/analyze",
            json=request_json,
        )
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Parse the response
        result = response.json()
        print("\nReceived recommendations from MCP server:")
        print(json.dumps(result, indent=2))
        
        return result
    except requests.exceptions.RequestException as e:
        print(f"\nError sending request to MCP server: {str(e)}")
        # For demonstration purposes, return a mock response
        return {
            "request_id": request_id,
            "recommendations": [
                {
                    "resource_type": "compute",
                    "name": "WebServer",
                    "description": "Compute instance for hosting the website",
                    "specifications": {
                        "shape": "VM.Standard.E2.1.Micro",
                        "ocpus": 1,
                        "memory_in_gbs": 1,
                        "instance_count": 1,
                        "image_id": "Oracle-Linux-8.6-2022.05.31-0",
                    },
                    "estimated_cost": {
                        "monthly": 50.0,
                        "currency": "USD",
                    },
                },
                {
                    "resource_type": "network",
                    "name": "WebsiteVCN",
                    "description": "Virtual Cloud Network for the website",
                    "specifications": {
                        "vcn_cidr": "10.0.0.0/16",
                        "subnet_cidr": "10.0.0.0/24",
                        "security_list_rules": [
                            {"protocol": "6", "port": 80, "source": "0.0.0.0/0"},
                            {"protocol": "6", "port": 443, "source": "0.0.0.0/0"},
                            {"protocol": "6", "port": 22, "source": "0.0.0.0/0"},
                        ],
                    },
                    "estimated_cost": {
                        "monthly": 0.0,
                        "currency": "USD",
                    },
                },
                {
                    "resource_type": "database",
                    "name": "WebsiteDB",
                    "description": "Database for the website",
                    "specifications": {
                        "type": "autonomous",
                        "workload_type": "OLTP",
                        "storage_in_tbs": 1,
                        "cpu_core_count": 1,
                    },
                    "estimated_cost": {
                        "monthly": 900.0,
                        "currency": "USD",
                    },
                    "dependencies": ["WebsiteVCN"],
                },
                {
                    "resource_type": "storage",
                    "name": "WebsiteStorage",
                    "description": "Block volume for the website",
                    "specifications": {
                        "size_in_gbs": 50,
                        "vpus_per_gb": 10,
                    },
                    "estimated_cost": {
                        "monthly": 1.28,
                        "currency": "USD",
                    },
                    "dependencies": ["WebServer"],
                },
            ],
            "message": "Resource analysis completed successfully",
        }


def confirm_provisioning(analysis_result):
    """Confirm the provisioning of resources"""
    print_section("Confirming Provisioning")
    
    # Get the request ID and recommendations from the analysis result
    request_id = analysis_result["request_id"]
    recommendations = analysis_result["recommendations"]
    
    # Print the recommendations
    print("Recommended resources:")
    total_cost = 0
    for i, resource in enumerate(recommendations):
        cost = resource.get("estimated_cost", {}).get("monthly", 0)
        total_cost += cost
        print(f"{i+1}. {resource['name']} ({resource['resource_type']}): ${cost:.2f}/month")
    
    print(f"\nTotal estimated cost: ${total_cost:.2f}/month")
    
    # In a real application, you would ask the user to confirm the provisioning
    # For demonstration purposes, we'll assume the user confirms all recommendations
    print("\nUser confirms all recommendations.")
    
    # Create the confirmation request
    confirmation = ProvisioningConfirmation(
        request_id=request_id,
        confirmed_resources=recommendations,
    )
    
    # Convert to JSON for printing
    confirmation_json = json.loads(confirmation.json())
    print("\nSending confirmation to MCP server:")
    print(json.dumps(confirmation_json, indent=2))
    
    try:
        # Send the confirmation to the MCP server
        response = requests.post(
            f"{MCP_SERVER_URL}/api/provision",
            json=confirmation_json,
        )
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Parse the response
        result = response.json()
        print("\nProvisioning initiated:")
        print(json.dumps(result, indent=2))
        
        return result
    except requests.exceptions.RequestException as e:
        print(f"\nError sending confirmation to MCP server: {str(e)}")
        # For demonstration purposes, return a mock response
        return {
            "request_id": request_id,
            "status": "success",
            "provisioned_resources": [
                {
                    "resource_type": "compute",
                    "name": "WebServer",
                    "ocid": "ocid1.instance.oc1..example",
                    "status": "active",
                    "details": {
                        "shape": "VM.Standard.E2.1.Micro",
                        "availability_domain": "AD-1",
                        "fault_domain": "FAULT-DOMAIN-1",
                        "time_created": "2023-10-25T12:34:56.789Z",
                    },
                    "access_info": {
                        "public_ip": "10.0.0.123",
                        "private_ip": "192.168.0.123",
                        "hostname": "webserver.example.com",
                    },
                },
                # Other resources would be included here
            ],
            "message": "Resources provisioned successfully",
        }


def check_provisioning_status(provisioning_result):
    """Check the status of the provisioning"""
    print_section("Checking Provisioning Status")
    
    # Get the request ID from the provisioning result
    request_id = provisioning_result["request_id"]
    
    try:
        # Send the request to the MCP server
        response = requests.get(f"{MCP_SERVER_URL}/api/status/{request_id}")
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Parse the response
        result = response.json()
        print("Provisioning status:")
        print(json.dumps(result, indent=2))
        
        return result
    except requests.exceptions.RequestException as e:
        print(f"\nError checking provisioning status: {str(e)}")
        # For demonstration purposes, return a mock response
        return {
            "request_id": request_id,
            "status": "completed",
            "progress": 100.0,
            "resources": [
                {
                    "name": "WebServer",
                    "type": "compute",
                    "status": "active",
                    "ocid": "ocid1.instance.oc1..example",
                },
                {
                    "name": "WebsiteVCN",
                    "type": "network",
                    "status": "active",
                    "ocid": "ocid1.vcn.oc1..example",
                },
                {
                    "name": "WebsiteDB",
                    "type": "database",
                    "status": "active",
                    "ocid": "ocid1.autonomousdatabase.oc1..example",
                },
                {
                    "name": "WebsiteStorage",
                    "type": "storage",
                    "status": "active",
                    "ocid": "ocid1.volume.oc1..example",
                },
            ],
            "started_at": "2023-10-25T12:34:56.789Z",
            "estimated_completion": "2023-10-25T12:49:56.789Z",
            "message": "Provisioning completed successfully",
        }


def main():
    """Main function"""
    print_section("OCI MCP Server Demo Workflow")
    print("This script demonstrates how to use the MCP server to analyze requirements and provision resources.")
    
    # Step 1: Simulate a conversation
    conversation = simulate_conversation()
    
    # Step 2: Analyze requirements
    analysis_result = analyze_requirements(conversation)
    
    # Step 3: Confirm provisioning
    provisioning_result = confirm_provisioning(analysis_result)
    
    # Step 4: Check provisioning status
    status_result = check_provisioning_status(provisioning_result)
    
    print_section("Demo Completed")
    print("The demo workflow has completed successfully.")
    print("In a real-world scenario, you would integrate the MCP server with your chatbot")
    print("and OCI account to provision actual resources.")


if __name__ == "__main__":
    main()
