import os, json
from typing import Any, Dict, List
from dotenv import load_dotenv
from openai import OpenAI

from .models import NormalizeInput, NormalizedPayload
from .topics_loader import load_all_topics

load_dotenv()
client = OpenAI()
NORM_MODEL = os.getenv("OPENAI_NORM_MODEL", "gpt-4o-mini")

# Загружаем все предметы из src/topics/*.json
ALL_TOPICS: Dict[str, Dict[str, Any]] = load_all_topics()

def _catalog_for_prompt() -> List[Dict[str, Any]]:
    """
    Делаем компактный каталог для промпта нормализатора:
    [{subject, id, title, synonyms, grades}, ...]
    """
    catalog: List[Dict[str, Any]] = []
    for subject, block in ALL_TOPICS.items():
        for t in block.get("topics", []):
            catalog.append({
                "subject": subject,
                "id": t.get("id"),
                "title": t.get("title"),
                "synonyms": t.get("synonyms", []),
                "grades": t.get("grades", [])
            })
    return catalog

SYSTEM = (
  "Ты — модуль нормализации запроса школьного ассистента. Вход: сырые поля (subject/grade/style/query). "
  "Выведи единый JSON-профиль. Если предмет в тексте не совпадает с subject клиента — при высокой уверенности (>=0.9) переключи subject и добавь флаг override_subject_from_query; при средней (0.6–0.9) добавь suggest_subject_switch. "
  "Подбери topic_id из CATALOG (по title/synonyms). Если не нашлось — верни null. "
  "Определи intent (explain/practice/solve/hint/exam_prep). style нормализуй в [simple|expanded|ege]. "
  "Всегда добавляй confidence.subject и confidence.topic (0..1). Возвращай только JSON, без текста."
)

FEW_SHOT = [
  {"role":"user","content": json.dumps({
      "subject":"biology","grade":8,"style":"для ЕГЭ","query":"Докажи теорему Пифагора и дай пару задач",
      "CATALOG":[{"subject":"mathematics","id":"math.geometry.pythagorean_theorem","title":"Теорема Пифагора","synonyms":["пифагора","гипотенуза","катет"],"grades":[7,8]}]
  }, ensure_ascii=False)},
  {"role":"assistant","content": json.dumps({
      "subject":"mathematics","grade":8,"style":"ege","intent":"solve",
      "topic_id":"math.geometry.pythagorean_theorem",
      "concepts":["прямоугольный","катет","гипотенуза"],
      "language":"ru","query_raw":"Докажи теорему Пифагора и дай пару задач",
      "confidence":{"subject":0.95,"topic":0.9},
      "flags":["override_subject_from_query"]
  }, ensure_ascii=False)}
]

def llm_normalize(inp: NormalizeInput) -> NormalizedPayload:
    catalog = _catalog_for_prompt()

    user_payload: dict[str, Any] = {
        "subject": inp.subject,
        "grade": inp.grade,
        "style": inp.style,
        "query": inp.query,
        "CATALOG": catalog
    }

    messages = [{"role":"system","content": SYSTEM}] + FEW_SHOT + [
        {"role":"user","content": json.dumps(user_payload, ensure_ascii=False)}
    ]

    resp = client.chat.completions.create(
        model=NORM_MODEL,
        messages=messages,
        response_format={"type":"json_object"}
    )
    data = json.loads(resp.choices[0].message.content)

    # Фолбэки/приведение к схеме
    data.setdefault("subject", inp.subject or "mathematics")
    data.setdefault("grade", int(inp.grade or 8))
    style_map = {"просто":"simple","simple":"simple","развернуто":"expanded","подробно":"expanded","для егэ":"ege","егэ":"ege","ege":"ege"}
    data["style"] = style_map.get(str(data.get("style","simple")).lower(), "simple")
    data.setdefault("intent", "explain")
    data.setdefault("language", "ru")
    data.setdefault("query_raw", inp.query)
    data.setdefault("concepts", [])
    data.setdefault("confidence", {"subject":0.5, "topic":0.0})
    data.setdefault("flags", [])

    return NormalizedPayload(**data)
