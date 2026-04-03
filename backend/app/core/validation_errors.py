from __future__ import annotations

from collections.abc import Iterable

from fastapi.exceptions import RequestValidationError


def format_request_validation_error(exc: RequestValidationError) -> str:
    messages: list[str] = []
    for error in exc.errors():
        field_name = _format_location(error.get("loc", ()))
        message = _translate_error(error)
        messages.append(f"Поле {field_name}: {message}" if field_name else message)

    return "; ".join(messages) if messages else "Проверьте корректность переданных данных."


def _format_location(location: Iterable[object]) -> str:
    parts = [str(part) for part in location if part not in {"body", "query", "path", "header", "cookie"}]
    return ".".join(parts)


def _translate_error(error: dict) -> str:
    error_type = str(error.get("type") or "")
    context = error.get("ctx")

    if error_type == "missing":
        return "обязательно для заполнения"
    if error_type == "json_invalid":
        return "содержит некорректный JSON"
    if error_type == "string_too_short":
        min_length = _context_value(context, "min_length")
        return f"должно содержать минимум {min_length} символов" if min_length is not None else "слишком короткое"
    if error_type == "string_too_long":
        max_length = _context_value(context, "max_length")
        return f"должно содержать не больше {max_length} символов" if max_length is not None else "слишком длинное"
    if error_type == "int_parsing":
        return "должно быть целым числом"
    if error_type == "list_type":
        return "должно быть списком"
    if error_type == "literal_error":
        expected = _context_value(context, "expected")
        return f"содержит недопустимое значение. Допустимые значения: {expected}" if expected else "содержит недопустимое значение"
    if error_type == "bool_parsing":
        return "должно быть логическим значением"
    if error_type == "greater_than_equal":
        minimum = _context_value(context, "ge")
        return f"должно быть не меньше {minimum}" if minimum is not None else "имеет слишком маленькое значение"
    if error_type == "less_than_equal":
        maximum = _context_value(context, "le")
        return f"должно быть не больше {maximum}" if maximum is not None else "имеет слишком большое значение"
    if error_type.startswith("value_error"):
        message = str(error.get("msg") or "").strip()
        return message if message else "содержит некорректное значение"

    return "содержит некорректное значение"


def _context_value(context: object, key: str) -> object | None:
    if not isinstance(context, dict):
        return None
    return context.get(key)
