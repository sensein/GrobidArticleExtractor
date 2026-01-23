# -*- coding: utf-8 -*-
"""Logging utilities."""

import logging
from typing import Optional


def setup_logger(name: str = 'GrobidArticleExtractor', level: int = logging.INFO) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        name: Logger name
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger
