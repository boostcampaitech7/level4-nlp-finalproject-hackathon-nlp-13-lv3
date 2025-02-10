import orjson

def orjson_dumps(data, *, default):
    return orjson.dumps(data, default=default).decode()
