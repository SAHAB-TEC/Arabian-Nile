# -*- coding: utf-8 -*-
"""Helpers for hiding analytic records from selection without blocking reads."""


def rgb_domain_resolves_ids(domain):
    """Return True when the domain fetches known record ids.

    Access checks and Many2one display use domains like ``('id', 'in', ids)``.
    Those must still return invisible records so old documents keep opening.
    Selection/search domains (name, code, etc.) must keep hiding them.
    """
    for item in domain or []:
        if isinstance(item, (list, tuple)) and len(item) >= 3:
            field, operator = item[0], item[1]
            if field == "id" and operator in ("=", "in"):
                return True
    return False
