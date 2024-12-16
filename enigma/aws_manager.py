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
import json
import boto3
from botocore.exceptions import EndpointConnectionError, SSLError, ClientError

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.WARNING)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
_logger = logging.getLogger(__name__)


class AwsManager:

    def __init__(self):
        """
        Initializes the client that will access to the credentials management service.

        This takes the credentials to log into aws from the .aws folder.
        This constructor also takes other relevant information from that folder if it exists.

        Raises:
            Exception: If there's a connection error.
        """

        # Creates a client using the credentials found in the .aws folder
        try:
            _logger.info("Initializing client and login in")
            self.client = boto3.client("secretsmanager")

        except (EndpointConnectionError, SSLError, ClientError, Exception) as e:
            _logger.error("Problem starting the client: %s", e)
            raise e

    def _retrieve_and_format_credentials(self, service_name: str) -> dict:
        """
        Retrieves credentials using the class client.

        Args:
            service_name (str): Name of the service to retrieve credentials for.(or name of the secret)

        Returns:
            formatted_credentials (dict): Dictionary containing the credentials retrieved and formatted as a dict

        Raises:
            Exception: If there's a connection error.
        """
        try:
            _logger.info("Retrieving credentials: %s", service_name)
            secret_value_response = self.client.get_secret_value(SecretId=service_name)
            formatted_credentials = json.loads(secret_value_response["SecretString"])
            return formatted_credentials

        except (
            ClientError,
            self.client.exceptions.InternalServiceError,
        ) as e:
            _logger.error("There was an error retrieving credentials: %s", e)
            raise e

    def get_secret(self, service_name: str, credential_name: str) -> str:
        """
        Gets a secret based on the service name and the desired credential.

        Args:
            service_name (str): Name of the service to retrieve credentials for
            credential_name (str): Name of the credential

        Returns:
            bool: True if something was retrieved, False otherwise

        Raises:
            Exception: If there's a connection error.
        """
        try:
            formatted_credentials = self._retrieve_and_format_credentials(service_name)
            credential = formatted_credentials[credential_name]
            return credential
        except self.client.exceptions.ResourceNotFoundException as e:
            _logger.error("The secret %s was not found.", service_name)
            _logger.error(e)
            return ""
        except Exception as e:
            _logger.error("There was a problem getting the secret")
            raise e
