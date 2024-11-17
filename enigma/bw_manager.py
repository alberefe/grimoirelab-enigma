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
import utils
from enigma import Enigma


class BitwardenManager(Enigma):

    def __init__(self, email: str, password: str):
        """
        Loads credential types mapping from a JSON file to determine expected types of secrets
        for each service in Bitwarden.
        """
        # Session key of the bw session
        self.session_key = None

        try:
            # load the credential types mapping from the json file and logs in
            credentials_type_file_path = "../config_files/credential_types.json"
            with open(credentials_type_file_path, "r", encoding="utf-8") as file:
                self.service_mapping = json.load(file)

            self._login(email, password)
        except FileNotFoundError:
            print("File not found")
            raise FileNotFoundError
        except Exception as e:
            print(e)

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
            # Check Bitwarden login status
            status_result = subprocess.run(
                ["/snap/bin/bw", "status"],
                capture_output=True,
                text=True
            )

            # if the status command was successful
            if status_result.returncode == 0:
                # Parse the JSON output from `bw status`
                status = json.loads(status_result.stdout)

                if status.get("userEmail") == bw_email:
                    # If the vault is locked, unlock it
                    if status.get("status") == "locked":
                        unlock_result = subprocess.run(
                            ["/snap/bin/bw", "unlock", bw_password, "--raw"],
                            capture_output=True,
                            text=True
                        )

                        if unlock_result.returncode != 0:
                            raise Exception("Failed to unlock Bitwarden: " + unlock_result.stderr)

                        # Set the session key
                        self.session_key = unlock_result.stdout.strip()

                    elif status.get("status") == "unlocked":
                        # If already unlocked, retrieve the current session key
                        self.session_key = status.get("sessionKey")

                    # Ensure session key is set
                    if not self.session_key:
                        raise Exception("Failed to obtain session key during login")

                else:
                    # Login to Bitwarden if not already logged in
                    result = subprocess.run(
                        ["/snap/bin/bw", "login", bw_email, bw_password, "--raw"],
                        capture_output=True,
                        text=True
                    )

                    # Check if the login was successful
                    if result.returncode != 0:
                        raise Exception("Failed to log into Bitwarden: " + result.stderr)

                    # Set session key
                    self.session_key = result.stdout.strip()

            # Sync the vault
            if self.session_key:
                subprocess.run(["/snap/bin/bw", "sync", "--session", self.session_key], check=True)
                return self.session_key
            else:
                print("Session key not found cause could not log in")
        except Exception as e:
            print("There was a problem login in:" + e)

    def _retrieve_credentials(self, service_name):
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
            result = subprocess.run(
                ["/snap/bin/bw", "get", "item", service_name, "--session", self.session_key],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise Exception(f"Failed to retrieve secret '{service_name}' from Bitwarden: {result.stderr}")

            retrieved_secrets = json.loads(result.stdout)
        except Exception as e:
            print("There was an error retrieving the secret: " + e)

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
        credential_types = ["api_key", "api_token", "api_username", "ssh_key", "bot_name", "bot_token", "app_key"]
        formatted_credentials = {}
        try:
            # get the basic credentials
            username = credentials.get("login", {}).get("username")
            if username is not None:
                formatted_credentials["username"] = username

            password = credentials.get("login", {}).get("password")
            if username is not None:
                formatted_credentials["password"] = password

            # checks for fields that could be potential credentials
            for field in credentials:
                if field in credential_types:
                    formatted_credentials[field] = credentials[field]
        except Exception as e:
            print("There was an error formatting credentials: " + e)

        return formatted_credentials

    def get_secret(self, service_name: str) -> bool:
        """
        Retrieves a secret by name from the Bitwarden vault and sets environment variables for it.

        Calls `_set_environment_variables` to retrieve and set environment variables based
        on the secret fields defined in `service_mapping`.

        Args:
            service_name (str): The name of the secret to retrieve.

        Returns:
            bool: True if the secret was successfully retrieved and environment variables were set,
                  False otherwise.
        """
        try:
            unformatted_credentials = self._retrieve_credentials(service_name)
            formatted_credentials = self._format_credentials(unformatted_credentials)
            utils.set_environment_variables(service_name, formatted_credentials)
            return True
        except Exception as e:
            print(f"Failed to retrieve secrets from service: '{service_name}' from Bitwarden: {e}")
            return False
