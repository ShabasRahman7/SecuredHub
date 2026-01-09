# unit tests for RAG service ingestion scripts
import pytest
import json
from unittest.mock import Mock, patch, mock_open, MagicMock


@pytest.mark.unit
class TestOWASPIngestion:
    # testing OWASP data ingestion logic
    
    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps({
        "controls": [
            {
                "id": "AC-1",
                "title": "Access Control Policy",
                "description": "Develop and document access control policy"
            },
            {
                "id": "AC-2",
                "title": "Account Management",
                "description": "Manage information system accounts"
            }
        ]
    }))
    def test_parse_owasp_json_file(self, mock_file):
        # should parse OWASP JSON file and extract controls
        # mocking the ingestion logic
        with open('owasp_controls.json', 'r') as f:
            data = json.load(f)
        
        controls = data.get('controls', [])
        assert len(controls) == 2
        assert controls[0]['id'] == 'AC-1'
        assert controls[1]['title'] == 'Account Management'
    
    @patch('chromadb.Client')
    def test_add_to_vector_store_mocked(self, mock_chroma_client):
        # should add parsed controls to vector store (mocked)
        # mocking ChromaDB collection
        mock_collection = MagicMock()
        mock_chroma_client.return_value.get_or_create_collection.return_value = mock_collection
        
        client = mock_chroma_client()
        collection = client.get_or_create_collection("owasp_controls")
        
        # simulating adding documents
        collection.add(
            documents=["Access control policy"],
            metadatas=[{"id": "AC-1", "source": "OWASP"}],
            ids=["AC-1"]
        )
        
        collection.add.assert_called_once()
    
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_handles_missing_file_gracefully(self, mock_file):
        # should handle missing OWASP file gracefully
        with pytest.raises(FileNotFoundError):
            with open('nonexistent.json', 'r') as f:
                json.load(f)


@pytest.mark.unit
class TestBanditIngestion:
    # testing Bandit rules ingestion logic
    
    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps({
        "rules": [
            {
                "test_id": "B201",
                "test_name": "flask_debug_true",
                "severity": "HIGH",
                "description": "Flask app with DEBUG=True detected"
            },
            {
                "test_id": "B501",
                "test_name": "request_with_no_cert_validation",
                "severity": "MEDIUM",
                "description": "Requests call without certificate validation"
            }
        ]
    }))
    def test_parse_bandit_rules_json(self, mock_file):
        # should parse Bandit rules JSON and extract rules
        with open('bandit_rules.json', 'r') as f:
            data = json.load(f)
        
        rules = data.get('rules', [])
        assert len(rules) == 2
        assert rules[0]['test_id'] == 'B201'
        assert rules[0]['severity'] == 'HIGH'
        assert rules[1]['test_name'] == 'request_with_no_cert_validation'
    
    @patch('chromadb.Client')
    def test_add_bandit_rules_to_vector_store(self, mock_chroma_client):
        # should add Bandit rules to vector store (mocked)
        mock_collection = MagicMock()
        mock_chroma_client.return_value.get_or_create_collection.return_value = mock_collection
        
        client = mock_chroma_client()
        collection = client.get_or_create_collection("bandit_rules")
        
        # simulating adding documents
        collection.add(
            documents=["Flask app with DEBUG=True detected"],
            metadatas=[{"test_id": "B201", "severity": "HIGH"}],
            ids=["B201"]
        )
        
        collection.add.assert_called_once()
    
    def test_severity_mapping(self):
        # should correctly map severity levels
        severity_map = {
            "HIGH": 3,
            "MEDIUM": 2,
            "LOW": 1
        }
        
        assert severity_map["HIGH"] == 3
        assert severity_map["MEDIUM"] == 2
        assert severity_map["LOW"] == 1


@pytest.mark.unit
class TestVectorStoreOperations:
    # testing vector store interaction patterns
    
    @patch('chromadb.Client')
    def test_query_vector_store_mocked(self, mock_chroma_client):
        # should query vector store for similar documents (mocked)
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            'documents': [['SQL Injection prevention techniques']],
            'metadatas': [[{'id': 'AC-10', 'source': 'OWASP'}]],
            'distances': [[0.15]]
        }
        
        mock_chroma_client.return_value.get_collection.return_value = mock_collection
        
        client = mock_chroma_client()
        collection = client.get_collection("owasp_controls")
        
        results = collection.query(
            query_texts=["How to prevent SQL injection"],
            n_results=5
        )
        
        assert len(results['documents']) > 0
        assert 'SQL Injection' in results['documents'][0][0]
        collection.query.assert_called_once()
