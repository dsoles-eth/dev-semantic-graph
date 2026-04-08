import pytest
import os
import sys
import ast
from unittest.mock import patch, mock_open, MagicMock

import code_scanner

# Fixtures for file system and parsing mocks

@pytest.fixture
def mock_file_content():
    """Returns sample Python code string for testing parsing."""
    return """
def hello_world():
    return "Hello, World!"

class Calculator:
    def add(self, a, b):
        return a + b
"""

@pytest.fixture
def sample_files(tmp_path):
    """Creates a temporary directory structure with fake code files."""
    sub_dir = tmp_path / "src"
    sub_dir.mkdir()
    (sub_dir / "module_a.py").touch()
    (sub_dir / "module_b.py").touch()
    (sub_dir / "readme.md").touch()
    return tmp_path, sub_dir

@pytest.fixture
def mock_ast_module():
    """Patches the ast module to simulate parsing results without real AST."""
    with patch.object(ast, 'parse', return_value=ast.Module(body=[])) as mock_parse:
        with patch.object(ast, 'dump', return_value="<ast object>") as mock_dump:
            yield mock_parse, mock_dump

# Test Cases for scan_directory

@patch.object(code_scanner, 'os')
def test_scan_directory_returns_found_files(mock_os, sample_files, mock_ast_module):
    """Verify that scan_directory returns a list of paths for supported files."""
    # Arrange
    mock_os.walk = MagicMock(return_value=[
        ("dir", ["folder"], ["file.txt", "file.py"]),
        ("dir/folder", [], ["code.py"])
    ])
    
    base_path, _ = sample_files
    
    # Act
    result = code_scanner.scan_directory(str(base_path))
    
    # Assert
    assert isinstance(result, list)
    assert len(result) == 2
    assert any("file.py" in str(p) for p in result)
    assert any("code.py" in str(p) for p in result)

@patch.object(code_scanner, 'os')
def test_scan_directory_filters_extensions(mock_os, sample_files, mock_ast_module):
    """Verify extension filtering excludes unsupported files."""
    mock_os.walk = MagicMock(return_value=[
        ("dir", ["folder"], ["file.txt", "file.py", "data.txt"]),
    ])
    base_path, _ = sample_files

    # Act
    result = code_scanner.scan_directory(str(base_path), extensions=[".py"])

    # Assert
    assert len(result) == 1
    assert any(str(p).endswith("file.py") for p in result)

@patch.object(code_scanner, 'os')
def test_scan_directory_raises_on_nonexistent_path(mock_os, tmp_path):
    """Verify ValueError is raised when directory does not exist."""
    mock_os.walk.side_effect = FileNotFoundError("directory does not exist")
    
    with pytest.raises(FileNotFoundError):
        code_scanner.scan_directory("/nonexistent/path")

# Test Cases for analyze_file

@patch.object(code_scanner, 'open')
def test_analyze_file_returns_structure(mock_open_func, sample_files, tmp_path, mock_ast_module):
    """Verify analyze_file extracts symbols from a file."""
    # Arrange
    (sample_files[1] / "code.py").write_text("def test(): pass")
    mock_file = mock_open_func(return_value=MagicMock(read=MagicMock(return_value="def test(): pass")))
    mock_ast_module  # Ensure ast is patched globally via fixture
    
    # Act
    result = code_scanner.analyze_file(str(sample_files[1] / "code.py"))

    # Assert
    assert "symbols" in result
    assert result["path"]