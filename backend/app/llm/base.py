from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str, *, context: str, query: str) -> str:
        raise NotImplementedError
