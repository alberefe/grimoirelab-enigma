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
from bw_manager import BitwardenManager
from aws_manager import AwsManager
from hc_manager import HashicorpManager


def get_secret(secrets_manager, service_name, credential_name) -> str:
    """
    Function that initializes the corresponding manager and returns the credential
    """
    if secrets_manager == "bitwarden":
        secrets_manager = BitwardenManager()
        return secrets_manager.get_secret(service_name, credential_name)
    elif secrets_manager == "hashicorp":
        secrets_manager = HashicorpManager()
        return secrets_manager.get_secret(service_name, credential_name)
    elif secrets_manager == "aws":
        secrets_manager = AwsManager()
        return secrets_manager.get_secret(service_name, credential_name)
