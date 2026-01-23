# -*- coding: utf-8 -*-
"""Utility modules for GrobidArticleExtractor."""

from .text_utils import clean_text, clean_junk_characters
from .xml_parser import TEI_NAMESPACE, get_namespaces, get_xml_id, extract_coordinates
from .logger import setup_logger
from .http_client import GrobidHTTPClient
from .metadata_extractor import extract_metadata
from .content_extractor import (
    extract_figures,
    extract_tables,
    extract_references,
    extract_citations,
)
from .section_processor import process_section, extract_body_text_paragraphs, extract_sections_hierarchy
from .formatters import format_as_json, format_as_markdown, save_formatted_output
from .figure_ocr import enhance_figures_with_ocr, check_gpu_available

__all__ = [
    'clean_text',
    'clean_junk_characters',
    'TEI_NAMESPACE',
    'get_namespaces',
    'get_xml_id',
    'extract_coordinates',
    'setup_logger',
    'GrobidHTTPClient',
    'extract_metadata',
    'extract_figures',
    'extract_tables',
    'extract_references',
    'extract_citations',
    'process_section',
    'extract_body_text_paragraphs',
    'extract_sections_hierarchy',
    'format_as_json',
    'format_as_markdown',
    'save_formatted_output',
    'enhance_figures_with_ocr',
    'check_gpu_available',
]
