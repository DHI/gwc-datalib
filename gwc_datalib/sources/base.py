from abc import ABC, abstractmethod


class BaseDataAdapter(ABC):
    def __init__(self, metadata):
        self.metadata = metadata

    @abstractmethod
    def to_pandas(self):
        pass

    @abstractmethod
    def to_xarray(self):
        pass
