"""External adapters: KAMIS, PublicData, Naver, NewsCrawler, S3.

Note: Unit 2 adapters (kamis, naver, public_data) require circuit breaker
instances that are defined in their own modules. They are imported lazily
to avoid circular import issues with Unit 4's circuit_breaker.py.
"""

from app.adapters.base import DataSourceAdapter

__all__ = [
    "DataSourceAdapter",
]
