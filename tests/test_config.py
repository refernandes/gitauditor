import os
import json
import pytest
from gitauditor.core.config import ConfigManager

def test_load_config_creates_default(mocker, tmp_path):
    mocker.patch("gitauditor.core.config.CONFIG_DIR", str(tmp_path))
    mocker.patch("gitauditor.core.config.CONFIG_FILE", str(tmp_path / "config.json"))
    
    config = ConfigManager.load_config()
    assert config["ai"]["provider"] == "ollama"
    assert os.path.exists(tmp_path / "config.json")

def test_load_config_reads_existing(mocker, tmp_path):
    mocker.patch("gitauditor.core.config.CONFIG_DIR", str(tmp_path))
    config_file = tmp_path / "config.json"
    mocker.patch("gitauditor.core.config.CONFIG_FILE", str(config_file))
    
    with open(config_file, "w") as f:
        json.dump({"ai": {"provider": "openai"}}, f)
        
    config = ConfigManager.load_config()
    assert config["ai"]["provider"] == "openai"

def test_load_config_handles_exception(mocker, tmp_path):
    mocker.patch("gitauditor.core.config.CONFIG_DIR", str(tmp_path))
    config_file = tmp_path / "config.json"
    mocker.patch("gitauditor.core.config.CONFIG_FILE", str(config_file))
    
    with open(config_file, "w") as f:
        f.write("invalid json")
        
    config = ConfigManager.load_config()
    assert config["ai"]["provider"] == "ollama"

def test_save_config(mocker, tmp_path):
    mocker.patch("gitauditor.core.config.CONFIG_DIR", str(tmp_path))
    config_file = tmp_path / "config.json"
    mocker.patch("gitauditor.core.config.CONFIG_FILE", str(config_file))
    
    ConfigManager.save_config({"ai": {"provider": "azure"}})
    
    with open(config_file, "r") as f:
        data = json.load(f)
        
    assert data["ai"]["provider"] == "azure"
    
    # check permissions
    st = os.stat(config_file)
    assert oct(st.st_mode)[-3:] == "600"
