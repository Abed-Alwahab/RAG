
import re


FOLLOWUP_WORDS = {
    "طيب", "طب", "و", "وبالنسبة", "كمان",
    "منها", "فيها", "اله", "الها", "إلها",
    "عنه", "عنها", "نفس", "ذلك", "هذه",
    "it", "its", "that", "those",
    "them", "what about", "and"
}


def normalize(text):
    return re.sub(r"\s+", " ", text).strip()


def is_followup(question):
    q = normalize(question.lower())

    if len(q.split()) <= 3:
        return True

    if any(q.startswith(word + " ") for word in (
        "طيب", "طب", "وبالنسبة", "كمان",
        "what about", "and"
    )):
        return True

    return any(
        re.search(
            rf"(?<!\w){re.escape(word)}(?!\w)",
            q
        )
        for word in FOLLOWUP_WORDS
        if len(word) > 1
    )


def build_search_query(question, history, max_turns=2):
    if not history or not is_followup(question):
        return question

    previous_questions = [
        message["content"]
        for message in history
        if message["role"] == "user"
    ]

    if not previous_questions:
        return question

    previous = previous_questions[-max_turns:]

    return (
        " ".join(previous)
        + "\n"
        + question
    )


def format_history(history, max_messages=6):
    recent = history[-max_messages:]

    lines = []

    for message in recent:
        role = (
            "Student"
            if message["role"] == "user"
            else "Advisor"
        )

        lines.append(
            f"{role}: {message['content'][:700]}"
        )

    return "\n".join(lines)
