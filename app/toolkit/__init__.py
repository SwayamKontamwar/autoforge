"""A self-building standard library — the toolkit autoforge grows over years.

Each backlog item adds one small, well‑specified, independently tested utility to
a module here and exports it below. Starting from a single seed (``slugify``),
the collection is designed to expand indefinitely: strings, numbers, dates,
collections, encoding, validation, data, structures, algorithms, and more.
"""

from __future__ import annotations

from app.toolkit.algorithms import binary_search
from app.toolkit.bits import set_bit
from app.toolkit.calendars import easter_date
from app.toolkit.checkdigit import upc_check_digit
from app.toolkit.cli import parse_args_simple
from app.toolkit.collections import chunk
from app.toolkit.colors import hex_to_rgb
from app.toolkit.combinatorics import nth_permutation
from app.toolkit.compression import rle_bytes_encode
from app.toolkit.config import get_env_bool
from app.toolkit.datetimes import parse_iso
from app.toolkit.encoding import base62_encode
from app.toolkit.files import human_path
from app.toolkit.finance import compound_interest
from app.toolkit.functional import compose
from app.toolkit.geometry import distance_2d
from app.toolkit.hashing import md5_hex
from app.toolkit.i18n import plural_rule_en
from app.toolkit.imageppm import ppm_new
from app.toolkit.markdown import md_bold
from app.toolkit.mathx import hypot
from app.toolkit.matrix import mat_zeros
from app.toolkit.ml import euclidean_knn
from app.toolkit.net import build_query
from app.toolkit.numbers import clamp
from app.toolkit.numbertheory import euler_totient
from app.toolkit.observability import Stopwatch
from app.toolkit.parsing import parse_semver
from app.toolkit.physics import kinetic_energy
from app.toolkit.probability import binomial_pmf
from app.toolkit.randomness import random_string
from app.toolkit.regexutil import extract_emails
from app.toolkit.resilience import retry
from app.toolkit.scheduling import next_cron_time
from app.toolkit.security import constant_time_equals
from app.toolkit.serialization import to_jsonl
from app.toolkit.statemachine import StateMachine
from app.toolkit.stats import geometric_mean
from app.toolkit.streams import batched
from app.toolkit.strings import slugify, truncate, word_wrap
from app.toolkit.structures import LRUCache
from app.toolkit.textsearch import fuzzy_ratio
from app.toolkit.units import celsius_to_fahrenheit
from app.toolkit.validation import is_email
from app.toolkit.vectors3d import v3_add
from app.toolkit.webframework import Router

__all__ = [
    "slugify",
    "truncate",
    "word_wrap",
    "clamp",
    "euler_totient",
    "parse_iso",
    "chunk",
    "compose",
    "base62_encode",
    "md5_hex",
    "is_email",
    "parse_semver",
    "LRUCache",
    "binary_search",
    "random_string",
    "fuzzy_ratio",
    "human_path",
    "build_query",
    "hex_to_rgb",
    "celsius_to_fahrenheit",
    "distance_2d",
    "compound_interest",
    "get_env_bool",
    "retry",
    "parse_args_simple",
    "Router",
    "Stopwatch",
    "to_jsonl",
    "constant_time_equals",
    "set_bit",
    "batched",
    "hypot",
    "mat_zeros",
    "geometric_mean",
    "nth_permutation",
    "binomial_pmf",
    "extract_emails",
    "md_bold",
    "easter_date",
    "plural_rule_en",
    "v3_add",
    "kinetic_energy",
    "rle_bytes_encode",
    "ppm_new",
    "next_cron_time",
    "StateMachine",
    "euclidean_knn",
    "upc_check_digit",
]
