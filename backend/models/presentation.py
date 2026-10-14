from dataclasses import dataclass, field


@dataclass
class Presentation:
    slides: list = field(default_factory=list)