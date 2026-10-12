"""
VaaniAI — Response Filter
Cleans LLM output for TTS (text-to-speech) consumption.

Problems it solves:
- LLMs sometimes output markdown (**, ##, -, etc.)
- LLMs sometimes give very long answers
- LLMs sometimes use emojis or special characters
- TTS engines read punctuation weirdly if not cleaned
"""

import re


class ResponseFilter:
    """Clean AI output so TTS reads it naturally."""

    MAX_SENTENCES = 15      # Allow long presentations when requested
    MAX_CHARS = 1500        # Allow full paragraphs for presentations

    @staticmethod
    def clean(text: str) -> str:
        """
        Clean LLM response for TTS.

        Steps:
        1. Remove markdown formatting
        2. Remove emojis and special characters
        3. Trim to max sentences
        4. Trim to max characters
        5. Clean up whitespace

        Args:
            text: Raw LLM response

        Returns:
            Clean, TTS-friendly text
        """
        if not text:
            return "I am not sure what to say."

        # ── Step 1: Remove action tags and markdown ───────────────────────
        # Delete action roleplay like *laughs* or (giggles) completely
        text = re.sub(r'\*.*?\*', '', text)
        text = re.sub(r'\(.*?\)', '', text)
        # Headers
        text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
        # Bullet points
        text = re.sub(r'^[\-\*\•]\s*', '', text, flags=re.MULTILINE)
        # Numbered lists
        text = re.sub(r'^\d+\.\s*', '', text, flags=re.MULTILINE)
        # Code blocks
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        # Inline code
        text = re.sub(r'`([^`]*)`', r'\1', text)
        # Links
        text = re.sub(r'\[([^\]]*)\]\([^\)]*\)', r'\1', text)

        # ── Step 2: Remove emojis and special characters ──────────────────
        # Remove emoji Unicode ranges
        text = re.sub(
            r'[\U0001F600-\U0001F64F'   # emoticons
            r'\U0001F300-\U0001F5FF'     # symbols & pictographs
            r'\U0001F680-\U0001F6FF'     # transport & map
            r'\U0001F1E0-\U0001F1FF'     # flags
            r'\U00002702-\U000027B0'     # dingbats
            r'\U0001FA00-\U0001FA6F'     # chess symbols
            r'\U0001FA70-\U0001FAFF'     # symbols extended
            r'\U00002600-\U000026FF'     # misc symbols
            r']+', '', text
        )

        # ── Step 3: Clean up whitespace ───────────────────────────────────
        # Multiple newlines → single space
        text = re.sub(r'\n+', ' ', text)
        # Multiple spaces → single space
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        # ── Step 4: Trim to max sentences ─────────────────────────────────
        # Split on sentence-ending punctuation
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) > ResponseFilter.MAX_SENTENCES:
            text = ' '.join(sentences[:ResponseFilter.MAX_SENTENCES])

        # ── Step 5: Trim to max characters ────────────────────────────────
        if len(text) > ResponseFilter.MAX_CHARS:
            # Cut at last complete sentence before limit
            cut = text[:ResponseFilter.MAX_CHARS]
            last_period = max(cut.rfind('.'), cut.rfind('!'), cut.rfind('?'))
            if last_period > 50:   # found a reasonable sentence boundary
                text = cut[:last_period + 1]
            else:
                text = cut.rstrip() + "."

        # ── Step 6: Final cleanup ─────────────────────────────────────────
        text = text.strip()
        if not text:
            return "I am not sure what to say."

        return text
