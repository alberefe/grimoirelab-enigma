# -*- coding: utf-8 -*-
#
#
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Author:
#     Alberto Ferrer Sánchez (alberefe@gmail.com)
#
import logging

import hvac
import hvac.exceptions

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class HashicorpManager:
    """
    A class to retrieve secrets from HashicorpVault
    """

    def __init__(self, vault_url, token, certificate):
        """
        Initializes the client with the corresponding token to interact with the vault, so no login
        is required in vault.

        Args:
            vault_url (str): The vault URL.
            token (str): The access token.
            certificate (str): The tls certificate.
        """
        try:
            logger.info("Creating client and logging in.")
            self.client = hvac.Client(url=vault_url, token=token, verify=certificate)

        except Exception as e:
            logger.error("An error ocurred initializing the client: %e", e)
            # this is dealt with    in the get_secret function
            raise e

        if self.client.sys.is_initialized():
            logger.info("Client is initialized")

        if self.client.is_authenticated():
            logger.info("Client is authenticated")

    def _retrieve_credentials(self, service_name: str) -> dict:
        """
        Function responsible for retrieving credentials from vault

        Args:
            service_name (str): The name of the service to retrieve credentials for

        Returns:
            a dict containing all the data for that service. Includes metadata
            and other information stored in the vault
        """
        try:
            logger.info("Retrieving credentials from vault.")
            secret = self.client.secrets.kv.read_secret(path=service_name)
            return secret
        except Exception as e:
            logger.error("Error retrieving the secret: %e", e)
            # this is dealt with in the get_secret function
            raise e

    def get_secret(self, service_name: str, credential_name: str) -> str:
        """
        Ahora mismo devuelve el valor de la variable de entorno que habrá generado
        al recuperar secretos
        """
        try:
            credentials = self._retrieve_credentials(service_name)
            # We get the exact credential from the dict returned by the retrieval
            credential = credentials["data"]["data"][credential_name]
            return credential
        except (
            hvac.exceptions.Forbidden,
            hvac.exceptions.InternalServerError,
            hvac.exceptions.InvalidPath,
            hvac.exceptions.InvalidRequest,
            hvac.exceptions.RateLimitExceeded,
            hvac.exceptions.Unauthorized,
            hvac.exceptions.UnsupportedOperation,
            hvac.exceptions.VaultDown,
            hvac.exceptions.VaultError,
        ) as e:
            logger.error("There was an error retrieving the secret: %s", e)
            return ""
        except KeyError as e:
            logger.error("The credential %s was not found", credential_name)
            return ""
