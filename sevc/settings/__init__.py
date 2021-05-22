import json
from json import JSONDecodeError
from typing import Dict, List, Optional

import sevc
from sevc.locations import Location
from sevc.tariffs import Tariff
from sevc.vehicles import Vehicle


class Settings:
    """Stores all locations, tariffs and vehicles"""

    __filename: str = ''

    assets: dict = {}

    def __init__(self, filename: str):
        self.__filename = filename

        parsed: dict = {}

        try:
            file = open(self.__filename, 'r')
            parsed = json.load(file)
            file.close()
        except IOError:
            self.save()
        except JSONDecodeError:
            self.save()

        if 'tariffs' in parsed:
            for uuid in parsed['tariffs']:
                self.assets[uuid] = sevc.object_from_dict(parsed['tariffs'][uuid], uuid)

        if 'locations' in parsed:
            for uuid in parsed['locations']:
                self.assets[uuid] = Location(parsed['locations'][uuid], uuid)

        if 'vehicles' in parsed:
            for uuid in parsed['vehicles']:
                self.assets[uuid] = sevc.object_from_dict(parsed['vehicles'][uuid], uuid)

    def __call__(self):
        """Update everything"""

        for uuid in self.assets:
            self.assets[uuid](self.assets)

    def __del__(self):
        """Save the settings on object deletion"""

        self.save()

    def delete_assets(self, asset_type: type, ids: List[int]) -> None:
        """Delete assets"""

        to_delete = list(self.uuid_dict(asset_type, ids).values())

        if asset_type == Tariff:
            for loc in self.assets:
                if not isinstance(self.assets[loc], Location):
                    continue

                if self.assets[loc].tariff in to_delete:
                    print('Cannot delete ' + str(self.assets[self.assets[loc].tariff])
                          + ' while it is being used in ' + str(self.assets[loc]))

                    to_delete.remove(self.assets[loc].tariff)

        for uuid in to_delete:
            print('Deleting ' + str(self.assets[uuid]))
            self.assets.pop(uuid)

    def dict(self) -> dict:
        """Output the object as a dictionary"""

        rtn = {
            'locations': {},
            'tariffs': {},
            'vehicles': {}
        }

        for uuid in self.assets:
            if isinstance(self.assets[uuid], Location):
                rtn['locations'][uuid] = self.assets[uuid].dict()
            elif isinstance(self.assets[uuid], Tariff):
                rtn['tariffs'][uuid] = self.assets[uuid].dict()
            elif isinstance(self.assets[uuid], Vehicle):
                rtn['vehicles'][uuid] = self.assets[uuid].dict()

        return rtn

    def print_list(self, asset_type: type, ids: Optional[List[int]] = None) -> None:
        """Display a list of assets"""

        uuids = self.uuid_dict(asset_type, ids)

        for i in uuids:
            print(str(i) + '. ' + str(self.assets[uuids[i]]))

    def save(self) -> None:
        """Save the settings to the file"""

        file = open(self.__filename, 'w')
        json.dump(self.dict(), file, separators=(',', ':'))
        file.close()

    def uuid_dict(self, asset_type: type, ids: Optional[List[int]] = None) -> Dict[int, str]:
        """Create a dictionary of asset UUIDs"""

        uuids: Dict[int, str] = {}
        i: int = 0

        for uuid in self.assets:
            if not isinstance(self.assets[uuid], asset_type):
                continue

            i += 1

            if ids is None or len(ids) == 0 or i in ids:
                uuids[i] = uuid

        return uuids
