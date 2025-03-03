# Grimoirelab Enigma


This is a module made to retrieve credentials from different secrets management systems like Bitwarden. 

It accesses the secrets management service, looks for the desired credential and returns it in String form. 

## Requirements

- Python >= 3.9
- Poetry >= 1.8.4
- hvac >= 2.3.0
- boto3 >= 1.35.63

All the dependencies are listed in the pyproject.toml file.

## Installation


### Getting the source code

To install you will need to clone the repository:

```
$ git clone https://github.com/alberefe/grimoirelab-enigma.git 
$ cd grimoirelab-enigma
```

### Installing

[Poetry]( https://python-poetry.org/) is used for managing the project. You can install it following [these steps](https://python-poetry.org/docs/#installing-with-pipx).

Install the required dependencies (this will also create a virtual environment).

```
$ poetry install
```

Activate the virtual environment. 

```
$ poetry shell
```


## Usage


There are two ways to use this module

- In the terminal as a standalone application
- As a python module that can be called by other python code. 

### Terminal 

To use this, any of these two is valid:

Command-Line Interface:

```
$ python -m enigma <manager> <service> <credential>
```

Or if installed as executable:

```
$ enigma <manager> <service> <credential>
```

Where:

- manager → credential manager used to store the credentials (Bitwarden, aws, Hashicorp Vault)
- service → the platform to which you want to connect (github, gitlab, bugzilla)
- credential → the credential that you want to retrieve (username, password, api-token)

Examples:

```
$ python -m enigma bitwarden bugzilla username
$ python -m enigma hashicorp gitlab password
$ python -m enigma aws github api-token
```

In each case, the script will log / access into the corresponding vault, search for the secret with the name of the service that wants to be accessed and then retrieve, from that secret, the value with the name inserted as credential. 

That is, in the first case, it will log into Bitwarden, access the secret called "bugzilla", and from it retrieve the value of the field "username". 

Each of the secrets management services are accessed in different forms and need different configurations to work, as specified in the [[#Managers]] section.

### Python API

To use the module in your python code, import the module


```
from enigma import get_secret

# Retrieve a secret from Bitwarden
username = get_secret("bitwarden", "bugzilla", "username")

# Retrieve a secret from AWS Secrets Manager
api_token = get_secret("aws", "github", "api-token")

# Retrieve a secret from HashiCorp Vault
password = get_secret("hashicorp", "gitlab", "password")
```

For more advaced usage, you can directly use the factory to get a specific manager:

```
from enigma import SecretsManagerFactory

# Get a Bitwarden manager instance
bw_manager = SecretsManagerFactory.get_bitwarden_manager()
username = bw_manager.get_secret("bugzilla", "username")

# Get an AWS Secrets Manager instance
aws_manager = SecretsManagerFactory.get_aws_manager()
api_token = aws_manager.get_secret("github", "api-token")

```

## Supported Managers


This section explains the different things to consider when using each of the supported secrets management services, like where to store the credentials to access the secrets manager.

### AWS

The module uses [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html), and this looks for your credentials in the .aws folder, in the files "credentials" and "config".  

Configuration:

- Credentials are read from the standard AWS credentials file (~/.aws/credentials)
- Region configuration is read from ~/.aws/config
- Ensure your IAM user/role has appropriate permissions to access Secrets Manager

More about this [here](https://docs.aws.amazon.com/sdkref/latest/guide/file-location.html). 

### Hashicorp Vault

The module uses [hvac](https://hvac.readthedocs.io/en/stable/overview.html) to interact with Hashicorp Vault.

The function will look for the following environment variables to get into the vault, and prompt the user for them if not found:

- VAULT_ADDR  → Address of the Vault server.
- VAULT_TOKEN → A Vault-issued service token that authenticates the CLI user to Vault.
- VAULT_CACERT → Path to a PEM-encoded CA certificate file on the local disk. Used to verify SSL certificates for the server

If environment variables are not found, the user will be prompted to introduce the data manually.

More info on this can be found [here](https://developer.hashicorp.com/vault/docs/commands).

### Bitwarden

The module uses the [Bitwarden CLI](https://bitwarden.com/help/cli/) to interact with Bitwarden.

Required environment variables:

- BW_EMAIL → the email used to log into the bitwarden account
- BW_PASSWORD

If environment variables are not found, the user will be prompted to introduce the data manually.

## Contributing
Contributions are welcome! Please see our CONTRIBUTING.md file for details on how to contribute to the project, including how to add support for additional secret managers.
