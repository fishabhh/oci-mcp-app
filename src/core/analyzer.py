"""
Resource Analyzer for the OCI MCP Server
"""
import logging
import re
from typing import Any, Dict, List, Optional

from api.schemas import ConversationMessage, OCIResource, ResourceType
from utils.logger import get_logger

logger = get_logger(__name__)


class ResourceAnalyzer:
    """
    Analyzes conversation context to determine resource requirements
    and recommends appropriate OCI resources
    """

    def __init__(self):
        """Initialize the resource analyzer"""
        self.logger = logger

    def analyze_requirements(self, conversation_context: List[ConversationMessage]) -> List[OCIResource]:
        """
        Analyze conversation context to extract resource requirements
        
        Args:
            conversation_context: List of conversation messages
            
        Returns:
            List of recommended OCI resources
        """
        self.logger.info("Analyzing resource requirements from conversation context")
        
        # Extract key information from conversation
        extracted_info = self._extract_information(conversation_context)
        
        # Determine resource requirements based on extracted information
        requirements = self._determine_requirements(extracted_info)
        
        # Generate resource recommendations
        recommendations = self._generate_recommendations(requirements)
        
        self.logger.info(f"Generated {len(recommendations)} resource recommendations")
        return recommendations

    def _extract_information(self, conversation_context: List[ConversationMessage]) -> Dict[str, Any]:
        """
        Extract key information from conversation context
        
        Args:
            conversation_context: List of conversation messages
            
        Returns:
            Dictionary containing extracted information
        """
        # Initialize extracted information
        extracted_info = {
            "website_type": None,
            "expected_traffic": None,
            "database_needs": None,
            "storage_requirements": None,
            "performance_requirements": None,
            "budget_constraints": None,
            "security_requirements": None,
            "availability_requirements": None,
            "scaling_needs": None,
            "region_preferences": None,
        }
        
        # Combine all messages into a single text for analysis
        full_text = " ".join([msg.content for msg in conversation_context])
        
        # Extract website type
        website_patterns = [
            (r"(static|simple)\s+(website|site|web\s+page)", "static"),
            (r"(dynamic|interactive)\s+(website|site|web\s+application)", "dynamic"),
            (r"(e-commerce|ecommerce|online\s+store|shop)", "ecommerce"),
            (r"(blog|content\s+management|cms)", "blog"),
            (r"(api|backend|service)", "api"),
        ]
        
        for pattern, website_type in website_patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                extracted_info["website_type"] = website_type
                break
        
        # Extract expected traffic
        traffic_patterns = [
            (r"(low|small|minimal)\s+(traffic|visitors|users)", "low"),
            (r"(medium|moderate)\s+(traffic|visitors|users)", "medium"),
            (r"(high|large|heavy|substantial)\s+(traffic|visitors|users)", "high"),
        ]
        
        for pattern, traffic_level in traffic_patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                extracted_info["expected_traffic"] = traffic_level
                break
        
        # Extract database needs
        if re.search(r"(database|db|data\s+storage)", full_text, re.IGNORECASE):
            if re.search(r"(sql|relational|mysql|postgresql)", full_text, re.IGNORECASE):
                extracted_info["database_needs"] = "relational"
            elif re.search(r"(nosql|mongodb|document|key-value)", full_text, re.IGNORECASE):
                extracted_info["database_needs"] = "nosql"
            else:
                extracted_info["database_needs"] = "general"
        
        # Extract storage requirements
        storage_match = re.search(r"(\d+)\s*(gb|tb|gigabytes|terabytes)", full_text, re.IGNORECASE)
        if storage_match:
            amount = int(storage_match.group(1))
            unit = storage_match.group(2).lower()
            
            if unit in ["tb", "terabytes"]:
                amount *= 1024  # Convert to GB
            
            extracted_info["storage_requirements"] = amount
        
        # Extract budget constraints
        budget_match = re.search(r"budget\s+of\s+\$?(\d+)", full_text, re.IGNORECASE)
        if budget_match:
            extracted_info["budget_constraints"] = int(budget_match.group(1))
        
        # Extract availability requirements
        if re.search(r"(high\s+availability|ha|always\s+available|99\.9)", full_text, re.IGNORECASE):
            extracted_info["availability_requirements"] = "high"
        
        # Extract scaling needs
        if re.search(r"(scal(e|ing|able)|grow|expand)", full_text, re.IGNORECASE):
            extracted_info["scaling_needs"] = "required"
        
        # Extract region preferences
        region_patterns = [
            (r"(us|united\s+states|america)", "us"),
            (r"(europe|eu|european)", "eu"),
            (r"(asia|apac|asia\s+pacific)", "asia"),
        ]
        
        for pattern, region in region_patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                extracted_info["region_preferences"] = region
                break
        
        self.logger.debug(f"Extracted information: {extracted_info}")
        return extracted_info

    def _determine_requirements(self, extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine resource requirements based on extracted information
        
        Args:
            extracted_info: Dictionary containing extracted information
            
        Returns:
            Dictionary containing resource requirements
        """
        requirements = {
            "compute": self._determine_compute_requirements(extracted_info),
            "network": self._determine_network_requirements(extracted_info),
            "database": self._determine_database_requirements(extracted_info),
            "storage": self._determine_storage_requirements(extracted_info),
        }
        
        self.logger.debug(f"Determined requirements: {requirements}")
        return requirements

    def _determine_compute_requirements(self, extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """Determine compute requirements based on extracted information"""
        compute_req = {
            "instance_count": 1,
            "shape": "VM.Standard.E4.Flex",
            "ocpus": 1,
            "memory_in_gbs": 8,
        }
        
        # Adjust based on website type
        if extracted_info["website_type"] == "static":
            compute_req["shape"] = "VM.Standard.E2.1.Micro"
            compute_req["ocpus"] = 1
            compute_req["memory_in_gbs"] = 1
        elif extracted_info["website_type"] == "ecommerce":
            compute_req["shape"] = "VM.Standard.E4.Flex"
            compute_req["ocpus"] = 2
            compute_req["memory_in_gbs"] = 16
        
        # Adjust based on expected traffic
        if extracted_info["expected_traffic"] == "high":
            compute_req["instance_count"] = 2
            compute_req["ocpus"] = max(compute_req["ocpus"], 4)
            compute_req["memory_in_gbs"] = max(compute_req["memory_in_gbs"], 32)
        
        # Adjust for scaling needs
        if extracted_info["scaling_needs"] == "required":
            compute_req["autoscaling"] = True
            compute_req["min_instances"] = compute_req["instance_count"]
            compute_req["max_instances"] = compute_req["instance_count"] * 3
        
        return compute_req

    def _determine_network_requirements(self, extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """Determine network requirements based on extracted information"""
        network_req = {
            "vcn_cidr": "10.0.0.0/16",
            "subnet_cidr": "10.0.0.0/24",
            "load_balancer": False,
        }
        
        # Add load balancer for high traffic or multiple instances
        compute_req = self._determine_compute_requirements(extracted_info)
        if extracted_info["expected_traffic"] == "high" or compute_req["instance_count"] > 1:
            network_req["load_balancer"] = True
            network_req["load_balancer_shape"] = "flexible"
            network_req["load_balancer_min_shape"] = 10
            network_req["load_balancer_max_shape"] = 100
        
        # Add security list rules based on website type
        network_req["security_list_rules"] = [
            {"protocol": "6", "port": 80, "source": "0.0.0.0/0"},  # HTTP
            {"protocol": "6", "port": 443, "source": "0.0.0.0/0"},  # HTTPS
        ]
        
        # Add SSH access
        network_req["security_list_rules"].append(
            {"protocol": "6", "port": 22, "source": "0.0.0.0/0"}  # SSH
        )
        
        return network_req

    def _determine_database_requirements(self, extracted_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Determine database requirements based on extracted information"""
        if not extracted_info["database_needs"]:
            return None
        
        database_req = {
            "type": "autonomous",
            "workload_type": "OLTP",
            "storage_in_tbs": 1,
            "cpu_core_count": 1,
        }
        
        # Adjust based on database type
        if extracted_info["database_needs"] == "relational":
            database_req["type"] = "autonomous"
            database_req["db_name"] = "OCIDB"
        elif extracted_info["database_needs"] == "nosql":
            database_req["type"] = "nosql"
            database_req["table_name"] = "OCITable"
        
        # Adjust based on expected traffic
        if extracted_info["expected_traffic"] == "high":
            database_req["cpu_core_count"] = 2
            database_req["storage_in_tbs"] = 2
        
        return database_req

    def _determine_storage_requirements(self, extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """Determine storage requirements based on extracted information"""
        storage_req = {
            "block_volume_size_in_gbs": 50,
            "object_storage": True,
        }
        
        # Adjust based on storage requirements
        if extracted_info["storage_requirements"]:
            storage_req["block_volume_size_in_gbs"] = max(
                50, extracted_info["storage_requirements"]
            )
        
        # Adjust based on website type
        if extracted_info["website_type"] == "static":
            storage_req["block_volume_size_in_gbs"] = 50
        elif extracted_info["website_type"] in ["ecommerce", "dynamic"]:
            storage_req["block_volume_size_in_gbs"] = max(
                storage_req["block_volume_size_in_gbs"], 100
            )
        
        return storage_req

    def _generate_recommendations(self, requirements: Dict[str, Any]) -> List[OCIResource]:
        """
        Generate resource recommendations based on requirements
        
        Args:
            requirements: Dictionary containing resource requirements
            
        Returns:
            List of recommended OCI resources
        """
        recommendations = []
        
        # Compute instance recommendation
        compute_req = requirements["compute"]
        compute_resource = OCIResource(
            resource_type=ResourceType.COMPUTE,
            name="WebServer",
            description="Compute instance for hosting the website",
            specifications={
                "shape": compute_req["shape"],
                "ocpus": compute_req["ocpus"],
                "memory_in_gbs": compute_req["memory_in_gbs"],
                "instance_count": compute_req["instance_count"],
                "image_id": "Oracle-Linux-8.6-2022.05.31-0",
            },
            estimated_cost={
                "monthly": 50.0 * compute_req["ocpus"] * compute_req["instance_count"],
                "currency": "USD",
            },
        )
        recommendations.append(compute_resource)
        
        # Network recommendation
        network_req = requirements["network"]
        network_resource = OCIResource(
            resource_type=ResourceType.NETWORK,
            name="WebsiteVCN",
            description="Virtual Cloud Network for the website",
            specifications={
                "vcn_cidr": network_req["vcn_cidr"],
                "subnet_cidr": network_req["subnet_cidr"],
                "security_list_rules": network_req["security_list_rules"],
            },
            estimated_cost={
                "monthly": 0.0,  # VCN is free
                "currency": "USD",
            },
        )
        recommendations.append(network_resource)
        
        # Load balancer recommendation (if needed)
        if network_req["load_balancer"]:
            lb_resource = OCIResource(
                resource_type=ResourceType.LOAD_BALANCER,
                name="WebsiteLoadBalancer",
                description="Load balancer for distributing traffic",
                specifications={
                    "shape": network_req["load_balancer_shape"],
                    "min_bandwidth_mbps": network_req["load_balancer_min_shape"],
                    "max_bandwidth_mbps": network_req["load_balancer_max_shape"],
                },
                estimated_cost={
                    "monthly": 10.0 + (0.0017 * 730 * network_req["load_balancer_min_shape"]),
                    "currency": "USD",
                },
                dependencies=["WebsiteVCN"],
            )
            recommendations.append(lb_resource)
        
        # Database recommendation (if needed)
        if requirements["database"]:
            db_req = requirements["database"]
            db_resource = OCIResource(
                resource_type=ResourceType.DATABASE,
                name="WebsiteDB",
                description="Database for the website",
                specifications={
                    "type": db_req["type"],
                    "workload_type": db_req["workload_type"],
                    "storage_in_tbs": db_req["storage_in_tbs"],
                    "cpu_core_count": db_req["cpu_core_count"],
                },
                estimated_cost={
                    "monthly": 900.0 * db_req["cpu_core_count"],
                    "currency": "USD",
                },
                dependencies=["WebsiteVCN"],
            )
            recommendations.append(db_resource)
        
        # Storage recommendation
        storage_req = requirements["storage"]
        storage_resource = OCIResource(
            resource_type=ResourceType.STORAGE,
            name="WebsiteStorage",
            description="Block volume for the website",
            specifications={
                "size_in_gbs": storage_req["block_volume_size_in_gbs"],
                "vpus_per_gb": 10,
            },
            estimated_cost={
                "monthly": 0.0255 * storage_req["block_volume_size_in_gbs"],
                "currency": "USD",
            },
            dependencies=["WebServer"],
        )
        recommendations.append(storage_resource)
        
        # Object storage bucket (if needed)
        if storage_req["object_storage"]:
            bucket_resource = OCIResource(
                resource_type=ResourceType.STORAGE,
                name="WebsiteBucket",
                description="Object storage bucket for static assets",
                specifications={
                    "storage_tier": "Standard",
                    "auto_tiering": True,
                },
                estimated_cost={
                    "monthly": 0.0255 * 100,  # Assuming 100GB of object storage
                    "currency": "USD",
                },
            )
            recommendations.append(bucket_resource)
        
        return recommendations
