"""Presentation-wide document properties shared by imports and PPTX exports."""
import re

FIELDS = {"title":"title", "author":"author", "subject":"subject",
          "description":"comments", "keywords":"keywords", "category":"category",
          "language":"language"}


def validate_metadata(metadata):
    if not isinstance(metadata, dict):
        raise ValueError("Metadata must be an object.")
    result = dict(metadata)
    for name in FIELDS:
        if name not in result:
            continue
        value = result[name]
        if not isinstance(value, str) or len(value) > 255 or re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", value):
            raise ValueError(f"Metadata {name} must be text (max 255 characters, no control characters).")
    return result
