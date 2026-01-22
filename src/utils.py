"""Utility functions for the app."""


def format_number(num: float, decimals: int = 2) -> str:
    """Format a number to a string with specified decimal places."""
    return f"{num:.{decimals}f}"


def validate_input(text: str, min_length: int = 1) -> bool:
    """Validate that input text meets minimum length requirement."""
    return len(text.strip()) >= min_length
