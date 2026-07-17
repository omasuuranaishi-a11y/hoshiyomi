from __future__ import annotations

from datetime import date
import os
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from .engine import calculate_reading
from .translator import build_message, summarize_theme

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "frontend" / "index.html"

app = FastAPI(title="あなただけの今日の星よみ")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["*"])


class ReadingRequest(BaseModel):
    name: str | None = Field(default=None, max_length=40)
    birth_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    birth_time: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    target_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    if not INDEX_PATH.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    html = INDEX_PATH.read_text(encoding="utf-8")
    return html.replace("__LIFF_ID__", os.getenv("LIFF_ID", ""))


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/reading")
def reading(
    payload: ReadingRequest,
    x_line_id_token: Annotated[str | None, Header(alias="X-Line-ID-Token")] = None,
) -> JSONResponse:
    try:
        data = calculate_reading(
            birth_date=payload.birth_date,
            birth_time=payload.birth_time,
            target_date=payload.target_date or date.today().isoformat(),
            name=payload.name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="生年月日の形式を確認してください。") from exc

    data["theme"] = summarize_theme(data)
    data["message"] = build_message(data)
    data["line_verified"] = bool(x_line_id_token)
    return JSONResponse(data)
