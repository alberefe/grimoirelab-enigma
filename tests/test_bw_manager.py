import pytest
import os
from unittest.mock import patch, mock_open, MagicMock
from enigma.bw_manager import BitwardenManager

# Load environment variables for testing
from dotenv import load_dotenv

load_dotenv("../enigma/.env")


@pytest.fixture
def bw_manager_instance():
    bw_email = os.getenv("BW_EMAIL")
    bw_password = os.getenv("BW_PASSWORD")
    return BitwardenManager(bw_email, bw_password)


def test_initialization():
    with patch("builtins.open", mock_open(read_data='{"service": "type"}')):
        manager = BitwardenManager("test@example.com", "password")
        assert manager.service_mapping is not None
        assert isinstance(manager.service_mapping, dict)


def test_login_success(bw_manager_instance):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"userEmail": "test@example.com", "status": "unlocked", "sessionKey": "test_session_key"}',
        )
        session_key = bw_manager_instance._login("test@example.com", "password")
        assert session_key == "test_session_key"


def test_login_failure(bw_manager_instance):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="Login failed")
        bw_manager_wrong_credentials = BitwardenManager("", "")
        session_key = bw_manager_wrong_credentials._login(
            "test@example.com", "wrong_password"
        )
        assert session_key == ""


def test_retrieve_credentials_success(bw_manager_instance):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"login": {"username": "user", "password": "pass"}, '
            '"fields": [{"name": "api_token", "value": "token_value"}]}',
        )
        credentials = bw_manager_instance._retrieve_credentials("service_name")
        assert credentials is not None
        assert isinstance(credentials, dict)
        assert credentials["login"]["username"] == "user"
        assert credentials["login"]["password"] == "pass"


def test_retrieve_credentials_failure(bw_manager_instance):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="Retrieval failed")
        credentials = bw_manager_instance._retrieve_credentials("service_name")
        assert credentials is None


def test_format_credentials(bw_manager_instance):
    credentials = {
        "login": {"username": "user", "password": "pass"},
        "fields": [{"name": "api_token", "value": "token_value"}],
    }
    formatted_credentials = bw_manager_instance._format_credentials(credentials)
    assert formatted_credentials["username"] == "user"
    assert formatted_credentials["password"] == "pass"
    assert formatted_credentials["api_token"] == "token_value"


def test_get_secret(bw_manager_instance):
    with patch.object(bw_manager_instance, "_retrieve_credentials") as mock_retrieve:
        mock_retrieve.return_value = {
            "login": {"username": "user", "password": "pass"},
            "fields": [{"name": "api_token", "value": "token_value"}],
        }
        secret = bw_manager_instance.get_secret("service_name", "api_token")
        assert secret == "token_value"
