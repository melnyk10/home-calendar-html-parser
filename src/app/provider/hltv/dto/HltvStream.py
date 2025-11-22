from dataclasses import dataclass
from typing import Optional


@dataclass
class HltvStream:
  name: str
  url: str
  flag_title: Optional[str]
  viewers: Optional[int]
