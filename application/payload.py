from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List
import struct


class PayloadParser(ABC):
    @abstractmethod
    def get_expected_length(self) -> int:
        """Return expected payload length in bytes"""
        pass

    @abstractmethod
    def parse(self, payload: bytes) -> Any:
        """Parse payload bytes into a data object"""
        pass
