import re


def mask_pii(text: str) -> str:
    """
    Mask common personally identifiable information (PII)
    from customer transcripts and support content.
    """

    if not text:
        return text

    masked = text

    # Email addresses
    masked = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "[EMAIL REDACTED]",
        masked
    )

    # Indian mobile numbers
    # Phone numbers
    masked = re.sub(
    r"(?<!\d)(?:\+91[\s-]?)?(?:\d[\s-]?){8,12}(?!\d)",
    "[PHONE REDACTED]",
    masked
)

    # 12-digit Aadhaar-like numbers
    masked = re.sub(
        r"(?<!\d)\d{4}[\s-]?\d{4}[\s-]?\d{4}(?!\d)",
        "[ID REDACTED]",
        masked
    )

    # Credit/debit-card-like 16 digit numbers
    masked = re.sub(
        r"(?<!\d)(?:\d{4}[\s-]?){3}\d{4}(?!\d)",
        "[CARD REDACTED]",
        masked
    )

    # CVV-like values when explicitly labelled
    masked = re.sub(
        r"(?i)\b(?:cvv|cvc|security code)\s*[:\-]?\s*\d{3,4}\b",
        "[SECURITY CODE REDACTED]",
        masked
    )

    return masked