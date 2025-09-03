
import os
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from src.models import NormalizeInput, NormalizedPayload, TutorOutput
from src.llm_normalizer import llm_normalize
from src.generator import generate

load_dotenv()

ALLOWED_ORIGINS = os.getenv("CORS_ORIGIN", "*")
if ALLOWED_ORIGINS:
    origins = [o.strip() for o in ALLOWED_ORIGINS.split(",") if o.strip()]
else:
    origins = ["*"]

app = FastAPI(title="Study Tutor LLM Service", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    subject: Optional[str] = None
    grade: Optional[int] = None
    style: Optional[str] = None
    query: str

def to_markdown(payload: NormalizedPayload, out: TutorOutput) -> str:
    lines = []
    header = f"**Тема:** {payload.subject} • **Класс:** {payload.grade} • **Стиль:** {payload.style}"
    if payload.topic:
        header += f" • **Топик:** {payload.topic}"
    lines.append(header)
    lines.append("")
    lines.append("## Объяснение")
    lines.append(out.explanation.strip())
    if out.examples:
        lines.append("")
        lines.append("## Примеры")
        for ex in out.examples:
            lines.append(f"- {ex}")
    if out.pitfalls:
        lines.append("")
        lines.append("## Частые ошибки")
        for p in out.pitfalls:
            lines.append(f"- {p}")
    if out.checks:
        lines.append("")
        lines.append("## Проверь себя")
        for i, qa in enumerate(out.checks, 1):
            q = qa.get("q", "").strip()
            a = qa.get("a", "").strip()
            if not q:
                continue
            lines.append(f"<details><summary><strong>Вопрос {i}.</strong> {q}</summary>")
            if a:
                lines.append("")
                lines.append(a)
            lines.append("</details>")
    if out.homework:
        lines.append("")
        lines.append("## Домашка")
        for h in out.homework:
            lines.append(f"- {h}")
    if out.citations:
        lines.append("")
        lines.append("## Источники/Контекст")
        for c in out.citations:
            lines.append(f"- {c}")
    return "\n".join(lines).strip()

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/api/generate")
def api_generate(req: GenerateRequest):
    norm: NormalizedPayload = llm_normalize(NormalizeInput(**req.model_dump()))
    out: TutorOutput = generate(norm)
    md = to_markdown(norm, out)
    return {"payload": norm.model_dump(), "output": out.model_dump(), "markdown": md}
