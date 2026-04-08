import pytest
import os
import json
import tempfile
from unittest.mock import patch, mock_open, MagicMock

from config_loader import (
    load_configuration,
    add_ignore_pattern,
    validate_config,
    get_indexing_settings,
    fetch_defaults,
    resolve_base_path
)

# Fixtures
@pytest.fixture
def valid_config_data():
    return {
        "project_name": "test_project",
        "paths": ["src", "tests"],
        "ignore_rules": ["*.pyc", "__pycache__"],
        "indexing": {
            "enabled": True,
            "mode": "full"
        }
    }

@pytest.fixture
def invalid_config_data():
    return {
        "project_name": "test_project",
        "paths": [],
        "indexing": {}
    }

@pytest.fixture
def config_file_path(tmp_path, valid_config_data):
    file_path = tmp_path / "config.json"
    file_path.write_text(json.dumps(valid_config_data))
    return str(file_path)

@pytest.fixture
def empty_config():
    return {"ignore_rules": [], "indexing": {"enabled": False, "mode": "minimal"}}

# Test cases for load_configuration

def test_load_configuration_success(tmp_path, valid_config_data):
    config_path = str(tmp_path / "config.json")
    with open(config_path, 'w') as f:
        json.dump(valid_config_data, f)
    
    result = load_configuration(config_path)
    assert result["project_name"] == valid_config_data["project_name"]
    assert result["paths"] == valid_config_data["paths"]

def test_load_configuration_file_not_found():
    fake_path = "/nonexistent/config.json"
    with pytest.raises(FileNotFoundError):
        load_configuration(fake_path)

def test_load_configuration_invalid_json(tmp_path):
    config_path = str(tmp_path / "invalid.json")
    config_path.write_text("{ invalid json content }")
    
    with pytest.raises(ValueError):
        load_configuration(config_path)

# Test cases for add_ignore_pattern

def test_add_ignore_pattern_new_pattern(valid_config_data):
    config = valid_config_data.copy()
    config["ignore_rules"] = list(config["ignore_rules"])
    new_config = add_ignore_pattern(config, "temp_folder")
    
    assert "temp_folder" in new_config["ignore_rules"]
    assert len(new_config["ignore_rules"]) == 4

def test_add_ignore_pattern_duplicate_pattern(valid_config_data):
    config = valid_config_data.copy()
    config["ignore_rules"] = list(config["ignore_rules"])
    new_config = add_ignore_pattern(config, "*.pyc")
    
    assert len(new_config["ignore_rules"]) == len(config["ignore_rules"])
    assert new_config["ignore_rules"].count("*.pyc") == 1

def test_add_ignore_pattern_empty_config():
    config = {"ignore_rules": []}
    new_config = add_ignore_pattern(config, "new_rule")
    assert len(new_config["ignore_rules"]) == 1
    assert new_config["ignore_rules"][0] == "new_rule"

# Test cases for get_indexing_settings

def test_get_indexing_settings_happy_path(valid_config_data):
    settings = get_indexing_settings(valid_config_data)
    assert settings["enabled"] == True
    assert settings["mode"] == "full"

def test_get_indexing_settings_missing_field(empty_config):
    settings = get_indexing_settings(empty_config)
    assert settings["enabled"] == False
    assert settings["mode"] == "minimal"

def test_get_indexing_settings_invalid_config_type():
    with pytest.raises(TypeError):
        get_indexing_settings("not a dict")

# Test cases for fetch_defaults (API Mocking)

@patch('config_loader.requests.get')
def test_fetch_defaults_api_success(mock_get, valid_config_data):
    mock_get.return_value.json.return_value = valid