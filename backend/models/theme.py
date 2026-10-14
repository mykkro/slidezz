from dataclasses import dataclass


@dataclass
class Theme:
    font_name: str = "Aptos"
    primary_color: str = "#0055AA"
    background_color: str = "#FFFFFF"

    title_size: int = 30
    subtitle_size: int = 18