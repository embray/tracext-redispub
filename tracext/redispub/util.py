import datetime
import functools
import json


class JSONEncoder(json.JSONEncoder):
    REGISTERED_TYPES = {
        datetime.datetime: lambda o: o.isoformat(),
        datetime.date: lambda o: o.isoformat()
    }
    def default(self, obj):
        if type(obj) in self.REGISTERED_TYPES:
            return self.REGISTERED_TYPES[type(obj)](obj)

        return super(JSONEncoder, self).default(obj)


dumps = functools.partial(json.dumps, cls=JSONEncoder)
