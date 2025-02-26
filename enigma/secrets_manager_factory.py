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

import os
import getpass
import logging
from typing import Optional

from .bw_manager import BitwardenManager
from .aws_manager import AwsManager
from .hc_manager import HashicorpManager

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
_logger = logging.getLogger(__name__)


class SecretsManagerFactory:
    _bw_manager: Optional[BitwardenManager] = None
    _aws_manager: Optional[AwsManager] = None
    _hc_manager: Optional[HashicorpManager] = None

    @classmethod
    def get_bitwarden_manager(cls, email=None, password=None):
        """
        Gets or creates a BitwardenManager instance.

        Args:
            email (str, optional): Bitwarden email. If not provided,
                                  will try environment variables or prompt.
            password (str, optional): Bitwarden password. If not provided,
                                     will try environment variables or prompt.

        Returns:
            BitwardenManager: The singleton BitwardenManager instance

        Raises:
            ValueError: If credentials cannot be obtained
        """
        if cls._bw_manager is None:
            _logger.debug("Creating new Bitwarden manager")

            # Try to get credentials from parameters or environment
            if email is None:
                email = os.environ.get("BW_EMAIL")
            if password is None:
                password = os.environ.get("BW_PASSWORD")

            # If still not available, prompt the user
            if not email or not password:
                email = input("Bitwarden email: ")
                password = getpass.getpass("Bitwarden master password: ")

                if not email or not password:
                    raise ValueError("Bitwarden credentials are required")

            cls._bw_manager = BitwardenManager(email, password)

        return cls._bw_manager

    @classmethod
    def get_aws_manager(cls):
        """
        Gets or creates an AwsManager instance.

        Returns:
            AwsManager: The singleton AwsManager instance
        """
        if cls._aws_manager is None:
            _logger.debug("Creating new AWS manager")
            cls._aws_manager = AwsManager()

        return cls._aws_manager

    @classmethod
    def get_hashicorp_manager(
        cls, vault_addr=None, vault_token=None, vault_cacert=None
    ):
        """
        Gets or creates a HashicorpManager instance.

        Args:
            vault_addr (str, optional): Vault address. If not provided,
                                       will try environment variables or prompt.
            vault_token (str, optional): Vault token. If not provided,
                                        will try environment variables or prompt.
            vault_cacert (str, optional): Path to CA certificate. If not provided,
                                         will try environment variables or prompt.

        Returns:
            HashicorpManager: The singleton HashicorpManager instance

        Raises:
            ValueError: If required credentials cannot be obtained
        """
        if cls._hc_manager is None:
            _logger.debug("Creating new Hashicorp manager")

            # Try to get credentials from parameters or environment
            if vault_addr is None:
                vault_addr = os.environ.get("VAULT_ADDR")
            if vault_token is None:
                vault_token = os.environ.get("VAULT_TOKEN")
            if vault_cacert is None:
                vault_cacert = os.environ.get("VAULT_CACERT")

            # If still not available, prompt the user
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

            cls._hc_manager = HashicorpManager(vault_addr, vault_token, vault_cacert)

        return cls._hc_manager

    @classmethod
    def reset_managers(cls):
        """
        Resets all manager instances. Primarily used for testing or when
        credentials need to be refreshed.
        """
        cls._bw_manager = None
        cls._aws_manager = None
        cls._hc_manager = None
