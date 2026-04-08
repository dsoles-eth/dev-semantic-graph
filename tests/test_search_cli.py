import pytest
from unittest.mock import patch, MagicMock, call
from search_cli import query_graph, get_context, main
import sys

# Fixtures
@pytest.fixture
def mock_graph_client():
    """Mock for the internal graph client used by search_cli."""
    with patch('search_cli.graph_client') as mock_client:
        mock_client.search.return_value = [
            {"id": "node_1", "label": "Project A", "similarity": 0.9},
            {"id": "node_2", "label": "Project B", "similarity": 0.85}
        ]
        mock_client.get_neighbors.return_value = [
            {"id": "node_3", "label": "Dependency 1"},
            {"id": "node_4", "label": "Dependency 2"}
        ]
        yield mock_client

@pytest.fixture
def mocked_graph_client_with_error():
    """Mock client that raises exceptions for error testing."""
    with patch('search_cli.graph_client') as mock_client:
        mock_client.search.side_effect = Exception("Connection timeout")
        mock_client.get_neighbors.side_effect = Exception("Connection timeout")
        yield mock_client

@pytest.fixture
def capsys():
    """Ensure pytest capture is available."""
    return None  # pytest handles this via cli_runner

@pytest.fixture
def mock_args():
    """Fixture to simulate CLI arguments."""
    return ["--query", "semantic", "--limit", "5", "--context"]

# Test Cases for query_graph
class TestQueryGraph:
    @patch.object('search_cli.graph_client', 'search', return_value=[])
    def test_query_graph_returns_results(self, mock_search, mock_graph_client):
        """Test happy path: query returns valid graph nodes."""
        result = query_graph("search term", limit=10)
        assert isinstance(result, list)
        assert len(result) == 2
        mock_search.assert_called_once_with("search term", limit=10)

    @patch.object('search_cli.graph_client', 'search', return_value=[])
    def test_query_graph_no_results(self, mock_search, mock_graph_client):
        """Test no results case: returns empty list."""
        mock_search.return_value = []
        result = query_graph("nonexistent term", limit=5)
        assert result == []

    @patch.object('search_cli.graph_client', 'search', side_effect=Exception("DB Error"))
    def test_query_graph_handles_exceptions(self, mock_search, mock_graph_client):
        """Test error handling: raises specific error on DB failure."""
        with pytest.raises(Exception, match="DB Error"):
            query_graph("bad query", limit=5)

# Test Cases for get_context
class TestGetContext:
    @patch.object('search_cli.graph_client', 'get_neighbors', return_value=[{"id": "c1", "type": "ref"}])
    def test_get_context_happy_path(self, mock_neighbors, mock_graph_client):
        """Test happy path: retrieves context for valid node."""