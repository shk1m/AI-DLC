"""EXT-02: PublicData API Adapter (공공데이터포털)

- 수산물, 축산물, 가공식품 시세 조회
- 다중 API 호출 통합
- Circuit Breaker 적용
"""

from datetime import date, timedelta
from typing import Any

import httpx
import structlog

from app.adapters.base import DataSourceAdapter
from app.config import get_settings
from app.core.circuit_breaker import public_data_cb

logger = structlog.get_logger()

# 공공데이터포털 API 엔드포인트
PUBLIC_DATA_ENDPOINTS = {
    "수산물": "http://apis.data.go.kr/1192000/select0030List/getselect0030List",
    "축산류": "http://apis.data.go.kr/1543061/LiveStockPriceService/getLiveStockPriceList",
    "가공식품": "http://apis.data.go.kr/B553077/api/open/sdsc2/storeListInRadius",
}


class PublicDataAdapter(DataSourceAdapter):
    """공공데이터포털 API 어댑터

    수산물, 축산물, 가공식품 등 다중 API를 통합 인터페이스로 제공.
    """

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.public_data_api_key
        self.timeout = httpx.Timeout(5.0, connect=3.0)

    async def fetch_prices(
        self,
        category: str,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[dict[str, Any]]:
        """카테고리별 시세 조회

        Args:
            category: 카테고리명 (수산물, 축산류, 가공식품)
            date_from: 조회 시작일
            date_to: 조회 종료일
        """
        if date_to is None:
            date_to = date.today()
        if date_from is None:
            date_from = date_to - timedelta(days=7)

        endpoint = PUBLIC_DATA_ENDPOINTS.get(category)
        if not endpoint:
            logger.warning("public_data_unknown_category", category=category)
            return []

        if category == "수산물":
            return await self._fetch_seafood_prices(endpoint, date_from, date_to)
        elif category == "축산류":
            return await self._fetch_livestock_prices(endpoint, date_from, date_to)
        elif category == "가공식품":
            return await self._fetch_processed_prices(endpoint, date_from, date_to)

        return []

    async def fetch_item_price(
        self,
        item_code: str,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[dict[str, Any]]:
        """특정 품목 시세 조회"""
        if date_to is None:
            date_to = date.today()
        if date_from is None:
            date_from = date_to - timedelta(days=30)

        # 품목 코드로 카테고리 추정 후 해당 API 호출
        # 실제 구현에서는 품목 마스터 DB에서 카테고리 조회
        logger.info("public_data_item_fetch", item_code=item_code)
        return []

    async def health_check(self) -> bool:
        """공공데이터포털 API 상태 확인"""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(3.0)) as client:
                response = await client.get(
                    "http://apis.data.go.kr/1192000/select0030List/getselect0030List",
                    params={
                        "serviceKey": self.api_key,
                        "numOfRows": "1",
                        "pageNo": "1",
                        "type": "json",
                    },
                )
                return response.status_code == 200
        except Exception as e:
            logger.warning("public_data_health_check_failed", error=str(e))
            return False

    async def _fetch_seafood_prices(
        self, endpoint: str, date_from: date, date_to: date
    ) -> list[dict[str, Any]]:
        """수산물 시세 조회"""
        params = {
            "serviceKey": self.api_key,
            "numOfRows": "100",
            "pageNo": "1",
            "type": "json",
            "baseDt": date_to.strftime("%Y%m%d"),
        }

        async def _fetch():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                return response.json()

        try:
            raw_data = await public_data_cb.call(_fetch)
            return self._parse_seafood_response(raw_data)
        except Exception as e:
            logger.error("public_data_seafood_error", error=str(e))
            return []

    async def _fetch_livestock_prices(
        self, endpoint: str, date_from: date, date_to: date
    ) -> list[dict[str, Any]]:
        """축산물 시세 조회"""
        params = {
            "serviceKey": self.api_key,
            "numOfRows": "100",
            "pageNo": "1",
            "type": "json",
            "baseDt": date_to.strftime("%Y%m%d"),
        }

        async def _fetch():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                return response.json()

        try:
            raw_data = await public_data_cb.call(_fetch)
            return self._parse_livestock_response(raw_data)
        except Exception as e:
            logger.error("public_data_livestock_error", error=str(e))
            return []

    async def _fetch_processed_prices(
        self, endpoint: str, date_from: date, date_to: date
    ) -> list[dict[str, Any]]:
        """가공식품 시세 조회"""
        params = {
            "serviceKey": self.api_key,
            "numOfRows": "100",
            "pageNo": "1",
            "type": "json",
        }

        async def _fetch():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                return response.json()

        try:
            raw_data = await public_data_cb.call(_fetch)
            return self._parse_processed_response(raw_data)
        except Exception as e:
            logger.error("public_data_processed_error", error=str(e))
            return []

    def _parse_seafood_response(self, raw_data: dict) -> list[dict[str, Any]]:
        """수산물 API 응답 파싱"""
        results = []
        try:
            body = raw_data.get("response", {}).get("body", {})
            items = body.get("items", {}).get("item", [])

            if not isinstance(items, list):
                items = [items] if items else []

            for item in items:
                wholesale = float(item.get("whslCost", 0) or 0)
                retail = float(item.get("rtlCost", 0) or 0)

                if wholesale <= 0 and retail <= 0:
                    continue

                if wholesale <= 0:
                    wholesale = retail * 0.7
                if retail <= 0:
                    retail = wholesale * 1.4

                results.append({
                    "item_name": item.get("goodNm", ""),
                    "item_code": item.get("goodCd", ""),
                    "unit": item.get("unitNm", "kg"),
                    "wholesale_price": wholesale,
                    "retail_price": retail,
                    "date": date.today(),
                    "source": "공공데이터포털",
                })
        except (KeyError, TypeError, ValueError) as e:
            logger.error("public_data_seafood_parse_error", error=str(e))

        return results

    def _parse_livestock_response(self, raw_data: dict) -> list[dict[str, Any]]:
        """축산물 API 응답 파싱"""
        results = []
        try:
            body = raw_data.get("response", {}).get("body", {})
            items = body.get("items", {}).get("item", [])

            if not isinstance(items, list):
                items = [items] if items else []

            for item in items:
                price = float(item.get("price", 0) or 0)
                if price <= 0:
                    continue

                results.append({
                    "item_name": item.get("itemNm", ""),
                    "item_code": item.get("itemCd", ""),
                    "unit": "kg",
                    "wholesale_price": price * 0.7,
                    "retail_price": price,
                    "date": date.today(),
                    "source": "공공데이터포털",
                })
        except (KeyError, TypeError, ValueError) as e:
            logger.error("public_data_livestock_parse_error", error=str(e))

        return results

    def _parse_processed_response(self, raw_data: dict) -> list[dict[str, Any]]:
        """가공식품 API 응답 파싱"""
        results = []
        try:
            body = raw_data.get("response", {}).get("body", {})
            items = body.get("items", {}).get("item", [])

            if not isinstance(items, list):
                items = [items] if items else []

            for item in items:
                price = float(item.get("price", 0) or 0)
                if price <= 0:
                    continue

                results.append({
                    "item_name": item.get("goodNm", ""),
                    "item_code": item.get("goodCd", ""),
                    "unit": item.get("unitNm", "개"),
                    "wholesale_price": price * 0.7,
                    "retail_price": price,
                    "date": date.today(),
                    "source": "공공데이터포털",
                })
        except (KeyError, TypeError, ValueError) as e:
            logger.error("public_data_processed_parse_error", error=str(e))

        return results
