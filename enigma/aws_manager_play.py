from aws_manager import AwsManager


# Creates the object with the credentials in the .aws/credentials file
aws_manager = AwsManager()

print(aws_manager.get_secret("bugzilla", "username"))
print(aws_manager.get_secret("bugzilla", "password"))
