import json
from typing import Any

from pydantic import BaseModel


def is_expected_result_json(result_json: dict[str, Any], expected_json: BaseModel) -> bool:
    return bool(result_json == json.loads(expected_json.model_dump_json(by_alias=True)))
