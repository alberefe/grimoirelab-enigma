"""
File that executes the bw manager things for developing purposes and testing the BitwardenManager class.

I'm using a json file to store the credentials, so I can access them from the script without having to set them every
time
"""

import os
from dotenv import load_dotenv
from bw_manager import BitwardenManager

# Load environment variables from the .env file
load_dotenv()

# Access Bitwarden credentials from environment variables
bw_email = os.getenv("BW_EMAIL")
bw_password = os.getenv("BW_PASSWORD")

# Ensure the environment variables are set
if not bw_email or not bw_password:
    raise ValueError(
        "Please set the BW_EMAIL and BW_PASSWORD environment variables in the .env file"
    )

# Create a BitwardenManager object using the secrets manager interface
bw_manager = BitwardenManager(bw_email, bw_password)

"""
Uncomment the service that wants to be tested.
"""
# Fetch and use Bugzilla login credentials
# print(bw_manager.get_secret("bugzilla", "username"))

# Fetch and use GitHub token
print(bw_manager.get_secret("github", "username"))
print(bw_manager.get_secret("github", "password"))
print(bw_manager.get_secret("github", "api_key"))

# Fetch and use SSH private key
print(bw_manager.get_secret("gerrit", "ssh_key"))

# Fetch and use StackExchange credentials
print(bw_manager.get_secret("stackexchange", "api_token"))


# print("\nBUGZILLA USERNAME = " + os.getenv("BUGZILLA_USERNAME"))
# print("BUGZILLA PASSWORD = " + os.getenv("BUGZILLA_PASSWORD"))
