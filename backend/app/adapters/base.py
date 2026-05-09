from abc import ABC, abstractmethod

class ModelAdapter(ABC):
    @abstractmethod
    def send_message(self, messages: list, config: dict) -> str:
        pass

    @abstractmethod
    def stream_message(self, messages: list, config: dict):
        pass