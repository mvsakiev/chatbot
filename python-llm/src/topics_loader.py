import json
from pathlib import Path
from typing import Dict, Any

TOPICS_DIR = Path(__file__).parent / "topics"

def load_all_topics() -> Dict[str, Dict[str, Any]]:
    """
    Загружает все *.json из src/topics/ в словарь вида:
    {
      "math": {"grades":[...], "topics":[...]},
      "physics": {...},
      ...
    }
    """
    topics: Dict[str, Dict[str, Any]] = {}
    if not TOPICS_DIR.exists():
        return topics

    for file in sorted(TOPICS_DIR.glob("*.json")):
        subject = file.stem  # math, physics, ...
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
            # поддержка форматов:
            # 1) {"grades":[...], "topics":[...]}
            # 2) {"math":{"grades":[...],"topics":[...]}}
            if "topics" in data:
                topics[subject] = data
            elif subject in data and "topics" in data[subject]:
                topics[subject] = data[subject]
            else:
                # мягкая деградация: пропускаем некорректный файл
                continue
        except Exception:
            # не валим весь загрузчик из-за одного файла
            continue
    return topics
