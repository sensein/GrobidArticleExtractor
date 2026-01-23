# -*- coding: utf-8 -*-
"""Text processing utilities."""

import re
import unicodedata


def clean_junk_characters(text: str) -> str:
    """
    Remove junk characters and symbols like ♠, ♣, ♥, ♦, and other unwanted symbols.
    
    Args:
        text: Raw text to clean
        
    Returns:
        Text with junk characters removed
    """
    if not text:
        return ""
    
    # Common junk characters and symbols to remove
    junk_patterns = [
        r'[♠♣♥♦]',  # Card suit symbols
        r'[•◦▪▫]',  # Bullet points variants
        r'[→←↑↓]',  # Arrow symbols (unless needed)
        r'[✓✗✘]',  # Check/cross symbols
        r'[⋆★☆]',  # Star symbols
        r'[©®™]',  # Copyright symbols (optional, comment out if needed)
        r'[°]',  # Degree symbol (optional)
        r'[\u2000-\u200F]',  # Unicode spaces
        r'[\u2028-\u202F]',  # Unicode line/paragraph separators
        r'[\u205F-\u206F]',  # Unicode invisible characters
        r'[\uFEFF]',  # Zero-width no-break space
    ]
    
    for pattern in junk_patterns:
        text = re.sub(pattern, '', text)
    
    # Remove other control characters except common whitespace
    text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C' or char in ['\n', '\t', ' '])
    
    return text


def clean_text(text: str, preserve_references: bool = True) -> str:
    """
    Clean and format extracted text while preserving references.
    
    Args:
        text: Raw text to clean
        preserve_references: Whether to preserve citation references in text (default: True)
        
    Returns:
        Cleaned text with normalized whitespace, preserved punctuation, and references
    """
    if not text:
        return ""
    
    # First, clean junk characters
    text = clean_junk_characters(text)
    
    # Normalize whitespace (but preserve line breaks if they exist)
    # Replace multiple spaces with single space
    text = re.sub(r'[ \t]+', ' ', text)
    # Normalize line breaks
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    text = re.sub(r'[ \t]*\n[ \t]*', ' ', text)  # Convert single line breaks to spaces
    
    # Remove multiple whitespaces again after line break normalization
    text = re.sub(r'\s+', ' ', text)
    
    # If preserving references, we keep parentheses and common citation patterns
    # Otherwise, we can be more aggressive
    if preserve_references:
        # Preserve parentheses, brackets, and common citation patterns
        # Remove only clearly unwanted characters, but keep citation markers
        # Allow: letters, numbers, spaces, common punctuation, parentheses, brackets
        text = re.sub(r'[^\w\s.,;:!?()\[\]{}"\'-]', '', text)
    else:
        # More aggressive cleaning
        text = re.sub(r'[^\w\s.,;:!?()-]', '', text)
    
    return text.strip()
