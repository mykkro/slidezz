from backend.templates.title import TitleTemplate


_registry = {
    "title": TitleTemplate(),
}


def get_template(name):
    return _registry[name]