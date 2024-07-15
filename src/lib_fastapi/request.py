from typing import Any, Dict

from fastapi import HTTPException


def raise_if_not_defined_values(args: Dict[str, Any]):
    missing_values = [name for name, arg in args.items() if not (arg)]

    if len(missing_values):
        missing_values_str = ", ".join(args)
        raise HTTPException(401, f"Missing mandatory values: {missing_values_str}")
