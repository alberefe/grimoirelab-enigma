from abc import ABC, abstractmethod

class SecretsManager(ABC):

    #TODO: unify the signatures of all children and this class
    @abstractmethod
    def login(self, username: str, password: str) -> str:
        """Log into the secrets manager and establish a session if needed."""
        pass

    @abstractmethod
    def get_secret(self, service_name:str) -> bool:
        """Set environment variables for the secrets of the service."""
        pass

    @abstractmethod
    def store_secret(self, key: str, value: str):
        """Store a secret by key."""
        pass

    @abstractmethod
    def logout(self):
        """Log out and clean up the session."""
        pass
