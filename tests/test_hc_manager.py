import pytest
from unittest.mock import patch, MagicMock


from enigma.hc_manager import HashicorpManager

# Create a mock for the return value of get_secret
mock_read_secret = MagicMock()

# Mock the nested structure
mock_read_secret.return_value = {
    "auth": None,
    "data": {
        "data": {"password": "pass", "username": "user"},
        "metadata": {
            "created_time": "2024-11-23T12:20:59.985132927Z",
            "custom_metadata": None,
            "deletion_time": "",
            "destroyed": False,
            "version": 1,
        },
    },
    "lease_duration": 0,
    "lease_id": "",
    "mount_type": "kv",
    "renewable": False,
    "request_id": "d09e2bb5-00ee-576b-6078-5d291d35ccc3",
    "warnings": None,
    "wrap_info": None,
}


def test_initialization():
    with patch("hvac.Client") as mock_client:
        mock_client.return_value.sys.is_initialized.return_value = True
        mock_client.return_value.is_authenticated.return_value = True
        manager = HashicorpManager("http://vault-url", "test-token", "test-certificate")
        assert manager.client is not None
        assert manager.client.sys.is_initialized()
        assert manager.client.is_authenticated()


def test_get_secret_success():
    with patch("hvac.Client") as mock_client:
        # Mock `read_secret_version` method to return the mock we created above
        mock_client.secrets.kv.read_secret_version.return_value = (
            mock_read_secret.return_value
        )

        # Access the mocked return value
        credentials = mock_client.secrets.kv.read_secret_version(path="bugzilla")

        # Make assertions on the mocked return value
        assert credentials is not None
        assert credentials["data"]["data"]["username"] == "user"
        assert credentials["data"]["data"]["password"] == "pass"


def test_get_secret_failure():
    with patch("hvac.Client") as mock_client:

        with pytest.raises(Exception):
            mock_client.secrets.kv.read_secret_version.return_value = (
                mock_read_secret.return_value
            )

            # Access the mocked return value
            credentials = mock_client.secrets.kv.read_secret_version(path="bugzilla")
            assert credentials["data"]["data"]["api_key"] == ""


def test_retrieve_secret_success():
    with patch("hvac.Client") as mock_client:
        mock_client.secrets.kv.read_secret_version(path="bugzilla").return_value = (
            mock_read_secret.return_value
        )

        assert mock_client.secrets.kv.read_secret_version(path="bugzilla") is not None


def test_retrieve_credentials_failure():
    with patch("hvac.Client") as mock_client:
        mock_client.return_value.secrets.kv.read_secret.side_effect = Exception(
            "Vault error"
        )

        mock_manager = HashicorpManager("mock_url", "mock_token", "mock_cert")

        with pytest.raises(Exception):
            # This will call _retrieve_credentials and should raise the exception
            mock_manager._retrieve_credentials("non_existent_key")
