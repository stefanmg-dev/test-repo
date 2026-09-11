import re


def normalize_text(text: str) -> str:

    text = re.sub(r"[ ]{2,}", " ", text)

    text = re.sub(r"http.*", "", text)

    return text.strip()