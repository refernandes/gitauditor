import pytest
import os
from unittest.mock import MagicMock
from gitauditor.core.ssh_audit import IdentityManager

def test_get_global_git_config(mocker):
    # Mock subprocess.run
    mock_run = mocker.patch("subprocess.run")
    
    # Setup mock returns
    mock_name_result = MagicMock()
    mock_name_result.returncode = 0
    mock_name_result.stdout = "Test User\n"
    
    mock_email_result = MagicMock()
    mock_email_result.returncode = 0
    mock_email_result.stdout = "test@example.com\n"
    
    mock_run.side_effect = [mock_name_result, mock_email_result]
    
    configs = IdentityManager.get_global_git_config()
    
    assert configs["name"] == "Test User"
    assert configs["email"] == "test@example.com"

def test_list_ssh_keys(mocker, tmp_path):
    mocker.patch("os.path.expanduser", return_value=str(tmp_path))
    
    # Create fake keys
    (tmp_path / "id_rsa").write_text("private")
    (tmp_path / "id_rsa.pub").write_text("public")
    
    (tmp_path / "id_ed25519").write_text("private")
    (tmp_path / "id_ed25519.pub").write_text("public")
    
    (tmp_path / "other.pub").write_text("public") # no private key
    
    keys = IdentityManager.list_ssh_keys()
    
    assert len(keys) == 2
    types = {k["type"] for k in keys}
    assert "RSA" in types
    assert "Ed25519" in types

def test_set_repo_identity(mocker, tmp_git_repo):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = MagicMock(returncode=0)
    
    result = IdentityManager.set_repo_identity(
        tmp_git_repo, 
        ssh_key_path="/fake/key", 
        name="New Name", 
        email="new@email.com"
    )
    
    assert result is True
    assert mock_run.call_count == 3

@pytest.mark.asyncio
async def test_test_provider_connection_success(mocker):
    mock_create_subprocess_exec = mocker.patch("asyncio.create_subprocess_exec")
    mock_process = MagicMock()
    mock_process.communicate.return_value = (b"", b"successfully authenticated")
    mock_create_subprocess_exec.return_value = mock_process
    
    result = await IdentityManager.test_provider_connection("github.com")
    
    assert result is True

@pytest.mark.asyncio
async def test_test_provider_connection_failure(mocker):
    mock_create_subprocess_exec = mocker.patch("asyncio.create_subprocess_exec")
    mock_process = MagicMock()
    mock_process.communicate.return_value = (b"", b"Permission denied")
    mock_create_subprocess_exec.return_value = mock_process
    
    result = await IdentityManager.test_provider_connection("github.com")
    
    assert result is False
