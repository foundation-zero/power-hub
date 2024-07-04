from datetime import datetime
import json
from typing import Any
from uuid import UUID


def encoder(blacklist: set[str] = set()) -> type[json.JSONEncoder]:

    class NestedEncoder(json.JSONEncoder):

        def default(self, o: Any):
            if type(o) == datetime:
                return o.isoformat()
            if hasattr(o, "__dict__"):
                return {
                    attr: value
                    for attr, value in o.__dict__.items()
                    if attr not in blacklist
                }
            if type(o) == UUID:
                return o.hex
            else:
                return json.JSONEncoder.default(self, o)

    return NestedEncoder
