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
from datetime import datetime, timedelta
from functools import lru_cache

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
        self.formatted_credentials = {}
        # store email for session validation
        self._email = email
        self.last_sync_time = None
        self.sync_interval = timedelta(minutes=5)

        try:
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
            # If we have a session key, check if sync is needed
            if self.session_key and self._validate_session():
                if self._should_sync():
                    self._sync_vault()
                return self.session_key

            _logger.info("Checking Bitwarden login status")
            status_result = subprocess.run(
                ["/snap/bin/bw", "status"], capture_output=True, text=True, check=False
            )

            if status_result.returncode == 0:
                _logger.info("Checking vault status")
                status = json.loads(status_result.stdout)

                if status.get("userEmail") == bw_email:
                    _logger.info("User was already authenticated: %s", bw_email)

                    if status.get("status") == "unlocked":
                        _logger.info("Vault unlocked, getting session key")
                        self.session_key = status.get("sessionKey")

                    elif status.get("status") == "locked":
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

                        self.session_key = unlock_result.stdout.strip()

                    if not self.session_key:
                        _logger.info("Couldn't obtain session key during login")
                        return ""

                else:
                    _logger.info("Login in: %s", bw_email)
                    result = subprocess.run(
                        ["/snap/bin/bw", "login", bw_email, bw_password, "--raw"],
                        capture_output=True,
                        text=True,
                        check=False,
                    )

                    if result.returncode != 0:
                        _logger.error("Error logging in: %s ", result.stderr)
                        return ""

                    _logger.info("Setting session key")
                    self.session_key = result.stdout.strip()

            if self.session_key:
                # Only sync if needed based on time interval
                if self._should_sync():
                    _logger.info("Syncing local vault with Bitwarden")
                    subprocess.run(
                        ["/snap/bin/bw", "sync", "--session", self.session_key],
                        check=True,
                    )
                    self.last_sync_time = datetime.now()
                return self.session_key

            _logger.info("Session key not found cause could not log in")
            return ""

        except Exception as e:
            _logger.error("There was a problem login in: %s", e)
            raise e

    def _validate_session(self) -> bool:
        """Validates if the current session is still valid."""
        try:
            status_result = subprocess.run(
                ["/snap/bin/bw", "status"], capture_output=True, text=True, check=False
            )

            if status_result.returncode != 0:
                return False

            status = json.loads(status_result.stdout)
            return (
                status.get("status") == "unlocked"
                and status.get("userEmail") == self._email
                and status.get("sessionKey") == self.session_key
            )
        except:
            return False

    def _should_sync(self) -> bool:
        """Determines if vault sync is needed based on last sync time."""
        return (
            not self.last_sync_time
            or datetime.now() - self.last_sync_time > self.sync_interval
        )

    def _sync_vault(self) -> None:
        """Syncs the vault and updates last sync time."""
        try:
            _logger.info("Syncing vault")
            subprocess.run(
                ["/snap/bin/bw", "sync", "--session", self.session_key], check=True
            )
            self.last_sync_time = datetime.now()
        except subprocess.CalledProcessError as e:
            _logger.error("Sync failed: %s", e)

    @lru_cache(maxsize=32)
    def _retrieve_credentials(self, service_name: str) -> dict:
        """
        Retrieves a secret from a particular service from the Bitwarden vault.
        This function is cached using LRU cache with a maximum size of 32 entries.

        Args:
            service_name (str): The name of the service for which to retrieve the secret.

        Returns:
            dict: The secret item retrieved from Bitwarden as a dictionary.

        Raises:
            Exception: If retrieval of the secret fails.
        """
        try:
            _logger.info("Retrieving credential from Bitwarden CLI: %s", service_name)
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
                return {}

            retrieved_secrets = json.loads(result.stdout)
            _logger.info("Secrets successfully retrieved and cached")
            return retrieved_secrets

        except Exception as e:
            _logger.error("There was a problem retrieving secret: %s", e)
            raise e

    def _format_credentials(self, credentials: dict) -> dict:
        """
        Formats the credentials retrieved from Bitwarden into a standardized format.

        Args:
            credentials (dict): Raw credentials from Bitwarden

        Returns:
            dict: Formatted credentials with standardized keys
        """
        formatted = {"service_name": credentials["name"].lower()}

        # Get username and password from login section
        login = credentials.get("login", {})
        if login.get("username"):
            formatted["username"] = login["username"]
        if login.get("password"):
            formatted["password"] = login["password"]

        # Get custom fields
        for field in credentials.get("fields", []):
            formatted[field["name"]] = field["value"]

        return formatted

    def get_secret(self, service_name: str, credential_name: str) -> str:
        """
        Retrieves a secret by name from the Bitwarden vault and sets environment variables for it.

        Calls `_set_environment_variables` to retrieve and set environment variables based
        on the secret fields defined in `service_mapping`.

        Args:
            service_name (str): The name of the secret to retrieve.
            credential_name (str): The concrete credential to retrieve.

        Returns:
            str: The secret value retrieved.
        """
        # If stored credentials are not available or belong to a different service
        if (
            not self.formatted_credentials
            or self.formatted_credentials.get("service_name") != service_name
        ):
            unformatted_credentials = self._retrieve_credentials(service_name)
            self.formatted_credentials = self._format_credentials(
                unformatted_credentials
            )

        secret = self.formatted_credentials.get(credential_name)
        # in case nothing was found
        if not secret:
            _logger.error(
                "The credential %s:%s, was not found.", service_name, credential_name
            )
            _logger.error("In the meantime here you got an empty string")
            return ""
        else:
            # Return the requested credential
            return secret

    def clear_cache(self):
        """Clears the LRU cache."""
        self._retrieve_credentials.cache_clear()
