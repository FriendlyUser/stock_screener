from abc import ABC, abstractmethod


class ScannerInterface(ABC):
    """Each scanner has an interface and get_match for the ticker"""

    @abstractmethod
    def main_func(self):
        pass

    @abstractmethod
    def get_match(self, ticker):
        pass