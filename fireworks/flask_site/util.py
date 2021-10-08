import datetime
import json

from bson.objectid import ObjectId
from flask.globals import current_app
from flask.json import dumps


class MongoJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        elif isinstance(obj, ObjectId):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


def jsonify(*args, **kwargs):
    """flask.json.jsonify with cls=MongoJsonEncoder passed to flask.json.dumps

    Body copied from flask==1.0.2 (latest);
    """
    indent = None
    separators = (",", ":")

    if current_app.config["JSONIFY_PRETTYPRINT_REGULAR"] or current_app.debug:
        indent = 2
        separators = (", ", ": ")

    if args and kwargs:
        raise TypeError("jsonify() behavior undefined when passed both args and kwargs")
    elif len(args) == 1:  # single args are passed directly to dumps()
        data = args[0]
    else:
        data = args or kwargs

    return current_app.response_class(
        dumps(data, indent=indent, separators=separators, cls=MongoJsonEncoder) + "\n",
        mimetype=current_app.config["JSONIFY_MIMETYPE"],
    )
