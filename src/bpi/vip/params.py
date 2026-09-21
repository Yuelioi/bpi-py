from bpi._core.params import integer
from bpi.errors import InvalidParameterError


def center_info_query(build: int) -> dict[str, str]:
    return {"build": integer(build, "build", minimum=0)}


def privilege_type(value: int) -> str:
    result = integer(value, "privilege_type")
    if value > 255:
        raise InvalidParameterError("privilege_type must fit in an unsigned byte")
    return result
