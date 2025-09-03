import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
from openai import OpenAI

from .models import NormalizedPayload, TutorOutput
from .prompts import SYSTEM_PROMPT, JSON_SCHEMA_HINT
from .retriever_stub import retrieve

load_dotenv()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
client = OpenAI()

def build_user_message(payload: NormalizedPayload, context: list[dict]) -> Dict[str, Any]:
    return {
        "role": "user",
        "content": json.dumps({
            "STUDENT": {
                "subject": payload.subject,
                "grade": payload.grade,
                "style": payload.style,
                "language": payload.language
            },
            "TOPIC": payload.topic_id,
            "CONCEPTS": payload.concepts,
            "QUERY": payload.query_raw,
            "CONTEXT": context
        }, ensure_ascii=False)
    }

def generate(payload: NormalizedPayload) -> TutorOutput:
    # MVP: достаём мини-контекст по topic_id из заглушки
    ctx = retrieve(payload.topic_id) if payload.topic_id else []

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + " " + JSON_SCHEMA_HINT},
        build_user_message(payload, ctx)
    ]

    resp = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        response_format={"type": "json_object"}
    )

    data = json.loads(resp.choices[0].message.content)
    return TutorOutput(**data)
