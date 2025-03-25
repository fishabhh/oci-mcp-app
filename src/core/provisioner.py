"""
Resource Provisioner for the OCI MCP Server
"""
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from api.schemas import OCIResource, ProvisionedResource, ResourceStatus
from services.oci_client import OCIClient
from utils.logger import get_logger

logger = get_logger(__name__)


class ResourceProvisioner:
    """
    Provisions OCI resources based on confirmed recommendations
    """

    def __init__(self):
        """Initialize the resource provisioner"""
        self.logger = logger
        self.oci_client = OCIClient()
        
        # In-memory storage for provisioning requests
        # In a production environment, this would be stored in a database
        self.provisioning_requests = {}

    def provision_resources(
        self, request_id: str, resources: List[OCIResource]
    ) -> List[ProvisionedResource]:
        """
        Provision OCI resources based on confirmed recommendations
        
        Args:
            request_id: Unique identifier for the request
            resources: List of resources to provision
            
        Returns:
            List of provisioned resources
        """
        self.logger.info(f"Starting resource provisioning for request {request_id}")
        
        # Initialize provisioning request
        if request_id not in self.provisioning_requests:
            self.provisioning_requests[request_id] = {
                "status": "in_progress",
                "started_at": datetime.now().isoformat(),
                "estimated_completion": (datetime.now() + timedelta(minutes=15)).isoformat(),
                "resources": [],
                "progress": 0.0,
            }
        
        # Sort resources by dependencies
        sorted_resources = self._sort_resources_by_dependencies(resources)
        
        # Provision resources in order
        provisioned_resources = []
        total_resources = len(sorted_resources)
        
        for i, resource in enumerate(sorted_resources):
            try:
                self.logger.info(f"Provisioning {resource.resource_type} resource: {resource.name}")
                
                # Update progress
                progress_percentage = (i / total_resources) * 100
                self.provisioning_requests[request_id]["progress"] = progress_percentage
                
                # Provision resource based on type
                provisioned = self._provision_resource(resource)
                provisioned_resources.append(provisioned)
                
                # Update provisioning request
                self.provisioning_requests[request_id]["resources"].append({
                    "name": provisioned.name,
                    "type": provisioned.resource_type,
                    "status": provisioned.status,
                    "ocid": provisioned.ocid,
                })
                
                self.logger.info(f"Successfully provisioned {resource.name}")
                
            except Exception as e:
                self.logger.error(f"Error provisioning {resource.name}: {str(e)}")
                
                # Update provisioning request with error
                self.provisioning_requests[request_id]["resources"].append({
                    "name": resource.name,
                    "type": resource.resource_type,
                    "status": "failed",
                    "error": str(e),
                })
                
                # Continue with next resource
                continue
        
        # Update final status
        self.provisioning_requests[request_id]["status"] = "completed"
        self.provisioning_requests[request_id]["progress"] = 100.0
        
        self.logger.info(f"Completed resource provisioning for request {request_id}")
        return provisioned_resources

    def get_provisioning_status(self, request_id: str) -> Dict[str, Any]:
        """
        Get the status of a provisioning request
        
        Args:
            request_id: Unique identifier for the request
            
        Returns:
            Dictionary containing provisioning status
        """
        if request_id not in self.provisioning_requests:
            return {
                "request_id": request_id,
                "status": "not_found",
                "message": f"No provisioning request found with ID {request_id}",
                "progress": 0.0,
                "resources": [],
            }
        
        return {
            "request_id": request_id,
            **self.provisioning_requests[request_id],
        }

    def _sort_resources_by_dependencies(self, resources: List[OCIResource]) -> List[OCIResource]:
        """
        Sort resources by dependencies to ensure proper provisioning order
        
        Args:
            resources: List of resources to sort
            
        Returns:
            Sorted list of resources
        """
        # Create a mapping of resource names to resources
        resource_map = {resource.name: resource for resource in resources}
        
        # Create a dependency graph
        dependency_graph = {resource.name: set() for resource in resources}
        for resource in resources:
            if resource.dependencies:
                for dependency in resource.dependencies:
                    if dependency in resource_map:
                        dependency_graph[resource.name].add(dependency)
        
        # Perform topological sort
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(name):
            if name in temp_visited:
                raise ValueError(f"Circular dependency detected for {name}")
            if name in visited:
                return
            
            temp_visited.add(name)
            for dependency in dependency_graph[name]:
                visit(dependency)
            
            temp_visited.remove(name)
            visited.add(name)
            order.append(name)
        
        for name in dependency_graph:
            if name not in visited:
                visit(name)
        
        # Convert back to resource objects in the correct order
        return [resource_map[name] for name in reversed(order)]

    def _provision_resource(self, resource: OCIResource) -> ProvisionedResource:
        """
        Provision a single OCI resource
        
        Args:
            resource: Resource to provision
            
        Returns:
            Provisioned resource
        """
        # In a real implementation, this would call the OCI SDK to provision resources
        # For demonstration purposes, we'll simulate the provisioning process
        
        # Simulate provisioning delay
        time.sleep(1)
        
        # Generate a mock OCID
        ocid = f"ocid1.{resource.resource_type.lower()}.oc1..aaaaaaaa{uuid.uuid4().hex}"
        
        # Provision based on resource type
        if resource.resource_type == "compute":
            return self._provision_compute_instance(resource, ocid)
        elif resource.resource_type == "network":
            return self._provision_network(resource, ocid)
        elif resource.resource_type == "database":
            return self._provision_database(resource, ocid)
        elif resource.resource_type == "storage":
            return self._provision_storage(resource, ocid)
        elif resource.resource_type == "load_balancer":
            return self._provision_load_balancer(resource, ocid)
        else:
            raise ValueError(f"Unsupported resource type: {resource.resource_type}")

    def _provision_compute_instance(self, resource: OCIResource, ocid: str) -> ProvisionedResource:
        """Provision a compute instance"""
        # In a real implementation, this would call the OCI Compute API
        
        # Extract specifications
        shape = resource.specifications.get("shape", "VM.Standard.E4.Flex")
        ocpus = resource.specifications.get("ocpus", 1)
        memory_in_gbs = resource.specifications.get("memory_in_gbs", 8)
        
        # Create provisioned resource
        return ProvisionedResource(
            resource_type=resource.resource_type,
            name=resource.name,
            ocid=ocid,
            status=ResourceStatus.ACTIVE,
            details={
                "shape": shape,
                "ocpus": ocpus,
                "memory_in_gbs": memory_in_gbs,
                "availability_domain": "AD-1",
                "fault_domain": "FAULT-DOMAIN-1",
                "time_created": datetime.now().isoformat(),
            },
            access_info={
                "public_ip": f"10.0.0.{uuid.uuid4().int % 255}",
                "private_ip": f"192.168.0.{uuid.uuid4().int % 255}",
                "hostname": f"{resource.name.lower()}.example.com",
            },
        )

    def _provision_network(self, resource: OCIResource, ocid: str) -> ProvisionedResource:
        """Provision a network resource"""
        # In a real implementation, this would call the OCI Networking API
        
        # Extract specifications
        vcn_cidr = resource.specifications.get("vcn_cidr", "10.0.0.0/16")
        subnet_cidr = resource.specifications.get("subnet_cidr", "10.0.0.0/24")
        
        # Create provisioned resource
        return ProvisionedResource(
            resource_type=resource.resource_type,
            name=resource.name,
            ocid=ocid,
            status=ResourceStatus.ACTIVE,
            details={
                "vcn_cidr": vcn_cidr,
                "subnet_cidr": subnet_cidr,
                "dns_label": resource.name.lower().replace("-", ""),
                "time_created": datetime.now().isoformat(),
            },
            access_info={
                "vcn_domain_name": f"{resource.name.lower().replace('-', '')}.oraclevcn.com",
            },
        )

    def _provision_database(self, resource: OCIResource, ocid: str) -> ProvisionedResource:
        """Provision a database resource"""
        # In a real implementation, this would call the OCI Database API
        
        # Extract specifications
        db_type = resource.specifications.get("type", "autonomous")
        workload_type = resource.specifications.get("workload_type", "OLTP")
        storage_in_tbs = resource.specifications.get("storage_in_tbs", 1)
        
        # Create provisioned resource
        return ProvisionedResource(
            resource_type=resource.resource_type,
            name=resource.name,
            ocid=ocid,
            status=ResourceStatus.ACTIVE,
            details={
                "db_type": db_type,
                "workload_type": workload_type,
                "storage_in_tbs": storage_in_tbs,
                "time_created": datetime.now().isoformat(),
            },
            access_info={
                "connection_string": f"{resource.name.lower()}.adb.{self.oci_client.region}.oraclecloudapps.com",
                "admin_username": "ADMIN",
            },
        )

    def _provision_storage(self, resource: OCIResource, ocid: str) -> ProvisionedResource:
        """Provision a storage resource"""
        # In a real implementation, this would call the OCI Storage API
        
        # Extract specifications
        size_in_gbs = resource.specifications.get("size_in_gbs", 50)
        
        # Create provisioned resource
        return ProvisionedResource(
            resource_type=resource.resource_type,
            name=resource.name,
            ocid=ocid,
            status=ResourceStatus.ACTIVE,
            details={
                "size_in_gbs": size_in_gbs,
                "vpus_per_gb": resource.specifications.get("vpus_per_gb", 10),
                "time_created": datetime.now().isoformat(),
            },
            access_info={
                "iqn": f"iqn.2015-12.com.oracleiaas:{uuid.uuid4().hex}",
                "attachment_type": "paravirtualized",
            },
        )

    def _provision_load_balancer(self, resource: OCIResource, ocid: str) -> ProvisionedResource:
        """Provision a load balancer resource"""
        # In a real implementation, this would call the OCI Load Balancer API
        
        # Extract specifications
        shape = resource.specifications.get("shape", "flexible")
        min_bandwidth_mbps = resource.specifications.get("min_bandwidth_mbps", 10)
        max_bandwidth_mbps = resource.specifications.get("max_bandwidth_mbps", 100)
        
        # Create provisioned resource
        return ProvisionedResource(
            resource_type=resource.resource_type,
            name=resource.name,
            ocid=ocid,
            status=ResourceStatus.ACTIVE,
            details={
                "shape": shape,
                "min_bandwidth_mbps": min_bandwidth_mbps,
                "max_bandwidth_mbps": max_bandwidth_mbps,
                "time_created": datetime.now().isoformat(),
            },
            access_info={
                "ip_address": f"10.0.0.{uuid.uuid4().int % 255}",
                "hostname": f"{resource.name.lower()}.example.com",
            },
        )
