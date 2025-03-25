"""
OCI Client Service for the MCP Server
"""
import logging
import os
from typing import Any, Dict, List, Optional

import oci
from oci.config import from_file

from utils.config import get_oci_config
from utils.logger import get_logger

logger = get_logger(__name__)


class OCIClient:
    """
    Client for interacting with Oracle Cloud Infrastructure APIs
    """

    def __init__(self):
        """Initialize the OCI client"""
        self.logger = logger
        self.config = self._load_config()
        self.region = self.config.get("region", "us-ashburn-1")
        
        # Initialize OCI clients
        self._init_clients()

    def _load_config(self) -> Dict[str, Any]:
        """
        Load OCI configuration
        
        Returns:
            Dictionary containing OCI configuration
        """
        oci_config = get_oci_config()
        
        # Check if config file path is provided
        config_file_path = oci_config.get("config_file_path")
        profile_name = oci_config.get("profile_name", "DEFAULT")
        
        if config_file_path:
            # Expand ~ to user's home directory
            config_file_path = os.path.expanduser(config_file_path)
            
            try:
                self.logger.info(f"Loading OCI config from {config_file_path}")
                return from_file(config_file_path, profile_name)
            except Exception as e:
                self.logger.error(f"Error loading OCI config from file: {str(e)}")
        
        # Use direct configuration if config file is not available
        self.logger.info("Using direct OCI configuration")
        return {
            "user": oci_config.get("user_ocid"),
            "fingerprint": oci_config.get("fingerprint"),
            "tenancy": oci_config.get("tenancy_ocid"),
            "region": oci_config.get("region", "us-ashburn-1"),
            "key_file": os.path.expanduser(oci_config.get("key_file_path", "")),
        }

    def _init_clients(self) -> None:
        """Initialize OCI service clients"""
        try:
            # Initialize compute client
            self.compute_client = oci.core.ComputeClient(self.config)
            
            # Initialize virtual network client
            self.network_client = oci.core.VirtualNetworkClient(self.config)
            
            # Initialize block storage client
            self.block_storage_client = oci.core.BlockstorageClient(self.config)
            
            # Initialize database client
            self.database_client = oci.database.DatabaseClient(self.config)
            
            # Initialize load balancer client
            self.load_balancer_client = oci.load_balancer.LoadBalancerClient(self.config)
            
            # Initialize object storage client
            self.object_storage_client = oci.object_storage.ObjectStorageClient(self.config)
            
            # Initialize identity client for compartment operations
            self.identity_client = oci.identity.IdentityClient(self.config)
            
            self.logger.info("OCI clients initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing OCI clients: {str(e)}")
            raise

    def get_available_resource_types(self) -> List[str]:
        """
        Get available OCI resource types that can be provisioned
        
        Returns:
            List of resource type names
        """
        # In a real implementation, this might query OCI APIs for available resource types
        # For demonstration purposes, we'll return a static list
        return [
            "Compute Instance",
            "Virtual Cloud Network",
            "Subnet",
            "Internet Gateway",
            "Route Table",
            "Security List",
            "Network Security Group",
            "Load Balancer",
            "Autonomous Database",
            "Block Volume",
            "Object Storage Bucket",
            "File Storage",
            "Kubernetes Cluster",
        ]

    def get_compute_shapes(self) -> List[Dict[str, Any]]:
        """
        Get available compute shapes in the configured region
        
        Returns:
            List of compute shapes
        """
        try:
            # Get the tenancy ID
            tenancy_id = self.config.get("tenancy")
            
            # List shapes
            response = self.compute_client.list_shapes(compartment_id=tenancy_id)
            
            # Extract shape information
            shapes = []
            for shape in response.data:
                shapes.append({
                    "shape": shape.shape,
                    "ocpus": getattr(shape, "ocpus", None),
                    "memory_in_gbs": getattr(shape, "memory_in_gbs", None),
                    "networking_bandwidth_in_gbps": getattr(shape, "networking_bandwidth_in_gbps", None),
                    "max_vnic_attachments": getattr(shape, "max_vnic_attachments", None),
                    "gpus": getattr(shape, "gpus", None),
                    "local_disks": getattr(shape, "local_disks", None),
                    "local_disks_total_size_in_gbs": getattr(shape, "local_disks_total_size_in_gbs", None),
                    "processor_description": getattr(shape, "processor_description", None),
                })
            
            return shapes
        except Exception as e:
            self.logger.error(f"Error fetching compute shapes: {str(e)}")
            # Return some default shapes for demonstration purposes
            return [
                {
                    "shape": "VM.Standard.E4.Flex",
                    "ocpus": "1-64",
                    "memory_in_gbs": "16-1024",
                    "processor_description": "2.55 GHz AMD EPYC™ 7J13",
                },
                {
                    "shape": "VM.Standard.E3.Flex",
                    "ocpus": "1-64",
                    "memory_in_gbs": "16-1024",
                    "processor_description": "2.25 GHz AMD EPYC™ 7742",
                },
                {
                    "shape": "VM.Standard.A1.Flex",
                    "ocpus": "1-80",
                    "memory_in_gbs": "6-512",
                    "processor_description": "Ampere® Altra® Q80-30",
                },
                {
                    "shape": "VM.Standard2.1",
                    "ocpus": 1,
                    "memory_in_gbs": 15,
                    "processor_description": "2.0 GHz Intel® Xeon® Platinum 8167M",
                },
            ]

    def create_vcn(self, compartment_id: str, vcn_name: str, cidr_block: str) -> Dict[str, Any]:
        """
        Create a Virtual Cloud Network (VCN)
        
        Args:
            compartment_id: Compartment ID
            vcn_name: Name of the VCN
            cidr_block: CIDR block for the VCN
            
        Returns:
            Dictionary containing VCN details
        """
        try:
            # Create VCN details
            vcn_details = oci.core.models.CreateVcnDetails(
                compartment_id=compartment_id,
                display_name=vcn_name,
                cidr_block=cidr_block,
                dns_label=vcn_name.lower().replace("-", "")[:15],
            )
            
            # Create VCN
            response = self.network_client.create_vcn(vcn_details)
            
            # Wait for VCN to be available
            get_vcn_response = oci.wait_until(
                self.network_client,
                self.network_client.get_vcn(response.data.id),
                "lifecycle_state",
                "AVAILABLE",
            )
            
            vcn = get_vcn_response.data
            
            return {
                "id": vcn.id,
                "display_name": vcn.display_name,
                "cidr_block": vcn.cidr_block,
                "dns_label": vcn.dns_label,
                "lifecycle_state": vcn.lifecycle_state,
            }
        except Exception as e:
            self.logger.error(f"Error creating VCN: {str(e)}")
            raise

    def create_subnet(
        self, compartment_id: str, vcn_id: str, subnet_name: str, cidr_block: str
    ) -> Dict[str, Any]:
        """
        Create a subnet in a VCN
        
        Args:
            compartment_id: Compartment ID
            vcn_id: VCN ID
            subnet_name: Name of the subnet
            cidr_block: CIDR block for the subnet
            
        Returns:
            Dictionary containing subnet details
        """
        try:
            # Create subnet details
            subnet_details = oci.core.models.CreateSubnetDetails(
                compartment_id=compartment_id,
                vcn_id=vcn_id,
                display_name=subnet_name,
                cidr_block=cidr_block,
                dns_label=subnet_name.lower().replace("-", "")[:15],
            )
            
            # Create subnet
            response = self.network_client.create_subnet(subnet_details)
            
            # Wait for subnet to be available
            get_subnet_response = oci.wait_until(
                self.network_client,
                self.network_client.get_subnet(response.data.id),
                "lifecycle_state",
                "AVAILABLE",
            )
            
            subnet = get_subnet_response.data
            
            return {
                "id": subnet.id,
                "display_name": subnet.display_name,
                "cidr_block": subnet.cidr_block,
                "dns_label": subnet.dns_label,
                "lifecycle_state": subnet.lifecycle_state,
            }
        except Exception as e:
            self.logger.error(f"Error creating subnet: {str(e)}")
            raise

    def launch_instance(
        self,
        compartment_id: str,
        subnet_id: str,
        instance_name: str,
        shape: str,
        image_id: str,
        ssh_public_key: Optional[str] = None,
        ocpus: Optional[float] = None,
        memory_in_gbs: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Launch a compute instance
        
        Args:
            compartment_id: Compartment ID
            subnet_id: Subnet ID
            instance_name: Name of the instance
            shape: Compute shape
            image_id: OS image ID
            ssh_public_key: SSH public key for instance access
            ocpus: Number of OCPUs (for flexible shapes)
            memory_in_gbs: Memory in GBs (for flexible shapes)
            
        Returns:
            Dictionary containing instance details
        """
        try:
            # Create source details
            source_details = oci.core.models.InstanceSourceViaImageDetails(
                image_id=image_id,
            )
            
            # Create shape config for flexible shapes
            shape_config = None
            if ocpus and memory_in_gbs:
                shape_config = oci.core.models.LaunchInstanceShapeConfigDetails(
                    ocpus=ocpus,
                    memory_in_gbs=memory_in_gbs,
                )
            
            # Create metadata
            metadata = {}
            if ssh_public_key:
                metadata["ssh_authorized_keys"] = ssh_public_key
            
            # Create instance details
            instance_details = oci.core.models.LaunchInstanceDetails(
                compartment_id=compartment_id,
                display_name=instance_name,
                shape=shape,
                shape_config=shape_config,
                source_details=source_details,
                create_vnic_details=oci.core.models.CreateVnicDetails(
                    subnet_id=subnet_id,
                    assign_public_ip=True,
                ),
                metadata=metadata,
            )
            
            # Launch instance
            response = self.compute_client.launch_instance(instance_details)
            
            # Wait for instance to be running
            get_instance_response = oci.wait_until(
                self.compute_client,
                self.compute_client.get_instance(response.data.id),
                "lifecycle_state",
                "RUNNING",
            )
            
            instance = get_instance_response.data
            
            # Get VNIC attachments to get public IP
            vnic_attachments = self.compute_client.list_vnic_attachments(
                compartment_id=compartment_id,
                instance_id=instance.id,
            ).data
            
            vnic_id = vnic_attachments[0].vnic_id
            vnic = self.network_client.get_vnic(vnic_id).data
            
            return {
                "id": instance.id,
                "display_name": instance.display_name,
                "shape": instance.shape,
                "lifecycle_state": instance.lifecycle_state,
                "time_created": instance.time_created.isoformat(),
                "public_ip": vnic.public_ip,
                "private_ip": vnic.private_ip,
            }
        except Exception as e:
            self.logger.error(f"Error launching instance: {str(e)}")
            raise

    def create_autonomous_database(
        self,
        compartment_id: str,
        db_name: str,
        display_name: str,
        cpu_core_count: int,
        data_storage_size_in_tbs: int,
        admin_password: str,
        is_free_tier: bool = False,
        db_workload: str = "OLTP",
    ) -> Dict[str, Any]:
        """
        Create an Autonomous Database
        
        Args:
            compartment_id: Compartment ID
            db_name: Database name
            display_name: Display name
            cpu_core_count: Number of CPU cores
            data_storage_size_in_tbs: Data storage size in TBs
            admin_password: Admin password
            is_free_tier: Whether to use free tier
            db_workload: Database workload type (OLTP or DW)
            
        Returns:
            Dictionary containing database details
        """
        try:
            # Create database details
            db_details = oci.database.models.CreateAutonomousDatabaseDetails(
                compartment_id=compartment_id,
                db_name=db_name,
                display_name=display_name,
                cpu_core_count=cpu_core_count,
                data_storage_size_in_tbs=data_storage_size_in_tbs,
                admin_password=admin_password,
                is_free_tier=is_free_tier,
                db_workload=db_workload,
            )
            
            # Create database
            response = self.database_client.create_autonomous_database(db_details)
            
            # Wait for database to be available
            get_db_response = oci.wait_until(
                self.database_client,
                self.database_client.get_autonomous_database(response.data.id),
                "lifecycle_state",
                "AVAILABLE",
            )
            
            db = get_db_response.data
            
            return {
                "id": db.id,
                "display_name": db.display_name,
                "db_name": db.db_name,
                "lifecycle_state": db.lifecycle_state,
                "time_created": db.time_created.isoformat(),
                "connection_strings": db.connection_strings.all_connection_strings,
            }
        except Exception as e:
            self.logger.error(f"Error creating Autonomous Database: {str(e)}")
            raise

    def create_block_volume(
        self,
        compartment_id: str,
        display_name: str,
        size_in_gbs: int,
        vpus_per_gb: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create a block volume
        
        Args:
            compartment_id: Compartment ID
            display_name: Display name
            size_in_gbs: Size in GBs
            vpus_per_gb: Volume performance units per GB
            
        Returns:
            Dictionary containing volume details
        """
        try:
            # Create volume details
            volume_details = oci.core.models.CreateVolumeDetails(
                compartment_id=compartment_id,
                display_name=display_name,
                size_in_gbs=size_in_gbs,
            )
            
            # Add performance if specified
            if vpus_per_gb:
                volume_details.vpus_per_gb = vpus_per_gb
            
            # Create volume
            response = self.block_storage_client.create_volume(volume_details)
            
            # Wait for volume to be available
            get_volume_response = oci.wait_until(
                self.block_storage_client,
                self.block_storage_client.get_volume(response.data.id),
                "lifecycle_state",
                "AVAILABLE",
            )
            
            volume = get_volume_response.data
            
            return {
                "id": volume.id,
                "display_name": volume.display_name,
                "size_in_gbs": volume.size_in_gbs,
                "lifecycle_state": volume.lifecycle_state,
                "time_created": volume.time_created.isoformat(),
            }
        except Exception as e:
            self.logger.error(f"Error creating block volume: {str(e)}")
            raise

    def create_load_balancer(
        self,
        compartment_id: str,
        display_name: str,
        subnet_ids: List[str],
        shape_name: str,
        is_private: bool = False,
        shape_details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a load balancer
        
        Args:
            compartment_id: Compartment ID
            display_name: Display name
            subnet_ids: List of subnet IDs
            shape_name: Shape name
            is_private: Whether the load balancer is private
            shape_details: Shape details for flexible shapes
            
        Returns:
            Dictionary containing load balancer details
        """
        try:
            # Create shape details if provided
            lb_shape_details = None
            if shape_details:
                lb_shape_details = oci.load_balancer.models.ShapeDetails(
                    minimum_bandwidth_in_mbps=shape_details.get("min_bandwidth_mbps", 10),
                    maximum_bandwidth_in_mbps=shape_details.get("max_bandwidth_mbps", 100),
                )
            
            # Create load balancer details
            lb_details = oci.load_balancer.models.CreateLoadBalancerDetails(
                compartment_id=compartment_id,
                display_name=display_name,
                shape_name=shape_name,
                subnet_ids=subnet_ids,
                is_private=is_private,
                shape_details=lb_shape_details,
            )
            
            # Create load balancer
            response = self.load_balancer_client.create_load_balancer(lb_details)
            
            # Get the work request ID
            work_request_id = response.headers["opc-work-request-id"]
            
            # Wait for the work request to complete
            work_request_response = oci.wait_until(
                self.load_balancer_client,
                self.load_balancer_client.get_work_request(work_request_id),
                "lifecycle_state",
                "SUCCEEDED",
            )
            
            # Get the load balancer ID from the work request
            lb_id = None
            for resource in work_request_response.data.resources:
                if resource.entity_type == "loadbalancer":
                    lb_id = resource.identifier
                    break
            
            if not lb_id:
                raise Exception("Failed to get load balancer ID from work request")
            
            # Get load balancer details
            lb = self.load_balancer_client.get_load_balancer(lb_id).data
            
            return {
                "id": lb.id,
                "display_name": lb.display_name,
                "shape_name": lb.shape_name,
                "ip_addresses": [ip.ip_address for ip in lb.ip_addresses],
                "lifecycle_state": lb.lifecycle_state,
                "time_created": lb.time_created.isoformat(),
            }
        except Exception as e:
            self.logger.error(f"Error creating load balancer: {str(e)}")
            raise

    def create_bucket(
        self,
        compartment_id: str,
        namespace_name: str,
        bucket_name: str,
        storage_tier: str = "Standard",
        public_access_type: str = "NoPublicAccess",
    ) -> Dict[str, Any]:
        """
        Create an object storage bucket
        
        Args:
            compartment_id: Compartment ID
            namespace_name: Namespace name
            bucket_name: Bucket name
            storage_tier: Storage tier
            public_access_type: Public access type
            
        Returns:
            Dictionary containing bucket details
        """
        try:
            # Create bucket details
            bucket_details = oci.object_storage.models.CreateBucketDetails(
                compartment_id=compartment_id,
                name=bucket_name,
                storage_tier=storage_tier,
                public_access_type=public_access_type,
            )
            
            # Create bucket
            response = self.object_storage_client.create_bucket(
                namespace_name=namespace_name,
                create_bucket_details=bucket_details,
            )
            
            bucket = response.data
            
            return {
                "name": bucket.name,
                "namespace": namespace_name,
                "compartment_id": bucket.compartment_id,
                "storage_tier": bucket.storage_tier,
                "public_access_type": bucket.public_access_type,
                "time_created": bucket.time_created.isoformat(),
            }
        except Exception as e:
            self.logger.error(f"Error creating bucket: {str(e)}")
            raise

    def get_namespace(self) -> str:
        """
        Get the object storage namespace
        
        Returns:
            Namespace name
        """
        try:
            response = self.object_storage_client.get_namespace()
            return response.data
        except Exception as e:
            self.logger.error(f"Error getting namespace: {str(e)}")
            raise
