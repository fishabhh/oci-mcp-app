"""
Tests for the Resource Analyzer
"""
import sys
import os
import unittest
from typing import List

# Add the src directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.schemas import ConversationMessage, OCIResource
from src.core.analyzer import ResourceAnalyzer


class TestResourceAnalyzer(unittest.TestCase):
    """Test cases for the ResourceAnalyzer class"""

    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = ResourceAnalyzer()

    def test_extract_information_static_website(self):
        """Test extracting information for a static website"""
        # Create test conversation context
        conversation = [
            ConversationMessage(
                role="user",
                content="I need to host a simple static website with low traffic."
            ),
            ConversationMessage(
                role="assistant",
                content="I can help you with that. What kind of content will your website have?"
            ),
            ConversationMessage(
                role="user",
                content="Just some HTML pages, CSS, and images. Nothing complex."
            )
        ]
        
        # Extract information
        extracted_info = self.analyzer._extract_information(conversation)
        
        # Verify extraction
        self.assertEqual(extracted_info["website_type"], "static")
        self.assertEqual(extracted_info["expected_traffic"], "low")

    def test_extract_information_ecommerce(self):
        """Test extracting information for an e-commerce website"""
        # Create test conversation context
        conversation = [
            ConversationMessage(
                role="user",
                content="I want to set up an e-commerce store with a database. I expect moderate traffic."
            ),
            ConversationMessage(
                role="assistant",
                content="I can help you with that. What kind of products will you be selling?"
            ),
            ConversationMessage(
                role="user",
                content="Clothing and accessories. I'll need about 500GB of storage."
            )
        ]
        
        # Extract information
        extracted_info = self.analyzer._extract_information(conversation)
        
        # Verify extraction
        self.assertEqual(extracted_info["website_type"], "ecommerce")
        self.assertEqual(extracted_info["expected_traffic"], "medium")
        self.assertEqual(extracted_info["database_needs"], "general")
        self.assertEqual(extracted_info["storage_requirements"], 500)

    def test_determine_compute_requirements(self):
        """Test determining compute requirements"""
        # Test for static website with low traffic
        extracted_info = {
            "website_type": "static",
            "expected_traffic": "low",
            "database_needs": None,
            "storage_requirements": None,
            "scaling_needs": None,
        }
        
        compute_req = self.analyzer._determine_compute_requirements(extracted_info)
        
        # Verify requirements
        self.assertEqual(compute_req["shape"], "VM.Standard.E2.1.Micro")
        self.assertEqual(compute_req["instance_count"], 1)
        
        # Test for e-commerce with high traffic
        extracted_info = {
            "website_type": "ecommerce",
            "expected_traffic": "high",
            "database_needs": "relational",
            "storage_requirements": 500,
            "scaling_needs": "required",
        }
        
        compute_req = self.analyzer._determine_compute_requirements(extracted_info)
        
        # Verify requirements
        self.assertEqual(compute_req["shape"], "VM.Standard.E4.Flex")
        self.assertEqual(compute_req["instance_count"], 2)
        self.assertTrue(compute_req["autoscaling"])

    def test_generate_recommendations(self):
        """Test generating resource recommendations"""
        # Create test requirements
        requirements = {
            "compute": {
                "instance_count": 2,
                "shape": "VM.Standard.E4.Flex",
                "ocpus": 4,
                "memory_in_gbs": 32,
                "autoscaling": True,
                "min_instances": 2,
                "max_instances": 6,
            },
            "network": {
                "vcn_cidr": "10.0.0.0/16",
                "subnet_cidr": "10.0.0.0/24",
                "load_balancer": True,
                "load_balancer_shape": "flexible",
                "load_balancer_min_shape": 10,
                "load_balancer_max_shape": 100,
                "security_list_rules": [
                    {"protocol": "6", "port": 80, "source": "0.0.0.0/0"},
                    {"protocol": "6", "port": 443, "source": "0.0.0.0/0"},
                    {"protocol": "6", "port": 22, "source": "0.0.0.0/0"},
                ],
            },
            "database": {
                "type": "autonomous",
                "workload_type": "OLTP",
                "storage_in_tbs": 1,
                "cpu_core_count": 2,
            },
            "storage": {
                "block_volume_size_in_gbs": 500,
                "object_storage": True,
            },
        }
        
        # Generate recommendations
        recommendations = self.analyzer._generate_recommendations(requirements)
        
        # Verify recommendations
        self.assertIsInstance(recommendations, list)
        self.assertTrue(len(recommendations) > 0)
        
        # Verify that each recommendation is an OCIResource
        for recommendation in recommendations:
            self.assertIsInstance(recommendation, OCIResource)
        
        # Verify compute recommendation
        compute_rec = next((r for r in recommendations if r.resource_type == "compute"), None)
        self.assertIsNotNone(compute_rec)
        self.assertEqual(compute_rec.specifications["shape"], "VM.Standard.E4.Flex")
        self.assertEqual(compute_rec.specifications["ocpus"], 4)
        
        # Verify database recommendation
        db_rec = next((r for r in recommendations if r.resource_type == "database"), None)
        self.assertIsNotNone(db_rec)
        self.assertEqual(db_rec.specifications["type"], "autonomous")
        self.assertEqual(db_rec.specifications["cpu_core_count"], 2)

    def test_analyze_requirements(self):
        """Test the full analyze_requirements method"""
        # Create test conversation context
        conversation = [
            ConversationMessage(
                role="user",
                content="I need to host an e-commerce website with a database. I expect high traffic and need it to scale automatically."
            ),
            ConversationMessage(
                role="assistant",
                content="I can help you with that. What kind of database do you need?"
            ),
            ConversationMessage(
                role="user",
                content="I need a relational database for storing product information and customer orders."
            ),
            ConversationMessage(
                role="assistant",
                content="How much storage do you think you'll need?"
            ),
            ConversationMessage(
                role="user",
                content="I'll need about 500GB of storage for products, images, and other data."
            )
        ]
        
        # Analyze requirements
        recommendations = self.analyzer.analyze_requirements(conversation)
        
        # Verify recommendations
        self.assertIsInstance(recommendations, list)
        self.assertTrue(len(recommendations) > 0)
        
        # Verify that each recommendation is an OCIResource
        for recommendation in recommendations:
            self.assertIsInstance(recommendation, OCIResource)
        
        # Verify that we have the expected resource types
        resource_types = [r.resource_type for r in recommendations]
        self.assertIn("compute", resource_types)
        self.assertIn("network", resource_types)
        self.assertIn("database", resource_types)
        self.assertIn("storage", resource_types)


if __name__ == "__main__":
    unittest.main()
