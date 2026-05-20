# Step 8 Summary — News Schema (Pydantic v2)

**Phase**: C  
**NFR**: SECURITY-05, PBT-08, BR-08

## Created files
- `backend/app/schemas/news.py` — `NewsArticle`, `NewsArticleCreate`, `NewsSearchQuery`, `NewsSourceEnum`
- `backend/tests/unit/test_news_schema.py` — 19 tests (5 strip_html + 8 article + 1 create + 3 search + 2 PBT)

## Validation rules implemented
- `title` ≤ 500자 + HTML 태그 자동 제거 (XSS 보호)
- `url` HttpUrl + http/https only
- `source` Enum 강제
- `published_at` timezone-aware 강제
- `keywords` 최대 20개, 각 ≤ 50자, 대소문자 무관 dedup
- `summary` 비었으면 title 일부로 자동 채움
- `extra="forbid"` — 알 수 없는 필드 거부
- `NewsSearchQuery`: keyword ≤ 50자, date_from ≤ date_to

## PBT
- `model_dump(mode="json")` ↔ `model_validate` round-trip
- `model_dump_json()` ↔ `model_validate_json` round-trip

## Notes
- 임시 모델 — Unit 2의 NewsService 도입 시 통합 (16:30 싱크포인트)
- DB 모델은 추후 별도 SQLAlchemy 매핑 (현 단계 범위 외)
