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
import getpass
import logging
import os

from bw_manager import BitwardenManager
from aws_manager import AwsManager
from hc_manager import HashicorpManager

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
_logger = logging.getLogger(__name__)


def get_secret(secrets_manager_name, service_name, credential_name) -> str:
    """
    Function that initializes the corresponding manager and returns the credential
    """
    if secrets_manager_name == "bitwarden":
        # Tries to get the user + password for bitwarden from env vars and if not it prompts the user to put them
        username = os.environ["BW_USERNAME"]
        password = os.environ["BW_PASSWORD"]

        if username and password:
            secrets_handler = BitwardenManager(username, password)
        else:
            username = input("Bitwarden email: ")
            password = getpass.getpass("Bitwarden master password: ")
            secrets_handler = BitwardenManager(username, password)

        return secrets_handler.get_secret(service_name, credential_name)

    elif secrets_manager_name == "hashicorp":
        try:
            # needs to have the things in env variables
            vault_addr = os.environ["VAULT_ADDR"]
            vault_token = os.environ["VAULT_TOKEN"]
            vault_cacert = os.environ["VAULT_CACERT"]
            if vault_addr and vault_token and vault_cacert:
                secrets_handler = HashicorpManager(
                    vault_addr, vault_token, vault_cacert
                )
                return secrets_handler.get_secret(service_name, credential_name)

        except KeyError as e:
            print("Missing environment variables needed to initialize the vault client")
            raise e

    elif secrets_manager_name == "aws":
        secrets_handler = AwsManager()
        return secrets_handler.get_secret(service_name, credential_name)
