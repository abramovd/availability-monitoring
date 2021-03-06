import datetime
import decimal
import json
import logging
import re
import uuid

from typing import Optional

from pydantic import BaseModel


logger = logging.getLogger(__name__)


# JSONEncoder and is_aware are partially taken from Django source code
def is_aware(value):
    """
    Determines if a given datetime.datetime is aware.

    The logic is described in Python's docs:
    http://docs.python.org/library/datetime.html#datetime.tzinfo
    """
    return value.tzinfo is not None and value.tzinfo.utcoffset(
        value) is not None


class JSONEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time,
    decimal types and UUIDs.
    """

    def default(self, o):
        # See "Date Time String Format" in the ECMA-262 specification.
        if isinstance(o, datetime.datetime):
            r = o.isoformat()
            if o.microsecond:
                r = r[:23] + r[26:]
            if r.endswith('+00:00'):
                r = r[:-6] + 'Z'
            return r
        elif isinstance(o, datetime.date):
            return o.isoformat()
        elif isinstance(o, datetime.time):
            if is_aware(o):
                raise ValueError("JSON can't represent timezone-aware times.")
            r = o.isoformat()
            if o.microsecond:
                r = r[:12]
            return r
        elif isinstance(o, decimal.Decimal):
            return str(o)
        elif isinstance(o, uuid.UUID):
            return str(o)
        elif isinstance(o, re.Pattern):
            return str(o)
        else:
            return super(JSONEncoder, self).default(o)


def pydantic_to_json_serializer(obj: BaseModel) -> bytes:
    return json.dumps(obj.dict(), cls=JSONEncoder).encode('utf-8')


def json_to_dict(obj: bytes) -> Optional[dict]:
    try:
        return json.loads(obj.decode('utf-8'))
    except json.decoder.JSONDecodeError:
        logger.exception('Unable to decode: %s', obj)
        return None
