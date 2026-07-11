"""Shared API dependencies."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Query


@dataclass
class Pagination:
    page: int
    page_size: int


def pagination(
    page: int = Query(1, ge=1, description="1-based page number"),
    page_size: int = Query(25, ge=1, le=200, description="Items per page"),
) -> Pagination:
    return Pagination(page=page, page_size=page_size)
