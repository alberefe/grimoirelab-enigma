Current dependencies: 

- dotenv
- json
- os
- hvac

(in the future I'm planning to manage all dependencies with poetry, like the rest of grimoirelab)

# bw_manager.py

Instructions to test the class bitwarden_manager.py

1. Create .env file and add the credentials used to access your vault. (or the vault where the credentials are stored)

   - BW_EMAIL=your_bitwarden_accout_email_here
   - BW_PASSWORD=your_bitwarden_password_here

    bw_manager_tester will use these credentials in order to login into the account. 

2. Store a secret (or more) in your bitwarden vault. It has to follow the format:
   
   - Name of the secret must be the service to access in lowcase, for example "github", "bugzilla".
   - For fields other than username:password, create a new field inside the secret and name it according to the structure
      provided in credential_types.json. The program will look for fields named after the file and assign their names
      according to the type of credential + service that's being accessed. 
   
      That is, if I want to store and access a github api token, I'd create a secret called "github", then inside this
      secret, a field called "api_token" in which storing said token.

3. Inside bw_manager_tester, uncomment the corresponding line according to the secret we want to retrieve. So if you
    stored github secret, then uncomment the line: 
    
    bw_manager.get_secret("github")

4. The credentials are stored in environment variables printed in the terminal, and we could then use them in a script 
    in order to access the service. That is, the get_secret() function assigns each credential found for that service
    an environment variable, based on the service + type of credential. 

    For example:  if I recover a bugzilla username and bugzilla password, the env vars will be called respectively:
        - BUGZILLA_USERNAME
        - BUGZILLA_PASSWORD

    Other examples would be: 
        - GITHUB_API_TOKEN
        - GERRIT_SSH_KEY

    With this naming I'm trying to make it easy for Perceval or other parts of Grimoirelab to use the correct credential.

    
# hc_manager.py


1. Install hashicorp vault in the system. The instructions are found here depending on your OS:
   
    https://developer.hashicorp.com/vault/tutorials/getting-started/getting-started-install

2. Start the server. 

    ```
    $ vault server -dev-tls
    ```

    The terminal will show some data that we should store in the next steps:

3. Save the following data in *../config_files/hashicorp_vault_config.json*
    
   - vault_url
   - vault_unseal_key

4. Set the following env vars in *.env* file

   - VAULT_ADDR
   - VAULT_TOKEN
   - VAULT_CACERT

    The vault token in the dev environment is the root_token, but in production it could be any token that 
    allows the user to unseal the vault and retrieve secrets from it. 

    In development mode the vault starts unsealed and stays like that. 

5. Set environment variables in our system to store our testing credentials

    ```
    $ export VAULT_ADDR=....
    $ export VAULT_CACERT=....
    ```
6. Store a username:password pair for bugzilla service.

    ```
    $ vault kv put secret/bugzilla username=bugzilla_user password=bugzilla_password
    ```
    
    This stores in the path "secret/bugzilla" the two elements, username and password. We can do this with any other
    type of credential. I'll be using the same naming convention for the elements stored. 

    We can check that the secret has been stored with
   
    ```
    $ vault kv get /secret/bugzilla/
    ```
   
7. Run hc_manager_tester.py


# aws_manager.py

1. You need an aws account, and a user that can access the secrets manager. So first steps:

   - Store secrets using the format:
     - Name of the secret must be the name of the service (i.e. bugzilla)
     - Inside, name the fields as the type of credential (i.e. api_key)

2. In security credentials, assign an access key to the user that's going to access the vault. This key, for now will
    go to the aws_config.json file that should be stored in ../config_files/
