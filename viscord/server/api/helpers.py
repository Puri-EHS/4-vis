import json
from flask import Response

def validate_fields(data, name_type):
    for name, type_ in name_type.items():
        if name not in data:
            return False
        if not isinstance(data[name], type_):
            return False
    return True

def validate_color(color: str) -> bool:
    if len(color) != 6:
        return False
    if not all([c in "1234567890abcdef" for c in color]):
        return False
    return True


def invalid_fields():
    return Response(
        json.dumps({"type": "incorrect", "message": "Invalid fields"}),
        status=400)

def return_error(e):
    return Response(
        json.dumps({"type": "error", "message": str(e)}),
        status=500)

def return_success():
    return Response(
        json.dumps({"type": "success"}),
        status=200)

def missing_permissions():
    return Response(
        json.dumps({"type": "incorrect", "message": "You do not have permission to perform this action"}),
        status=403)