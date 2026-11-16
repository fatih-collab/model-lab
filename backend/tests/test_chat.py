"""Chat AI outfit: RAG, penyaring topik, validasi warna, dan endpoint /api/chat (LLM di-mock)."""
import json

import pytest

from app import chat
from tests.test_api import make_client


@pytest.fixture
def client():
    with make_client() as c:
        yield c


def test_retrieve_filters_season_and_gender():
    chunks = chat.retrieve("estate_cool", "hijab untuk kerja", "wanita")
    assert chunks[0].startswith("Karakter:")
    assert any(c.startswith("Hijab") for c in chunks)
    assert not any("(pria)" in c for c in chunks)
    assert len(chunks) <= 4


def test_off_topic_skips_llm(monkeypatch):
    monkeypatch.setattr(chat, "_call_llm", lambda m: pytest.fail("LLM tidak boleh dipanggil"))
    res = chat.answer("estate_cool", "siapa presiden pertama?", [], "wanita")
    assert res["off_topic"] is True and res["outfits"] == []


def test_answer_drops_off_palette_colors(monkeypatch):
    fake = {"reply": "Coba ini", "outfits": [{
        "name": "Kerja", "items": ["Blazer soft navy"],
        "colors": ["#2F4566", "#FF0000"], "image_prompt": "navy blazer"}]}
    monkeypatch.setattr(chat, "_call_llm", lambda m: "```json\n" + json.dumps(fake) + "\n```")
    res = chat.answer("estate_cool", "outfit kerja?", [], "wanita")
    outfit = res["outfits"][0]
    assert outfit["colors"] == ["#2F4566"]
    assert outfit["image_url"].startswith("https://")


def test_chat_endpoint(client, monkeypatch):
    monkeypatch.setattr(chat, "_call_llm", lambda m: '{"reply":"Halo","outfits":[]}')
    r = client.post("/api/chat", json={"season_id": "estate_cool", "message": "outfit santai?"})
    assert r.status_code == 200, r.text
    assert r.json()["reply"] == "Halo"

    assert client.post("/api/chat", json={"season_id": "xxx", "message": "outfit?"}).status_code == 400


def test_chat_endpoint_unconfigured(client, monkeypatch):
    monkeypatch.setattr(chat, "settings", type("S", (), {"ai_api_key": "", "ai_model": ""})())
    r = client.post("/api/chat", json={"season_id": "estate_cool", "message": "outfit santai?"})
    assert r.status_code == 503
