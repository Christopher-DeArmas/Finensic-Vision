"""Shared schema types: pagination wrapper."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """A paginated list response."""

    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def build(cls, items: list, total: int, page: int, page_size: int) -> "Page":
        pages = (total + page_size - 1) // page_size if page_size else 0
        return cls(
            items=items, total=total, page=page, page_size=page_size, pages=pages
        )
