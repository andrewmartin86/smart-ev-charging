import importlib
import inspect
import os
import pkgutil
import re
from typing import Dict, List, Optional


def delete_assets(array: Dict, ids: List[int]) -> None:
    """Delete assets from the dictionary"""

    i: int = 0
    to_delete: List[str] = []
    for uuid in array:
        i += 1
        if i in ids and array[uuid].delete_allowed():
            print('Deleting ' + array[uuid].name)
            to_delete.append(uuid)

    for uuid in to_delete:
        array.pop(uuid)


def friendly_class_name(cls: type):
    """Make the given class name more readable"""

    parent = cls.__base__.__name__
    p = -len(parent)

    name = cls.__name__

    if name[p:] == parent:
        name = name[:p]  # remove the parent from the name

    return re.sub(r'(?<!^)(?=[A-Z])', ' ', name)  # change camel case into words


def instantiate_subclass(parent: type):
    """Choose and instantiate a subclass"""

    print()
    classes: Dict = {}
    names: Dict[int, str] = {}
    i: int = 0

    for importer, modname, ispkg in pkgutil.iter_modules([os.path.dirname(inspect.getfile(parent))]):
        module = importer.find_spec(modname).loader.load_module(modname)
        members = inspect.getmembers(module, lambda member: is_subclass_of(member, parent))

        for name, obj in members:
            i += 1
            names[i] = friendly_class_name(obj)
            classes[i] = [module, name]

    if len(classes) == 1:
        class_def = classes[1]
        print('Automatically selected ' + names[1])
    else:
        print()
        for i in names:
            print(str(i) + ': ' + names[i])

        class_def = classes[int(input('Please choose a ' + parent.__name__.lower() + ' type: '))]

    subclass = getattr(*class_def)
    return subclass()


def is_subclass_of(cls, parent: type) -> bool:
    """Is cls a subclass of the given parent?"""

    return inspect.isclass(cls) and issubclass(cls, parent) and cls != parent


def name_object(cls: type, default_name: Optional[str] = None) -> str:
    """Get a name for an object"""

    if cls.__base__ == object:
        parent_name = cls.__name__.lower()
    else:
        parent_name = cls.__base__.__name__.lower()

    if default_name is None:
        default_name = friendly_class_name(cls)

    print()
    name = input('Please enter a name for this ' + parent_name + ' (default = ' + default_name + '): ')

    if name != '':
        return name

    return default_name


def object_from_dict(array: dict, uuid: Optional[str] = None):
    """Create an object of the correct class from a dictionary"""

    cls = getattr(importlib.import_module(array['module']), array['class'])
    return cls(array, uuid=uuid)


def print_list(array: Dict, ids: Optional[List[int]] = None) -> None:
    """Display a list"""

    i: int = 0

    for uuid in array:
        i += 1
        if ids is None or len(ids) == 0 or i in ids:
            print(str(i) + '. ' + array[uuid].name)


def uuid_dict(array: Dict) -> Dict[int, str]:
    """Create a dictionary of UUIDs"""

    uuids: Dict[int, str] = {}
    i: int = 0

    for uuid in array:
        i += 1
        uuids[i] = uuid

    return uuids
