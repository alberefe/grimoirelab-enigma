#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

import argparse
import getpass
import logging
import os
import sys

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
        # Tries to get the user + password for Bitwarden from env vars and prompts if not available
        email = os.environ.get("BW_EMAIL")
        password = os.environ.get("BW_PASSWORD")

        if not email or not password:
            email = input("Bitwarden email: ")
            password = getpass.getpass("Bitwarden master password: ")

        secrets_handler = BitwardenManager(email, password)
        return secrets_handler.get_secret(service_name, credential_name)

    elif secrets_manager_name == "hashicorp":
        try:
            # Needs environment variables for HashiCorp Vault
            vault_addr = os.environ["VAULT_ADDR"]
            vault_token = os.environ["VAULT_TOKEN"]
            vault_cacert = os.environ["VAULT_CACERT"]

            if not vault_addr:
                vault_addr = input("Please enter vault address: ")
            if not vault_token:
                vault_token = input("Please enter vault token: ")
            if not vault_cacert:
                vault_cacert = input(
                    "Please enter path to a PEM-encoded CA certificate file on the local disk: "
                )

            secrets_handler = HashicorpManager(vault_addr, vault_token, vault_cacert)
            return secrets_handler.get_secret(service_name, credential_name)

        except KeyError as e:
            _logger.error(
                "Missing environment variables needed to initialize the vault client."
            )
            raise e

    elif secrets_manager_name == "aws":
        secrets_handler = AwsManager()
        return secrets_handler.get_secret(service_name, credential_name)

    else:
        _logger.error("Unsupported secrets manager: %s", secrets_manager_name)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Retrieve a secret from a specified secrets manager."
    )
    parser.add_argument(
        "manager",
        choices=["bitwarden", "hashicorp", "aws"],
        help="The name of the secrets manager to use.",
    )
    parser.add_argument(
        "service", help="The name of the service for which to retrieve the credential."
    )
    parser.add_argument("credential", help="The name of the credential to retrieve.")

    args = parser.parse_args()

    try:
        secret = get_secret(args.manager, args.service, args.credential)
        print(f"Retrieved secret: {secret}")
    except Exception as e:
        _logger.error("Error retrieving secret: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
