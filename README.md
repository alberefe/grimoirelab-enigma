# Grimoirelab Enigma
---

This is a module made to retrieve credentials from different secrets management systems like Bitwarden.

It accesses the secrets management service, looks for the desired credential and returns it in String form. 

## Requirements

- Python >= 3.9
- Poetry >= 1.8.4
- hvac >= 2.3.0
- boto3 >= 1.35.63

All the dependencies are listed in the pyproject.toml file.

## Installation
---

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
---

There are two ways to use this module

- In the terminal
- As a python module that can be called by other python code. 

### Terminal 

To use this, any of these two is valid:

```
$ python3 enigma.py <manager> <service> <credential>
$ ./enigma.py <manager> <service> <credential>
```

Where:

- manager → credential manager used to store the credentials (Bitwarden, aws, Hashicorp Vault)
- service → the platform to which you want to connect (github, gitlab, bugzilla)
- credential → the credential that you want to retrieve (username, password, api-token)

Examples:

```
$ python3 enigma.py bitwarden bugzilla username
$ python3 enigma.py hashicorp bugzilla password
$ python3 enigma.py aws github api-token
```

In each case, the script will log / access into the corresponding vault, search for the secret with the name of the service that wants to be accessed and then retrieve, from that secret, the value with the name inserted as credential. 

That is, in the first case, it will log into Bitwarden, access the secret called "bugzilla", and from it retrieve the value of the field "username". 

Each of the secrets management services are accessed in different forms and need different configurations to work, as specified in the [[#Managers]] section.

### In python code

To use the module in your python code, import the module

```
from enigma import enigma
```

Then, you can call 

```
enigma.get_secret(secrets_manager, service_name, credential_name)
```

And the function will return the desired credential in **String** form. 

## Managers
---

This section explains the different things to consider when using each of the supported secrets management services, like where to store the credentials to access the secrets manager.

### AWS

The module uses [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html), and this looks for your credentials in the .aws folder, in the files "credentials" and "config".  

The credentials file contains your credentials for accessing your aws account, that is your *aws_access_key_id* and *aws_secret_access_key*. 

The config file contains the region in which the script will work, that should be the one of your aws account. 

This two pieces of information are necessary for the script to access your account.

More about this [here](https://docs.aws.amazon.com/sdkref/latest/guide/file-location.html). 

### Hashicorp Vault

In this case, [hvac](https://hvac.readthedocs.io/en/stable/overview.html) is used. 

The function will look for the following environment variables to get into the vault, and prompt the user for them if not found:

- VAULT_ADDR  → Address of the Vault server.
- VAULT_TOKEN → A Vault-issued service token that authenticates the CLI user to Vault.
- VAULT_CACERT → Path to a PEM-encoded CA certificate file on the local disk. Used to verify SSL certificates for the server

More info on this can be found [here](https://developer.hashicorp.com/vault/docs/commands).

### Bitwarden

In this case, [Bitwarden CLI](https://bitwarden.com/help/cli/) is used. 

To log in, the function will look for the following environment variables to log into the vault, and prompt the user for them if not found:

- BW_EMAIL → the email used to log into the bitwarden account
- BW_PASSWORD