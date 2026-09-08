import re

from app.constants import SLUG_PATTERN, USERNAME_PATTERN

_USERNAME_RE = re.compile(USERNAME_PATTERN)
_SLUG_RE = re.compile(SLUG_PATTERN)


def normalize_username(value: str) -> str:
    return value.strip().lower()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug


def is_valid_username(value: str) -> bool:
    return bool(_USERNAME_RE.match(normalize_username(value)))


def is_valid_slug(value: str) -> bool:
    return bool(_SLUG_RE.match(slugify(value)))
