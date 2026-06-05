from __future__ import annotations

import json
from datetime import datetime, timezone

from src.models import ContentItem, SourceType
from src.orchestrator import HorizonOrchestrator


def _item(**overrides) -> ContentItem:
    data = {
        "id": "rss:test:item-1",
        "source_type": SourceType.RSS,
        "title": "Original title",
        "url": "https://example.com/item",
        "content": "Raw source content should not be exported.",
        "published_at": datetime(2026, 6, 8, 10, 30, tzinfo=timezone.utc),
        "metadata": {
            "title_zh": "中文标题",
            "detailed_summary_zh": "中文富化摘要",
            "feed_name": "Example Feed",
        },
        "ai_score": 9.2,
        "ai_reason": "High leverage for agents.",
        "ai_summary": "AI summary fallback.",
        "ai_tags": ["agent", "automation"],
    }
    data.update(overrides)
    return ContentItem.model_validate(data)


def test_build_run_json_payload_exports_script_friendly_fields_only() -> None:
    run_at = datetime(2026, 6, 8, 23, 15, tzinfo=timezone.utc)
    payload = HorizonOrchestrator._build_run_json_payload(
        date="2026-06-08",
        run_at=run_at,
        items=[_item()],
        summaries={"zh": "完整 summary markdown"},
    )

    assert payload == {
        "run_at": "2026-06-08T23:15:00+00:00",
        "date": "2026-06-08",
        "item_count": 1,
        "summaries": {
            "zh": {
                "title": "Horizon Summary: 2026-06-08 (ZH)",
                "markdown": "完整 summary markdown",
            }
        },
        "items": [
            {
                "rank": 1,
                "title": "中文标题",
                "url": "https://example.com/item",
                "summary": "中文富化摘要",
                "score": 9.2,
                "reason": "High leverage for agents.",
                "tags": ["agent", "automation"],
            }
        ],
    }

    exported_item = payload["items"][0]
    assert "content" not in exported_item
    assert "metadata" not in exported_item
    assert "source_type" not in exported_item
    assert "source_name" not in exported_item
    assert "published_at" not in exported_item


def test_write_run_json_exports_writes_dated_and_latest_files(tmp_path) -> None:
    payload = {
        "run_at": "2026-06-08T23:15:00+00:00",
        "date": "2026-06-08",
        "item_count": 0,
        "summaries": {},
        "items": [],
    }

    paths = HorizonOrchestrator._write_run_json_exports(
        payload=payload,
        docs_dir=tmp_path,
    )

    dated_path = tmp_path / "runs" / "2026-06-08.json"
    latest_path = tmp_path / "latest.json"
    assert paths == {"dated": dated_path, "latest": latest_path}
    assert json.loads(dated_path.read_text(encoding="utf-8")) == payload
    assert json.loads(latest_path.read_text(encoding="utf-8")) == payload
