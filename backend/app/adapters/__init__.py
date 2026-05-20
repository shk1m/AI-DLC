"""External adapters: KAMIS, PublicData, Naver, NewsCrawler, S3."""

from app.adapters.base import DataSourceAdapter
from app.adapters.kamis import KamisAdapter
from app.adapters.public_data import PublicDataAdapter
from app.adapters.naver import NaverAdapter

__all__ = [
    "DataSourceAdapter",
    "KamisAdapter",
    "PublicDataAdapter",
    "NaverAdapter",
]
