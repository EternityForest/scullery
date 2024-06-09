# SPDX-FileCopyrightText: Copyright Daniel Dunn
# SPDX-License-Identifier: LGPL-2.1-or-later

"""This file deals with conversions between camelCase, snake_case, and kebab-case.
It can convert both strings and dict keys.
"""

# https://stackoverflow.com/a/44969381/2360612

from typing import Dict, Any


def camel_to_kebab(s: str) -> str:
    return "".join(["_" + c.lower() if c.isupper() else c for c in s]).lstrip("_")


def kebab_to_snake(s: str):
    return s.replace("-", "_")


def snake_to_kebab(s: str):
    return s.replace("-", "_")


def snake_to_camel(s: str):
    temp = s.split("_")
    return temp[0] + "".join(ele.title() for ele in temp[1:])


def camel_to_snake(s: str):
    s2 = ""
    last = ""
    for i in s:
        if last.isalpha() and not last.isupper():
            if i.isupper():
                s2 += "_" + i.lower()
                continue
        last = i
        s2 += i.lower()
    return s2


def snakify_dict_keys(d: Dict[str, Any]) -> Dict[str, Any]:
    "Return a new dict with all keys converted to snake_case"
    return {camel_to_snake(kebab_to_snake(i)): d[i] for i in d}


def kebabify_dict_keys(d: Dict[str, Any]) -> Dict[str, Any]:
    "Return a new dict with all keys converted to kebab-case"
    return {snake_to_kebab(camel_to_kebab(i)): d[i] for i in d}


def camelify_dict_keys(d: Dict[str, Any]) -> Dict[str, Any]:
    "Return a new dict with all keys converted to camelCase"
    return {snake_to_camel(kebab_to_snake(i)): d[i] for i in d}
