
import re

STOP_WORDS = {
    "what", "is", "are", "the", "a", "an", "of",
    "in", "on", "for", "to", "and", "or", "how",
    "why", "when", "where", "who", "which", "with",
    "this", "that", "it", "does", "do", "can",
    "explain", "tell", "me", "about", "please"
}


def answer_question(pages: list, question: str):

    if not pages:
        return {
            "answer": "No text is available in this document.",
            "page_numbers": []
        }

    if not question or not question.strip():
        return {
            "answer": "Please enter a question.",
            "page_numbers": []
        }

    question_words = set(
        re.findall(r'\b[a-zA-Z]+\b', question.lower())
    )

    question_words -= STOP_WORDS

    if not question_words:
        return {
            "answer": "Please ask a more specific question.",
            "page_numbers": []
        }

    scored_sentences = []

    for page in pages:

        page_number = page["page"]
        page_text = page["text"]

        # Remove unwanted placeholder text
        text = re.sub(
            r"write your topic here",
            "",
            page_text,
            flags=re.IGNORECASE
        )

        # Remove presenter information
        text = re.sub(
            r"presented by.*?(?=geometric dual)",
            "",
            text,
            flags=re.IGNORECASE
        )

        text = re.sub(r"\s+", " ", text).strip()

        sentences = re.split(r'(?<=[.!?])\s+', text)

        for index, sentence in enumerate(sentences):

            sentence = sentence.strip()

            if len(sentence) < 20:
                continue

            if "presented by" in sentence.lower():
                continue

            sentence_words = set(
                re.findall(r'\b[a-zA-Z]+\b', sentence.lower())
            )

            matched_words = question_words.intersection(sentence_words)

            if matched_words:
                score = len(matched_words) / len(question_words)

                scored_sentences.append(
                    (score, page_number, index, sentence)
                )

    if not scored_sentences:
        return {
            "answer": "I could not find a relevant answer in this document.",
            "page_numbers": []
        }

    scored_sentences.sort(
        key=lambda item: item[0],
        reverse=True
    )

    selected = []
    page_numbers = []
    seen = set()

    for score, page_number, index, sentence in scored_sentences:

        normalized = sentence.lower()

        if normalized not in seen:
            selected.append(sentence)
            page_numbers.append(page_number)
            seen.add(normalized)

        if len(selected) == 2:
            break

    return {
        "answer": " ".join(selected),
        "page_numbers": sorted(set(page_numbers))
    }
