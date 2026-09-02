"""A self-building standard library — the toolkit autoforge grows over years.

Each backlog item adds one small, well‑specified, independently tested utility to
a module here and exports it below. Starting from a single seed (``slugify``),
the collection is designed to expand indefinitely: strings, numbers, dates,
collections, encoding, validation, data, structures, algorithms, and more.
"""

from __future__ import annotations

from app.toolkit.algorithms import binary_search, bisect_left
from app.toolkit.bits import clear_bit, set_bit
from app.toolkit.calendars import easter_date, nth_weekday_of_month
from app.toolkit.checkdigit import ean13_check_digit, upc_check_digit
from app.toolkit.cli import confirm_prompt, parse_args_simple
from app.toolkit.collections import chunk, flatten, flatten_deep
from app.toolkit.colors import hex_to_rgb, rgb_to_hex
from app.toolkit.combinatorics import nth_permutation, permutation_index
from app.toolkit.compression import rle_bytes_decode, rle_bytes_encode
from app.toolkit.config import get_env_bool, get_env_int
from app.toolkit.datetimes import now_utc, parse_iso, to_iso
from app.toolkit.encoding import base58_encode, base62_decode, base62_encode
from app.toolkit.files import human_path, split_extension
from app.toolkit.finance import compound_interest
from app.toolkit.functional import compose, curry, pipe
from app.toolkit.geometry import distance_2d, manhattan_distance
from app.toolkit.graphx import floyd_warshall
from app.toolkit.hashing import md5_hex, sha1_hex, sha256_hex
from app.toolkit.i18n import format_list, plural_rule_en
from app.toolkit.imageppm import ppm_new, ppm_set_pixel
from app.toolkit.markdown import md_bold, md_italic
from app.toolkit.mathx import clamp_angle, hypot
from app.toolkit.matrix import mat_identity, mat_zeros
from app.toolkit.ml import euclidean_knn
from app.toolkit.net import build_query, join_url
from app.toolkit.numbers import clamp, inverse_lerp, lerp
from app.toolkit.numbertheory import euler_totient, mobius
from app.toolkit.observability import Stopwatch, Timer
from app.toolkit.parsing import compare_semver, parse_semver
from app.toolkit.physics import kinetic_energy, potential_energy
from app.toolkit.probability import binomial_pmf, poisson_pmf
from app.toolkit.randomness import random_hex, random_string
from app.toolkit.regexutil import extract_emails, extract_urls
from app.toolkit.resilience import retry
from app.toolkit.scheduling import cron_iter, next_cron_time
from app.toolkit.security import constant_time_equals, generate_token
from app.toolkit.serialization import from_jsonl, to_jsonl
from app.toolkit.statemachine import StateMachine
from app.toolkit.stats import geometric_mean, harmonic_mean
from app.toolkit.streams import batched, iterate
from app.toolkit.strings import slugify, title_case, truncate, word_wrap
from app.toolkit.structures import LFUCache, LRUCache
from app.toolkit.textsearch import fuzzy_best_match, fuzzy_ratio
from app.toolkit.units import celsius_to_fahrenheit, fahrenheit_to_celsius
from app.toolkit.validation import is_email, is_url
from app.toolkit.vectors3d import v3_add, v3_sub
from app.toolkit.webframework import Router, path_to_regex

__all__ = [
    "slugify",
    "truncate",
    "word_wrap",
    "title_case",
    "clamp",
    "lerp",
    "inverse_lerp",
    "euler_totient",
    "mobius",
    "parse_iso",
    "to_iso",
    "now_utc",
    "chunk",
    "flatten",
    "flatten_deep",
    "compose",
    "pipe",
    "curry",
    "base58_encode",
    "base62_encode",
    "base62_decode",
    "md5_hex",
    "sha256_hex",
    "sha1_hex",
    "is_email",
    "is_url",
    "parse_semver",
    "compare_semver",
    "LRUCache",
    "LFUCache",
    "binary_search",
    "bisect_left",
    "random_string",
    "random_hex",
    "fuzzy_ratio",
    "fuzzy_best_match",
    "human_path",
    "split_extension",
    "build_query",
    "join_url",
    "hex_to_rgb",
    "rgb_to_hex",
    "celsius_to_fahrenheit",
    "fahrenheit_to_celsius",
    "distance_2d",
    "manhattan_distance",
    "compound_interest",
    "get_env_bool",
    "get_env_int",
    "retry",
    "parse_args_simple",
    "confirm_prompt",
    "Router",
    "path_to_regex",
    "Stopwatch",
    "Timer",
    "to_jsonl",
    "from_jsonl",
    "constant_time_equals",
    "generate_token",
    "set_bit",
    "clear_bit",
    "batched",
    "iterate",
    "hypot",
    "clamp_angle",
    "mat_zeros",
    "mat_identity",
    "geometric_mean",
    "harmonic_mean",
    "nth_permutation",
    "permutation_index",
    "binomial_pmf",
    "poisson_pmf",
    "extract_emails",
    "extract_urls",
    "md_bold",
    "md_italic",
    "easter_date",
    "nth_weekday_of_month",
    "plural_rule_en",
    "format_list",
    "v3_add",
    "v3_sub",
    "kinetic_energy",
    "potential_energy",
    "rle_bytes_encode",
    "rle_bytes_decode",
    "ppm_new",
    "ppm_set_pixel",
    "next_cron_time",
    "cron_iter",
    "StateMachine",
    "euclidean_knn",
    "upc_check_digit",
    "ean13_check_digit",
    "floyd_warshall",
]
