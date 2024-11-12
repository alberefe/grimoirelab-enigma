"""
My intention with this file is to have here all the functions that may be common to the credential management
"""
import os


# TODO: maybe do try except to check for possible exceptions
def set_environment_variables(service_name: str, credentials: dict) -> bool:
    """
    From a dict containing the credentials retrieved, I then parse all the elements and assign their values to env var

    Args:
        service_name (str): The name of the service
        credentials (dict): A dict containing the credentials retrieved from the service. TypeCredential:valueCredential
    """
    var_set = False
    for key, value in credentials.items():
        env_var_name = f"{service_name.upper()}_{key.upper()}"
        env_var_value = value

        # Set environment value
        if value:
            # If there's at least one variable set, it will return true
            var_set = True
            os.environ[env_var_name] = env_var_value
            print(f"Environment variable '{env_var_name.upper()}' set to value: '{value}'")

        else:
            print(f"Warning: Field '{env_var_name.upper()}' not found for service '{service_name}'")

    return var_set
