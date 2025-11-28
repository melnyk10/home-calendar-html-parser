from dataclasses import dataclass
from typing import Optional


@dataclass
class HltvStream:
  name: str
  url: str
  language: Optional[str]
  viewers: Optional[int]
