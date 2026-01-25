from collections import namedtuple
from collections.abc import Sequence
from typing import Any

from src.constants import SORT_BY, SORT_DIRECTION

sort_description = f"{SORT_DIRECTION} is used only with {SORT_BY} query param, `asc` - ascending, `desc` - descending"


def build_validation_error_detail(errors: Sequence[Any]) -> str:
    Details = namedtuple("Details", ["loc", "msg"])
    errors_details = [Details(loc=e.get("loc", ("body", "Unknown field")), msg=e.get("msg", "")) for e in errors]
    errors = [f"Field '{e.loc}' : {e.msg}" for e in errors_details]
    return f"[ {', '.join(errors)} ]"
