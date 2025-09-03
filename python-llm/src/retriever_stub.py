from typing import List, Dict

# MVP: статичные кусочки по topic_id (вместо RAG, чтобы было что цитировать)
SNIPPETS = {
    "math.geometry.pythagorean_theorem": [
        {
            "source": "Учебник Геометрия 8 кл.",
            "text": "Теорема Пифагора: в прямоугольном треугольнике квадрат гипотенузы равен сумме квадратов катетов."
        },
        {
            "source": "Конспект",
            "text": "Если c — гипотенуза, a и b — катеты, то c^2 = a^2 + b^2. Обратная теорема позволяет проверять прямоугольность."
        }
    ],
    "math.algebra.linear_equations": [
        {"source": "Алгебра 7 кл.", "text": "Линейное уравнение: ax + b = 0, решение x = -b/a, a ≠ 0."}
    ],
    "bio.cell": [
        {"source": "Биология 6 кл.", "text": "Клетка — структурная и функциональная единица живого. Органоиды: ядро, митохондрии, рибосомы."}
    ]
}

def retrieve(topic_id: str, k: int = 3) -> List[Dict[str, str]]:
    return SNIPPETS.get(topic_id, [])[:k]
