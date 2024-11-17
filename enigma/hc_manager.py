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

import hvac
import hvac.exceptions
import utils
from enigma import Enigma


class HashicorpManager(Enigma):

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
            self.client = hvac.Client(url=vault_url, token=token, verify=certificate)
        except Exception as e:
            print("An error ocurred initializing the client:" + e)
            # this is dealt with in the get_secret function
            raise e

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
        except hvac.exceptions.Forbidden as e:
            print("There was an error accessing the vault")
            print(e)
        except hvac.exceptions.InternalServerError as e:
            print("internal server error: " + e)
        except hvac.exceptions.InvalidPath as e:
            print("invalid path: " + e)
        except hvac.exceptions.InvalidRequest as e:
            print("invalid request: " + e)
        except hvac.exceptions.RateLimitExceeded as e:
            print("Rate limit Exceeded" + e)
        except hvac.exceptions.Unauthorized:
            print("Unauthorized" + e)
        except hvac.exceptions.UnsupportedOperation as e:
            print("Unsupported operation" + e)
        except hvac.exceptions.VaultError as e:
            print("Vault error: " + e)
        except hvac.exceptions.VaultDown as e:
            print("Vault down: " + e)
        except Exception as e:
            print("Could not retrieve credentials from vault")
            print(e)
            return False
