import os
import json
from dotenv import load_dotenv
from hc_manager import HashicorpManager


# Load the vault configuration
with open("../config_files/hashicorp_vault_config.json", "r") as file:
    vault_config = json.load(file)

# Get the vault url
vault_url = vault_config["vault_url"]
print(vault_url)

# Load the environment variables
load_dotenv()

# Assign useful variables
certificate = os.getenv("VAULT_CACERT")
token = os.getenv("VAULT_TOKEN")
vault_unseal_key = vault_config["vault_unseal_key"]

# Instantiate the class
hashicorp_manager = HashicorpManager(vault_url, token, certificate)

# Get the secret (it assigns it to env var)
hashicorp_manager.get_secret("bugzilla")
print("Variable de entorno asignada: " + os.getenv("BUGZILLA_USERNAME"))

