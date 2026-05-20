"""외부 데이터 소스 어댑터 인터페이스 (확장성 패턴: Adapter Pattern)

새 데이터 소스 추가 시:
1. DataSourceAdapter 구현
2. 설정에 등록
3. 기존 코드 변경 없음 (SCALE-01)
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Any


class DataSourceAdapter(ABC):
    """외부 데이터 소스 어댑터 추상 클래스"""

    @abstractmethod
    async def fetch_prices(
        self,
        category: str,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[dict[str, Any]]:
        """시세 데이터 조회

        Returns:
            list of dict with keys:
            - item_name: str
            - wholesale_price: float
            - retail_price: float
            - unit: str
            - date: date
        """
        ...

    @abstractmethod
    async def fetch_item_price(
        self,
        item_code: str,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[dict[str, Any]]:
        """특정 품목 시세 조회"""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """서비스 상태 확인"""
        ...
