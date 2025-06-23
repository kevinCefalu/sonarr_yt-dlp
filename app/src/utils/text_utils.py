"""Text processing utilities."""
import re
import logging


logger = logging.getLogger(__name__)


def escape_title_for_search(title: str) -> str:
    """Escape and format title for YT-DLP search matching.

    This function processes episode titles to make them more suitable
    for matching against video titles on platforms like YouTube.

    Args:
        title: The original episode title.

    Returns:
        Processed title for search matching.
    """
    if not title:
        return ""

    # Convert to uppercase for case-insensitive matching
    processed = title.upper()

    # Replace various quote characters with standard ones
    quote_replacements = {
        ''': "'",
        ''': "'",
        '"': '"',
        '"': '"',
    }

    for old_quote, new_quote in quote_replacements.items():
        processed = processed.replace(old_quote, new_quote)

    # Escape special regex characters
    processed = re.escape(processed)

    # Make "AND" flexible to match both "AND" and "&"
    processed = processed.replace(r'\ AND\ ', r'\ (AND|&)\ ')

    # Make punctuation optional for more flexible matching
    punctuation_optional = {
        "'": r"([']?)",      # Optional apostrophe
        ",": r"([,]?)",      # Optional comma
        "!": r"([!]?)",      # Optional exclamation mark
        r"\.": r"([.]?)",    # Optional period
        r"\?": r"([?]?)",    # Optional question mark
        ":": r"([:]?)",      # Optional colon
    }

    for punct, replacement in punctuation_optional.items():
        processed = processed.replace(punct, replacement)

    # Handle possessive apostrophe (must be last due to question mark)
    processed = re.sub(r'S\\', r"([']?)S\\", processed)

    logger.debug("Title '%s' escaped to '%s'", title, processed)
    return processed


def apply_regex_transformation(text: str, pattern: str, replacement: str) -> str:
    """Apply regex transformation to text.

    Args:
        text: The text to transform.
        pattern: The regex pattern to match.
        replacement: The replacement string.

    Returns:
        Transformed text.
    """
    try:
        result = re.sub(pattern, replacement, text)
        if result != text:
            logger.debug("Regex transform: '%s' -> '%s' (pattern: %s)",
                        text, result, pattern)
        return result
    except re.error as e:
        logger.error("Invalid regex pattern '%s': %s", pattern, e)
        return text
