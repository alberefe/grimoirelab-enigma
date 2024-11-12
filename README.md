Current dependencies: 

- dotenv
- json
- os

(in the future I'm planning to manage all dependencies with poetry, like the rest of grimoirelab)


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
    in order to access the service. 

    