from abc import ABC, abstractmethod

class SecretsManager(ABC):


    @abstractmethod
    def get_secret(self, service_name:str) -> bool:
        """Set environment variables for the secrets of the service."""
        pass