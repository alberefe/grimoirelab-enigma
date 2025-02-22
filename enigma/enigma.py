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
from typing import Optional

from .bw_manager import BitwardenManager
from .aws_manager import AwsManager
from .hc_manager import HashicorpManager

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
_logger = logging.getLogger(__name__)

# Initialize persistent manager instances so we can utilize cache
_bw_manager: Optional[BitwardenManager] = None
_aws_manager: Optional[AwsManager] = None
_hc_manager: Optional[HashicorpManager] = None


def _initialize_bitwarden() -> BitwardenManager:
    """
    Initialize the Bitwarden manager with proper credentials.

    Returns:
        BitwardenManager: An initialized BitwardenManager instance

    Raises:
        ValueError: If credentials cannot be obtained
    """
    email = os.environ.get("BW_EMAIL")
    password = os.environ.get("BW_PASSWORD")

    if not email or not password:
        email = input("Bitwarden email: ")
        password = getpass.getpass("Bitwarden master password: ")

        if not email or not password:
            raise ValueError("Bitwarden credentials are required")

    return BitwardenManager(email, password)


def _initialize_hashicorp() -> HashicorpManager:
    """
    Initialize the Hashicorp manager with credentials.

    Returns:
        HashicorpManager: An initialized HashicorpManager instance

    Raises:
        ValueError: If required environment variables are missing
    """
    try:
        vault_addr = os.environ.get("VAULT_ADDR")
        vault_token = os.environ.get("VAULT_TOKEN")
        vault_cacert = os.environ.get("VAULT_CACERT")

        if not vault_addr:
            vault_addr = input("Please enter vault address: ")
        if not vault_token:
            vault_token = input("Please enter vault token: ")
        if not vault_cacert:
            vault_cacert = input(
                "Please enter path to a PEM-encoded CA certificate file: "
            )

        if not all([vault_addr, vault_token, vault_cacert]):
            raise ValueError("All Hashicorp Vault credentials are required")

        return HashicorpManager(vault_addr, vault_token, vault_cacert)

    except Exception as e:
        _logger.error("Failed to initialize Hashicorp Vault manager: %s", e)
        raise


def get_secret(
    secrets_manager_name: str, service_name: str, credential_name: str
) -> str:
    """
    Retrieve a secret from the secrets manager.

    Args:
        secrets_manager_name (str): The name of the secrets manager to be used
        service_name (str): The name of the service we want to access
        credential_name (str): The name of the credential we want to retrieve

    Returns:
        str: The credential retrieved

    Raises:
        ValueError: If the secrets manager is not supported or initialization fails
    """
    global _bw_manager, _aws_manager, _hc_manager

    try:
        if secrets_manager_name == "bitwarden":
            # Initialize Bitwarden manager if not already initialized
            if _bw_manager is None:
                _logger.debug("Creating new Bitwarden manager instance")
                _bw_manager = _initialize_bitwarden()
            return _bw_manager.get_secret(service_name, credential_name)

        elif secrets_manager_name == "hashicorp":
            # Initialize Hashicorp manager if not already initialized
            if _hc_manager is None:
                _logger.debug("Creating new Hashicorp manager instance")
                _hc_manager = _initialize_hashicorp()
            return _hc_manager.get_secret(service_name, credential_name)

        elif secrets_manager_name == "aws":
            # Initialize AWS manager if not already initialized
            if _aws_manager is None:
                _logger.debug("Creating new AWS manager instance")
                _aws_manager = AwsManager()
            return _aws_manager.get_secret(service_name, credential_name)

        else:
            raise ValueError(f"Unsupported secrets manager: {secrets_manager_name}")

    except Exception as e:
        _logger.error("Error retrieving secret: %s", e)
        raise


def main():
    """
    Main entry point for the command line interface.
    Parses arguments and retrieves secrets using the appropriate manager.
    """
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
        print(f"Retrieved {args.credential} for {args.service}: {secret}")
    except Exception as e:
        _logger.error("Failed to retrieve secret: %s", e)
        sys.exit(1)

