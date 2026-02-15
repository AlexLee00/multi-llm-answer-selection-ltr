import uuid

def generate_dummy_candidates(question_text: str):
    c1 = {
        "provider": "openai",
        "model": "gpt-dummy",
        "answer_summary": f"Step-by-step explanation for: {question_text}",
        "has_code": False,
    }

    c2 = {
        "provider": "gemini",
        "model": "gemini-dummy",
        "answer_summary": f"Example code solution for: {question_text}",
        "has_code": True,
    }

    return [c1, c2]
