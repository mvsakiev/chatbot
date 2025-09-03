from .models import NormalizeInput
from .llm_normalizer import llm_normalize
from .generator import generate

def run_example():
    user = NormalizeInput(
        subject="biology",     # намеренно конфликтный выбор
        grade=8,
        style="для ЕГЭ",
        query="Докажи теорему Пифагора и дай пару задач"
    )

    norm = llm_normalize(user)
    print("Normalized payload (LLM):")
    print(norm.model_dump())

    out = generate(norm)
    print("\n=== TUTOR OUTPUT ===")
    print("\nExplanation:\n", out.explanation)
    print("\nExamples:")
    for e in out.examples:
        print("-", e)
    print("\nPitfalls:")
    for p in out.pitfalls:
        print("-", p)
    print("\nChecks:")
    for q in out.checks:
        print(f"- {q.get('q')} → {q.get('a')}")
    print("\nHomework:")
    for h in out.homework:
        print("-", h)
    print("\nCitations:")
    for c in out.citations:
        print("-", c)

if __name__ == "__main__":
    run_example()
