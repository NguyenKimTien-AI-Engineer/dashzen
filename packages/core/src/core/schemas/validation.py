from typing import Any

_FIELD_MESSAGES: dict[str, dict[str, str]] = {
    "email": {
        "value_error": "Enter a valid email address.",
        "missing": "Email is required.",
    },
    "password": {
        "string_too_short": "Password is required.",
        "missing": "Password is required.",
        "value_error": "Password is invalid.",
    },
    "display_name": {
        "string_too_long": "Display name must be at most 100 characters.",
        "string_too_short": "Display name cannot be empty.",
    },
}

_CUSTOM_ERROR_CODES = frozenset(
    {
        "password_too_short",
        "password_too_weak",
        "invalid_email",
        "password_required",
        "password_invalid",
        "display_name_too_long",
    }
)


def _field_name(location: tuple[str | int, ...]) -> str:
    if len(location) >= 2 and location[0] == "body":
        return str(location[1])
    if location:
        return str(location[-1])
    return "unknown"


def _error_code(err: dict[str, Any], field: str) -> str:
    err_type = str(err.get("type", ""))
    if err_type in _CUSTOM_ERROR_CODES:
        return err_type
    if field == "email":
        return "invalid_email"
    if field == "password":
        if err_type == "string_too_short":
            min_length = (err.get("ctx") or {}).get("min_length", 1)
            return "password_too_short" if min_length > 1 else "password_required"
        return "password_invalid"
    if field == "display_name":
        if err_type == "string_too_short":
            return "display_name_empty"
        return "display_name_too_long"
    return "validation_error"


def format_validation_errors(errors: list[dict[str, Any]]) -> dict[str, Any]:
    fields: list[dict[str, str]] = []

    for err in errors:
        field = _field_name(tuple(err.get("loc", ())))
        err_type = str(err.get("type", ""))
        raw_message = str(err.get("msg", "Invalid value."))

        if err_type in _CUSTOM_ERROR_CODES:
            code = err_type
            message = raw_message
        elif err_type == "string_too_short" and field == "password":
            min_length = (err.get("ctx") or {}).get("min_length", 1)
            if min_length > 1:
                code = "password_too_short"
                message = f"Password must be at least {min_length} characters."
            else:
                code = "password_required"
                message = "Password is required."
        else:
            field_rules = _FIELD_MESSAGES.get(field, {})
            message = field_rules.get(err_type, field_rules.get("value_error", raw_message))
            code = _error_code(err, field)

        fields.append({"field": field, "code": code, "message": message})

    summary = "Validation failed."
    if len(fields) == 1:
        summary = fields[0]["message"]

    return {
        "error": {
            "code": "validation_error",
            "message": summary,
            "fields": fields,
        }
    }
