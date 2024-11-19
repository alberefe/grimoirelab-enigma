import json
from aws_manager import AwsManager

with open("../config_files/aws_config.json") as config_file:
    aws_config = json.load(config_file)

# Assign the credentials from the json config file
aws_username = aws_config["aws_access_key_id"]
aws_password = aws_config["aws_secret_access_key"]

# Creates the object with the credentials
aws_manager = AwsManager(
    aws_access_key_id=aws_username, aws_secret_access_key=aws_password
)

print(aws_manager.get_secret("bugzilla", "username"))
print(aws_manager.get_secret("bugzilla", "password"))
