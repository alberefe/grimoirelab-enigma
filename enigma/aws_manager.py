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

from enigma import Enigma
import json
from botocore.exceptions import EndpointConnectionError
from botocore.exceptions import SSLError
from botocore.exceptions import ClientError
from utils import set_environment_variables
import boto3


class AwsManager(Enigma):
    # TODO: the region should be in the .aws config file that the user should have. This makes everything easier to
    #   deal with. Next step make it work with that configuration?
    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None, aws_session_token=None):
        """
        Initializes the client that will access to the credentials management service.

        Args:
            aws_access_key_id (str, optional): AWS access key id. Defaults to None.
            aws_secret_access_key (str, optional): AWS secret access key that corresponds to the key_id. Defaults to None.
            aws_session_token (str, optional): AWS session token. Defaults to None.
        """

        # Creates a client using the credentials
        try:
            self.client = boto3.client('secretsmanager', aws_access_key_id=aws_access_key_id,
                                       aws_secret_access_key=aws_secret_access_key,
                                       aws_session_token=aws_session_token,
                                       region_name='eu-west-3')
        except EndpointConnectionError as e:
            print("e connecting to the endpoing: " + e)
        except SSLError as e:
            print("e with the SSL connection: " + e)
        except ClientError as e:
            print("Client e:" + e)
        except Exception as e:
            print(e)

    def _retrieve_and_format_credentials(self, service_name: str) -> dict:
        """
        Retrieves credentials using the client initialized

        Args:
            service_name (str): Name of the service to retrieve credentials for.(or name of the secret)
        Returns:
            formatted_credentials (dict): Dictionary containing the credentials retrieved and formatted as a dict
        """
        try:
            secret_value_response = self.client.get_secret_value(
                SecretId=service_name
            )
            formatted_credentials = json.loads(secret_value_response['SecretString'])
            return formatted_credentials
        except ClientError as e:
            print("There was a problem accessing the secret:" + e)
        except self.client.exceptions.ResourceNotFoundException as e:
            print("Resource not found: " + e)
        except self.client.exceptions.InternalServiceError as e:
            print("Internal server e: " + e)
        except Exception as e:
            print(e)

    def get_secret(self, service_name: str) -> bool:
        """
        Gets a secret based on the service name

        Args:
            service_name (str): Name of the service to retrieve credentials for.(or name of the secret)
        Returns:
            bool: True if something was retrieved, False otherwise
        """
        try:
            credentials = self._retrieve_and_format_credentials(service_name)
            # TODO: this should return the secret.
            set_environment_variables(service_name, credentials)
            return True
        # this catches only generic exceptions because they are raised lower
        except Exception as e:
            print("Failed to retrieve the secrets. ")
            print(e)
            return False
