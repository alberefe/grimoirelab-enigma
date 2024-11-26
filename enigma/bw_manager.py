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
#       Alberto Ferrer Sánchez (alberefe@gmail.com)
#

import json
import subprocess
import logging

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
_logger = logging.getLogger(__name__)


class BitwardenManager:

    def __init__(self, email: str, password: str):
        """
        Loads credential types mapping from a JSON file to determine expected types of secrets
        for each service in Bitwarden.

        Args:
            email (str): The email of the user
            password (str): The password of the user

        Raises:
            FileNotFoundError: If no credentials file is found
        """
        # Session key of the bw session
        self.session_key = None

        try:
            # load the credential types mapping from the json file and logs in
            _logger.info("Loading credential types from config file")
            credentials_type_file_path = "../config_files/credential_types.json"
            with open(credentials_type_file_path, "r", encoding="utf-8") as file:
                self.service_mapping = json.load(file)
            self._login(email, password)
        except FileNotFoundError:
            _logger.error("File not found")

    def _login(self, bw_email: str, bw_password: str) -> str:
        """
        Logs into Bitwarden and obtains a session key.

        Checks the current Bitwarden session status, unlocking or logging in as necessary.
        If successful, synchronizes the vault.

        Args:
            bw_email (str): Bitwarden account email.
            bw_password (str): Bitwarden account password.

        Returns:
            str: The session key for the current Bitwarden session.

        Raises:
            Exception: If unlocking or logging into Bitwarden fails.
        """
        try:
            _logger.info("Checking Bitwarden login status")
            status_result = subprocess.run(
                ["/snap/bin/bw", "status"], capture_output=True, text=True, check=False
            )

            # if the status command was successful
            if status_result.returncode == 0:
                _logger.info("Checking vault status")
                # Parse the JSON output from `bw status`
                status = json.loads(status_result.stdout)

                if status.get("userEmail") == bw_email:
                    _logger.info("User was already authenticated: %s", bw_email)
                    # If the vault is locked, unlock it
                    if status.get("status") == "locked":
                        _logger.info("Vault locked, unlocking")
                        unlock_result = subprocess.run(
                            ["/snap/bin/bw", "unlock", bw_password, "--raw"],
                            capture_output=True,
                            text=True,
                            check=False,
                        )

                        if unlock_result.returncode != 0:
                            _logger.error(
                                "Error unlocking vault: %s", unlock_result.stderr
                            )
                            return ""

                        # Set the session key
                        self.session_key = unlock_result.stdout.strip()

                    elif status.get("status") == "unlocked":
                        _logger.info("Vault unlocked, getting session key")

                        # If already unlocked, retrieve the current session key
                        self.session_key = status.get("sessionKey")

                    # Ensure session key is set
                    if not self.session_key:
                        _logger.info("Couldn't obtain session key during login")
                        return ""

                else:
                    _logger.info("Login in: %s", bw_email)
                    # Login to Bitwarden if not already logged in
                    result = subprocess.run(
                        ["/snap/bin/bw", "login", bw_email, bw_password, "--raw"],
                        capture_output=True,
                        text=True,
                        check=False,
                    )

                    # Check if the login was successful
                    if result.returncode != 0:
                        _logger.error("Error logging in: %s ", result.stderr)
                        return ""

                    # Setting session key
                    _logger.info("Setting session key")
                    self.session_key = result.stdout.strip()

            # Sync the vault
            if self.session_key:
                _logger.info("Syncing local vault with Bitwarden")
                subprocess.run(
                    ["/snap/bin/bw", "sync", "--session", self.session_key], check=True
                )
                return self.session_key

            _logger.info("Session key not found cause could not log in")
            return ""

        except Exception as e:
            _logger.error("There was a problem login in: %s", e)
            raise e

    def _retrieve_credentials(self, service_name: str) -> dict:
        """
        Retrieves a secret from a particular service from the Bitwarden vault.

        Args:
            service_name (str): The name of the service for which to retrieve the secret.

        Returns:
            dict: The secret item retrieved from Bitwarden as a dictionary.

        Raises:
            Exception: If retrieval of the secret fails.
        """
        try:
            _logger.info("Retrieving credential: %s", service_name)
            result = subprocess.run(
                [
                    "/snap/bin/bw",
                    "get",
                    "item",
                    service_name,
                    "--session",
                    self.session_key,
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                _logger.error("Failed to retrieve secret: %s", result.stderr)
                return None

            retrieved_secrets = json.loads(result.stdout)
        except Exception as e:
            _logger.error("There was a problem retrieving secret: %s", e)
            raise e

        _logger.info("Secrets succesfully retrieved")
        return retrieved_secrets

    def _format_credentials(self, credentials: dict) -> dict:
        """
        Formats the credentials, so I can pass them to the utils.set_environment_variables

        Args:
            credentials (dict): A dictionary containing the unformatted credentials.

        Returns:
            dict: A dictionary containing the formatted credentials.
        """
        # en el dict viene login{user, pass}, notes y los custom.
        credential_types = [
            "api_key",
            "api_token",
            "api_username",
            "ssh_key",
            "bot_name",
            "bot_token",
            "app_key",
        ]
        formatted_credentials = {}

        _logger.info("Getting username and password")
        # get the basic credentials
        username = credentials.get("login", {}).get("username")
        if username is not None:
            formatted_credentials["username"] = username

        password = credentials.get("login", {}).get("password")
        if username is not None:
            formatted_credentials["password"] = password

        _logger.info("Getting custom field values")
        # checks for fields that could be potential credentials
        custom_fields = credentials["fields"]

        for field in custom_fields:
            field_name = field["name"]
            if field_name in credential_types:
                formatted_credentials[field_name] = field["value"]

        return formatted_credentials

    def get_secret(self, service_name: str, credential_name: str) -> str:
        """
        Retrieves a secret by name from the Bitwarden vault and sets environment variables for it.

        Calls `_set_environment_variables` to retrieve and set environment variables based
        on the secret fields defined in `service_mapping`.

        Args:
            service_name (str): The name of the secret to retrieve.
            credential_name (str): The concrete credential to retrieve.

        Returns:
            bool: True if the secret was successfully retrieved and environment variables were set,
                  False otherwise.
        """
        unformatted_credentials = self._retrieve_credentials(service_name)
        formatted_credentials = self._format_credentials(unformatted_credentials)
        credential = formatted_credentials[credential_name]
        return credential
