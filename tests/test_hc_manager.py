import pytest
from unittest.mock import patch
import hvac.exceptions

from enigma.hc_manager import HashicorpManager

# This mock represents a typical response from HashiCorp Vault's KV v2 store
# The structure follows Vault's actual response format
MOCK_SECRET_RESPONSE = {
    "auth": None,
    "data": {
        "data": {"password": "pass", "username": "user", "api_key": "test_key"},
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


@pytest.fixture
def mock_hvac_client():
    with patch("hvac.Client") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.sys.is_initialized.return_value = True
        mock_instance.is_authenticated.return_value = True
        yield mock_client


def test_initialization(mock_hvac_client):
    """Test successful initialization of HashicorpManager.
    Verifies that the manager properly creates and configures the Vault client."""

    manager = HashicorpManager("http://vault-url", "test-token", "test-certificate")

    assert manager.client is not None
    mock_hvac_client.assert_called_once_with(
        url="http://vault-url", token="test-token", verify="test-certificate"
    )
    assert manager.client.sys.is_initialized()
    assert manager.client.is_authenticated()


def test_initialization_failure(mock_hvac_client):
    """Test handling of initialization failures.
    Verifies that the manager properly handles connection errors."""

    mock_hvac_client.side_effect = hvac.exceptions.VaultError("Connection failed")

    with pytest.raises(hvac.exceptions.VaultError) as exception_info:
        HashicorpManager("http://vault-url", "test-token", "test-certificate")
    assert "Connection failed" in str(exception_info.value)


def test_get_secret_success(mock_hvac_client):
    """Test successful secret retrieval.
    Verifies that the manager can properly retrieve and extract a secret value."""

    # Configure mock to return our test secret
    mock_instance = mock_hvac_client.return_value
    mock_instance.secrets.kv.read_secret.return_value = MOCK_SECRET_RESPONSE

    # Create manager and retrieve secret
    manager = HashicorpManager("http://vault-url", "test-token", "test-certificate")
    result = manager.get_secret("test_service", "api_key")

    # Verify the result and that the correct path was queried
    assert result == "test_key"
    mock_instance.secrets.kv.read_secret.assert_called_once_with(path="test_service")


def test_get_secret_not_found(mock_hvac_client):
    """Test handling of missing secrets.
    Verifies that the manager returns an empty string when a secret doesn't exist."""

    # Configure mock to simulate missing secret
    mock_instance = mock_hvac_client.return_value
    mock_instance.secrets.kv.read_secret.side_effect = hvac.exceptions.InvalidPath()

    manager = HashicorpManager("http://vault-url", "test-token", "test-certificate")
    result = manager.get_secret("test_service", "nonexistent")

    # Verify empty string is returned for missing secrets
    assert result == ""


def test_get_secret_permission_denied(mock_hvac_client):
    """Test handling of permission denied errors.
    Verifies that the manager properly handles access denied scenarios."""

    # Configure mock to simulate permission denied
    mock_instance = mock_hvac_client.return_value
    mock_instance.secrets.kv.read_secret.side_effect = hvac.exceptions.Forbidden()

    manager = HashicorpManager("http://vault-url", "test-token", "test-certificate")
    result = manager.get_secret("test_service", "api_key")

    # Verify empty string is returned for permission denied
    assert result == ""


def test_retrieve_credentials_success(mock_hvac_client):
    """Test successful retrieval of raw credentials.
    Verifies that the internal _retrieve_credentials method works correctly."""

    # Configure mock to return our test secret
    mock_instance = mock_hvac_client.return_value
    mock_instance.secrets.kv.read_secret.return_value = MOCK_SECRET_RESPONSE

    manager = HashicorpManager("http://vault-url", "test-token", "test-certificate")
    result = manager._retrieve_credentials("test_service")

    # Verify the complete response is returned unmodified
    assert result == MOCK_SECRET_RESPONSE
    mock_instance.secrets.kv.read_secret.assert_called_once_with(path="test_service")


def test_retrieve_credentials_failure(mock_hvac_client):
    """Test handling of credential retrieval failures.
    Verifies that the manager properly propagates Vault errors."""

    # Configure mock to simulate Vault error
    mock_instance = mock_hvac_client.return_value
    mock_instance.secrets.kv.read_secret.side_effect = hvac.exceptions.VaultError(
        "Vault error"
    )

    manager = HashicorpManager("http://vault-url", "test-token", "test-certificate")

    # Verify that Vault errors are propagated
    with pytest.raises(hvac.exceptions.VaultError):
        manager._retrieve_credentials("test_service")


def test_vault_connection_error(mock_hvac_client):
    """Test handling of Vault connection errors.
    Verifies that the manager properly handles network-related failures."""

    # Configure mock to simulate connection error
    mock_instance = mock_hvac_client.return_value
    mock_instance.secrets.kv.read_secret.side_effect = hvac.exceptions.VaultDown(
        "Vault is sealed"
    )

    manager = HashicorpManager("http://vault-url", "test-token", "test-certificate")
    result = manager.get_secret("test_service", "api_key")

    # Verify empty string is returned for connection errors
    assert result == ""
