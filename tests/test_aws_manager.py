import pytest
from unittest.mock import patch

from botocore.exceptions import EndpointConnectionError

from enigma.aws_manager import AwsManager


@pytest.fixture
def aws_manager_instance():
    return AwsManager()


def test_initialization():
    manager = AwsManager()
    assert manager.client is not None


def test_initialization_failure():
    with patch("boto3.client") as mock_client:
        mock_client.side_effect = EndpointConnectionError
        with pytest.raises(Exception):
            AwsManager()


def test_retrieve_and_format_credentials_success(aws_manager_instance):
    with patch.object(
        aws_manager_instance.client, "get_secret_value"
    ) as mock_get_secret:
        mock_get_secret.return_value = {
            "SecretString": '{"username": "user", "password": "pass"}'
        }
        credentials = aws_manager_instance._retrieve_and_format_credentials(
            "secret_name"
        )
        assert credentials is not None
        assert credentials["username"] == "user"
        assert credentials["password"] == "pass"


def test_retrieve_and_format_credentials_failure(aws_manager_instance):
    with patch.object(
        aws_manager_instance.client, "get_secret_value"
    ) as mock_get_secret:
        mock_get_secret.side_effect = Exception("Retrieval failed")
        with pytest.raises(Exception):
            aws_manager_instance._retrieve_and_format_credentials("secret_name")


def test_get_secret_success(aws_manager_instance):
    with patch.object(
        aws_manager_instance, "_retrieve_and_format_credentials"
    ) as mock_retrieve:
        mock_retrieve.return_value = {"api_token": "token_value"}
        secret = aws_manager_instance.get_secret("secret_name", "api_token")
        assert secret == "token_value"


def test_get_secret_failure(aws_manager_instance):
    with patch.object(
        aws_manager_instance, "_retrieve_and_format_credentials"
    ) as mock_retrieve:
        mock_retrieve.side_effect = Exception
        with pytest.raises(Exception):
            secret = aws_manager_instance.get_secret("secret_name", "api_token")
            assert secret == ""
