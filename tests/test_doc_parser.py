import pytest
import doc_parser
from unittest.mock import patch, mock_open
import io
from pathlib import Path


@pytest.fixture
def sample_markdown():
    return "# Header\n\nThis is **bold** and *italic* text.\n\n- Item 1\n- Item 2"


@pytest.fixture
def sample_rst():
    return "Header\n======\n\nThis is **strong** and *emphasis* text.\n\n- Item 1\n- Item 2"


@pytest.fixture
def sample_docstring():
    return '"""A simple parser module.\n\n    This module extracts text from various formats.\n    """'


@pytest.fixture
def clean_text():
    return "Hello World"


@pytest.fixture
def dirty_text():
    return "