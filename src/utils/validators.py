"""Shared field-validation helpers.

Controllers used to hand-roll their own `validate*()` functions
(`auth_controller`, `product_controller`) or scatter inline
`if not X: return jsonify(...), 400` checks (`category_controller`,
`order_controller`), each reimplementing the same handful of checks
(required string, email format, positive number, allowed value) slightly
differently. See ARCHITECTURE_IMPROVEMENTS.md Step 6.

Each helper below checks one field and returns an error dict shaped like
`{'type': 'field', 'msg': ..., 'path': field}` (the shape the frontend
already expects from `validateRegister`/`validateProduct`), or `None` when
the value is valid. Controllers stay responsible for collecting these into
an `errors` list and turning a non-empty list into the `jsonify(...), 400`
response — these helpers only decide pass/fail per field, no control flow.
"""
import re

EMAIL_REGEX = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'


def _error(field, msg):
    return {'type': 'field', 'msg': msg, 'path': field}


def required_string(value, field, min_len=None, max_len=None, message=None, length_message=None):
    """Non-empty (after strip) string, optionally length-bounded."""
    text = value.strip() if isinstance(value, str) else ''
    if not text:
        return _error(field, message or f'{field.capitalize()} is required')
    too_short = min_len is not None and len(text) < min_len
    too_long = max_len is not None and len(text) > max_len
    if too_short or too_long:
        if length_message:
            return _error(field, length_message)
        if min_len is not None and max_len is not None:
            return _error(field, f'{field.capitalize()} must be {min_len}-{max_len} characters')
        if min_len is not None:
            return _error(field, f'{field.capitalize()} must be at least {min_len} characters')
        return _error(field, f'{field.capitalize()} must be at most {max_len} characters')
    return None


def max_length(value, field, max_len, message=None):
    """Optional string, only checked once it's non-empty."""
    text = value if isinstance(value, str) else (value or '')
    if text and len(text) > max_len:
        return _error(field, message or f'{field.capitalize()} must be at most {max_len} characters')
    return None


def valid_email(value, field='email', message=None):
    email = value.strip().lower() if isinstance(value, str) else ''
    if not email or not re.match(EMAIL_REGEX, email):
        return _error(field, message or 'Valid email is required')
    return None


def strong_password(value, field='password', min_len=6):
    """Minimum length, then upper/lower/digit complexity."""
    password = value or ''
    if len(password) < min_len:
        return _error(field, f'Password must be at least {min_len} characters')
    if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)', password):
        return _error(field, 'Password must contain uppercase, lowercase, and number')
    return None


def positive_number(value, field, allow_zero=False, integer=False, message=None):
    """Numeric field, either > 0 or (with allow_zero) >= 0."""
    try:
        number = int(value) if integer else float(value)
    except (TypeError, ValueError):
        return _error(field, message or f'{field.capitalize()} must be greater than 0')
    if allow_zero:
        if number < 0:
            return _error(field, message or f'{field.capitalize()} must be 0 or positive')
    elif number <= 0:
        return _error(field, message or f'{field.capitalize()} must be greater than 0')
    return None


def one_of(value, field, allowed, message=None):
    if value not in allowed:
        return _error(field, message or f'Invalid {field}')
    return None


def required_list(value, field, message=None):
    if not value or len(value) == 0:
        return _error(field, message or f'{field.capitalize()} is required')
    return None
