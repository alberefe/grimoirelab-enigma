import hvac
from secrets_manager import SecretsManager
import utils


class HashicorpManager(SecretsManager):

    def __init__(self, vault_url, token, certificate):
        """
        Initializes the client with the corresponding token to interact with the vault, so no login
        is required in vault.

        Args:
            vault_url (str): The vault URL.
            token (str): The access token.
            certificate (str): The tls certificate.
        """
        self.client = hvac.Client(url=vault_url, token=token, verify=certificate)

        if self.client.sys.is_initialized():
            print("Client is initialized")

        if self.client.is_authenticated():
            print("Client is authenticated")

    def _format_credentials(self, credentials: dict) -> dict:
        """
        Function responsible for formatting the credentials so we can put them into
        the funcion set_environment_variables.

        Args:
            credentials (dict): A dictionary containing the raw credentials retrieved from the vault.

        """
        formatted_credentials = {}
        for key, value in credentials["data"]["data"].items():
            formatted_credentials[key] = value

        return formatted_credentials

    def _retrieve_credentials(self, service_name: str) -> dict:
        """
        Function responsible for retrieving credentials from vault

        Args:
            service_name (str): The name of the service to retrieve credentials for
        Returns:
            a dict containing all the data for that service. Includes metadata and other information stored in the vault
        """
        secret = self.client.secrets.kv.read_secret(path=service_name)

        return secret

    def get_secret(self, service_name: str) -> bool:
        try:
            # Retrieves the credentials from vault
            credentials = self._retrieve_credentials(service_name)
            # Formats the credentials so we can assign their values to env vars
            # If there's no need to assign the env vars, I could just return this dict
            formatted_credentials = self._format_credentials(credentials)
            # Sets env vars
            utils.set_environment_variables(service_name, formatted_credentials)
            return True
        except Exception as e:
            print("Could not retrieve credentials from vault")
            return False
