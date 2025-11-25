import re
import unicodedata
from typing import Optional
from dateutil import parser

PARASITE_PATTERN = re.compile(r'[!@#$%^&*()\[\]{}<>]')
SPACE_PATTERN = re.compile(r'\s+')
CONFUSION_TRANSLATION = str.maketrans({
    'O': '0',
    'o': '0',
    'I': '1',
    'l': '1',
    'L': '1',
    'B': '8',
    'b': '8'
})


def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize('NFKD', value)
    return ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')


def normalize_text_field(value: Optional[str]) -> str:
    if not value:
        return ''
    text = strip_accents(value)
    text = text.lower()
    text = PARASITE_PATTERN.sub(' ', text)
    text = SPACE_PATTERN.sub(' ', text).strip()
    return text


def normalize_identifier(value: Optional[str]) -> str:
    if not value:
        return ''
    text = strip_accents(value)
    text = text.upper().translate(CONFUSION_TRANSLATION)
    text = PARASITE_PATTERN.sub('', text)
    text = SPACE_PATTERN.sub('', text)
    return text


def normalize_date_field(value: Optional[str]) -> str:
    if not value:
        return ''
    try:
        parsed = parser.parse(str(value), dayfirst=True, fuzzy=True)
        return parsed.strftime('%Y-%m-%d')
    except Exception:
        return ''


def clean_parasites(value: str) -> str:
    value = PARASITE_PATTERN.sub(' ', value)
    return SPACE_PATTERN.sub(' ', value).strip()


def score_text_quality(value: str) -> float:
    if not value:
        return 0.0
    alnum = len(re.findall(r'[A-Za-z0-9]', value))
    return min(alnum / max(len(value), 1), 1.0)

