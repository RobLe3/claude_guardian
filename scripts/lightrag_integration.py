#!/usr/bin/env python3
"""
LightRAG Integration for Claude Guardian
Lightweight RAG implementation for storing and retrieving security information
"""

import asyncio
import json
import logging
import requests
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LightRAG:
    """Lightweight RAG implementation for Claude Guardian"""
    
    def __init__(self, qdrant_url: str = "http://localhost:6333"):
        self.qdrant_url = qdrant_url
        self.collections = {
            'threat_patterns': 'threat_patterns',
            'security_procedures': 'security_procedures', 
            'attack_signatures': 'attack_signatures',
            'vulnerability_db': 'vulnerability_db'
        }
        
    async def initialize_collections(self):
        """Initialize Qdrant collections for RAG storage"""
        logger.info("🔧 Initializing LightRAG collections...")
        
        collection_configs = {
            'security_procedures': {
                "vectors": {"size": 384, "distance": "Cosine"},
                "hnsw_config": {"m": 16, "ef_construct": 100}
            },
            'vulnerability_db': {
                "vectors": {"size": 384, "distance": "Cosine"},
                "hnsw_config": {"m": 16, "ef_construct": 100}
            },
            'attack_signatures': {
                "vectors": {"size": 384, "distance": "Cosine"},
                "hnsw_config": {"m": 16, "ef_construct": 100}
            }
        }
        
        for collection_name, config in collection_configs.items():
            try:
                response = requests.put(
                    f"{self.qdrant_url}/collections/{collection_name}",
                    json=config,
                    headers={"Content-Type": "application/json"}
                )
                if response.status_code in [200, 409]:  # 200 = created, 409 = already exists
                    logger.info(f"✅ Collection '{collection_name}' initialized")
                else:
                    logger.error(f"❌ Failed to create collection '{collection_name}': {response.status_code}")
            except Exception as e:
                logger.error(f"❌ Error creating collection '{collection_name}': {e}")
    
    def create_embedding(self, text: str) -> List[float]:
        """Create simple text embedding (mock implementation)"""
        # Simple hash-based embedding for testing
        # In production, use sentence-transformers or similar
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()[:48]  # 384 bits = 48 bytes
        
        # Convert to normalized float vector
        vector = []
        for i in range(0, len(hash_bytes), 4):
            chunk = hash_bytes[i:i+4]
            if len(chunk) == 4:
                val = int.from_bytes(chunk, byteorder='big') / (2**32 - 1)
                vector.append(val * 2 - 1)  # Normalize to [-1, 1]
        
        # Pad to 384 dimensions
        while len(vector) < 384:
            vector.append(0.0)
        
        return vector[:384]
    
    async def store_security_procedure(self, procedure: Dict[str, Any]) -> bool:
        """Store security procedure in vector database"""
        try:
            # Create embedding from procedure description
            text_content = f"{procedure.get('title', '')} {procedure.get('description', '')} {procedure.get('steps', '')}"
            embedding = self.create_embedding(text_content)
            
            # Create point for Qdrant
            point = {
                "id": procedure.get('id', hash(text_content) % 1000000),
                "vector": embedding,
                "payload": {
                    "title": procedure.get('title'),
                    "description": procedure.get('description'),
                    "category": procedure.get('category', 'general'),
                    "severity": procedure.get('severity', 'medium'),
                    "created_at": datetime.now().isoformat(),
                    "type": "security_procedure"
                }
            }
            
            # Store in Qdrant
            response = requests.put(
                f"{self.qdrant_url}/collections/security_procedures/points",
                json={"points": [point]},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Stored procedure: {procedure.get('title', 'Unknown')}")
                return True
            else:
                logger.error(f"❌ Failed to store procedure: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error storing procedure: {e}")
            return False
    
    async def store_vulnerability_info(self, vuln: Dict[str, Any]) -> bool:
        """Store vulnerability information"""
        try:
            text_content = f"{vuln.get('name', '')} {vuln.get('description', '')} {vuln.get('impact', '')}"
            embedding = self.create_embedding(text_content)
            
            point = {
                "id": vuln.get('cve_id', hash(text_content) % 1000000),
                "vector": embedding,
                "payload": {
                    "cve_id": vuln.get('cve_id'),
                    "name": vuln.get('name'),
                    "description": vuln.get('description'),
                    "severity": vuln.get('severity', 'medium'),
                    "cvss_score": vuln.get('cvss_score', 0.0),
                    "mitigation": vuln.get('mitigation', ''),
                    "created_at": datetime.now().isoformat(),
                    "type": "vulnerability"
                }
            }
            
            response = requests.put(
                f"{self.qdrant_url}/collections/vulnerability_db/points",
                json={"points": [point]},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Stored vulnerability: {vuln.get('name', 'Unknown')}")
                return True
            else:
                logger.error(f"❌ Failed to store vulnerability: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error storing vulnerability: {e}")
            return False
    
    async def search_procedures(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for relevant security procedures"""
        try:
            query_embedding = self.create_embedding(query)
            
            search_request = {
                "vector": query_embedding,
                "limit": limit,
                "with_payload": True,
                "score_threshold": 0.3
            }
            
            response = requests.post(
                f"{self.qdrant_url}/collections/security_procedures/points/search",
                json=search_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                results = response.json().get('result', [])
                procedures = []
                for result in results:
                    procedures.append({
                        'score': result.get('score', 0.0),
                        'procedure': result.get('payload', {})
                    })
                return procedures
            else:
                logger.error(f"❌ Search failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error searching procedures: {e}")
            return []
    
    async def search_vulnerabilities(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for relevant vulnerabilities"""
        try:
            query_embedding = self.create_embedding(query)
            
            search_request = {
                "vector": query_embedding,
                "limit": limit,
                "with_payload": True,
                "score_threshold": 0.3
            }
            
            response = requests.post(
                f"{self.qdrant_url}/collections/vulnerability_db/points/search",
                json=search_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                results = response.json().get('result', [])
                vulnerabilities = []
                for result in results:
                    vulnerabilities.append({
                        'score': result.get('score', 0.0),
                        'vulnerability': result.get('payload', {})
                    })
                return vulnerabilities
            else:
                logger.error(f"❌ Vulnerability search failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error searching vulnerabilities: {e}")
            return []


async def populate_sample_data(lightrag: LightRAG):
    """Populate with sample security data"""
    logger.info("📚 Populating sample security data...")
    
    # Sample security procedures
    procedures = [
        {
            "id": 1,
            "title": "Code Injection Prevention",
            "description": "Procedures to prevent code injection attacks like eval() and exec()",
            "category": "code_security",
            "severity": "high",
            "steps": "1. Never use eval() 2. Sanitize input 3. Use parameterized queries"
        },
        {
            "id": 2,
            "title": "SQL Injection Mitigation",
            "description": "Steps to prevent SQL injection vulnerabilities",
            "category": "database_security", 
            "severity": "high",
            "steps": "1. Use prepared statements 2. Input validation 3. Least privilege"
        },
        {
            "id": 3,
            "title": "File System Protection",
            "description": "Protecting against unauthorized file access and deletion",
            "category": "file_security",
            "severity": "medium",
            "steps": "1. Path validation 2. Access controls 3. Audit logging"
        }
    ]
    
    # Sample vulnerabilities
    vulnerabilities = [
        {
            "cve_id": "CVE-2024-12345",
            "name": "Python eval() Code Injection",
            "description": "Use of eval() function allows arbitrary code execution",
            "severity": "critical",
            "cvss_score": 9.8,
            "mitigation": "Remove all eval() calls and use ast.literal_eval() for safe evaluation"
        },
        {
            "cve_id": "CVE-2024-67890", 
            "name": "Command Injection via os.system",
            "description": "Unsanitized input passed to os.system() enables command injection",
            "severity": "high",
            "cvss_score": 8.5,
            "mitigation": "Use subprocess with shell=False and input validation"
        }
    ]
    
    # Store procedures
    for procedure in procedures:
        await lightrag.store_security_procedure(procedure)
    
    # Store vulnerabilities  
    for vuln in vulnerabilities:
        await lightrag.store_vulnerability_info(vuln)
    
    logger.info("✅ Sample data population completed")


async def test_rag_functionality(lightrag: LightRAG):
    """Test RAG search functionality"""
    logger.info("🔍 Testing RAG search functionality...")
    
    # Test procedure search
    logger.info("\n--- Testing Procedure Search ---")
    procedures = await lightrag.search_procedures("prevent code injection eval", limit=3)
    for proc in procedures:
        logger.info(f"Score: {proc['score']:.3f} - {proc['procedure'].get('title')}")
    
    # Test vulnerability search
    logger.info("\n--- Testing Vulnerability Search ---")
    vulnerabilities = await lightrag.search_vulnerabilities("sql injection database", limit=3)
    for vuln in vulnerabilities:
        logger.info(f"Score: {vuln['score']:.3f} - {vuln['vulnerability'].get('name')}")
    
    logger.info("✅ RAG functionality testing completed")


async def main():
    """Main function to test LightRAG integration"""
    print("🚀 Claude Guardian LightRAG Integration Test")
    print("=" * 50)
    
    # Initialize LightRAG
    lightrag = LightRAG("http://localhost:6333")
    
    # Initialize collections
    await lightrag.initialize_collections()
    
    # Populate sample data
    await populate_sample_data(lightrag)
    
    # Test functionality
    await test_rag_functionality(lightrag)
    
    print("\n🎉 LightRAG integration test completed!")


if __name__ == "__main__":
    asyncio.run(main())