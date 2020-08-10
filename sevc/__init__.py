import inspect


def is_subclass_of(cls, parent: type) -> bool:
    return inspect.isclass(cls) and issubclass(cls, parent) and not cls == parent
