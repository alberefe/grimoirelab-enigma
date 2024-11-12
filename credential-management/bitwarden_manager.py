import json
import subprocess
import os
from secrets_manager import SecretsManager


class BitwardenManager(SecretsManager):

    def __init__(self):
        """
        Loads credential types mapping from a JSON file to determine expected types of secrets
        for each service in Bitwarden.
        """
        # Session key of the bw session
        self.session_key = None

        # load the credential types mapping from the json file
        credentials_type_file_path = "./credential_items/credential_types.json"
        with open(credentials_type_file_path, "r") as file:
            self.service_mapping = json.load(file)

    def login(self, bw_email: str, bw_password: str) -> str:
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
            print("Session key not found")

    def _fetch_secrets(self, service_name):
        """
        Retrieves a secret from a particular service from the Bitwarden vault.

        Args:
            service_name (str): The name of the service for which to retrieve the secret.

        Returns:
            dict: The secret item retrieved from Bitwarden as a dictionary.

        Raises:
            Exception: If retrieval of the secret fails.
        """

        result = subprocess.run(
            ["/snap/bin/bw", "get", "item", service_name, "--session", self.session_key],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise Exception(f"Failed to retrieve secret '{service_name}' from Bitwarden: {result.stderr}")

        return json.loads(result.stdout)

    def _extract_field_value(self, secret, field):
        """
        Extracts the value for a specific field from the Bitwarden secret.

        Searches various sections of the secret, including 'login', 'fields', and 'notes',
        to find the value for the specified field.

        Args:
            secret (dict): The Bitwarden secret object.
            field (str): The field name to retrieve.

        Returns:
            str or None: The value of the specified field if found, otherwise None.
        """
        # Check for field in 'login' section (e.g., username, password)
        if "login" in secret and field in secret["login"]:
            print("Login:", secret["login"])
            return secret["login"].get(field)

        # Check custom fields under 'fields' section
        if "fields" in secret:
            for custom_field in secret["fields"]:
                if custom_field["name"].lower() == field.lower():
                    print("Custom Field:", custom_field)
                    return custom_field["value"]

        # Check if there is something in 'notes' and return it (e.g. ssh_key)
        if field == "notes" and "notes" in secret:
            print("Notes:", secret["notes"])
            return secret.get("notes")

        # Field not found in any section
        # print("Nothing found for field:", field)
        return None

    # TODO: do i need the expected fields or could I just get the secret and set the environment variables to
    #  the field names that are present?
    def _set_environment_variables(self, service_name):
        """
        Sets environment variables based on credentials stored in Bitwarden for a given service.

        Fetches the secret for the specified service and sets environment variables based
        on the retrieved fields, using the `service_mapping` configuration.

        Args:
            service_name (str): The name of the service to retrieve credentials for.

        Raises:
            ValueError: If no credential structure is found for the service in the configuration.
        """

        # Fetch the secret from Bitwarden
        secret = self._fetch_secrets(service_name)
        print("Fetched Secret:", secret)

        # Retrieve the expected fields for this service from the configuration mapping
        expected_fields = self.service_mapping.get(service_name)

        if not expected_fields:
            raise ValueError(f"No credential structure found for service '{service_name}' in service mapping.")

        # Iterate over each expected field and attempt to retrieve its value from the secret
        for field in expected_fields:
            env_var_name = f"{service_name.upper()}_{field.upper()}"
            value = self._extract_field_value(secret, field)

            # Set environment variable if the value was found
            if value:
                os.environ[env_var_name] = value
                print(f"Environment variable '{env_var_name}' set to value: '{value}'")
            else:
                print(f"Warning: Field '{field}' not found for service '{service_name}'")

    def get_secret(self, service_name: str):
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
            self._set_environment_variables(service_name)
            return True
        except Exception as e:
            print(f"Failed to retrieve secrets from service: '{service_name}' from Bitwarden: {e}")
            return False

    # TODO: I don't know even if I need this method.
    #   the user could just store the secrets from the interface of the secrets manager and then
    #   access them from perceval (for example)
    def store_secret(self, name: str, secret_type: str, username: str = None, password: str = None,
                     private_key: str = None):
        pass

    def logout(self):
        subprocess.run(["/snap/bin/bw", "logout"])
        self.session_key = None
