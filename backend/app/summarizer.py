import re


def generate_summary(text: str):
    if not text or not text.strip():
        return "No text found in this document."

    text = re.sub(r"\s+", " ", text).strip()

    text = re.sub(
        r"write your topic here",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"presented by.*?(?=geometric dual)",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\bPRESENTED BY\b",
        "",
        text,
        flags=re.IGNORECASE
    )

    sentences = re.split(r'(?<=[.!?])\s+', text)

    sentences = [
        sentence.strip()
        for sentence in sentences
        if len(sentence.strip()) > 35
        and "presented by" not in sentence.lower()
    ]

    if not sentences:
        return "Not enough meaningful text to generate a summary."

    important_words = {
        "concept", "definition", "process", "method",
        "system", "result", "conclusion", "applications",
        "advantages", "analysis", "theory", "graph",
        "technology", "example", "purpose", "important"
    }

    scored_sentences = []

    for index, sentence in enumerate(sentences):
        words = set(
            re.findall(r"\b[a-zA-Z]+\b", sentence.lower())
        )

        score = len(words.intersection(important_words))
        score += max(0, 3 - index * 0.1)

        scored_sentences.append((score, index, sentence))

    selected = sorted(
        scored_sentences,
        key=lambda item: item[0],
        reverse=True
    )[:4]

    selected.sort(key=lambda item: item[1])

    summary = " ".join(
        sentence for score, index, sentence in selected
    )

    return summary