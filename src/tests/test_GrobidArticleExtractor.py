# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# DISCLAIMER: This software is provided "as is" without any warranty,
# express or implied, including but not limited to the warranties of
# merchantability, fitness for a particular purpose, and non-infringement.
#
# In no event shall the authors or copyright holders be liable for any
# claim, damages, or other liability, whether in an action of contract,
# tort, or otherwise, arising from, out of, or in connection with the
# software or the use or other dealings in the software.
# -----------------------------------------------------------------------------

# @Author  : Tek Raj Chhetri
# @Email   : tekraj@mit.edu
# @Web     : https://tekrajchhetri.com/
# @File    : test_GrobidArticleExtractor.py.py
# @Software: PyCharm

import pytest
from pathlib import Path
import json
from unittest.mock import Mock, patch, mock_open
from app import GrobidArticleExtractor
from cli import main

# Sample test data
SAMPLE_XML_RESPONSE = '''<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <teiHeader>
        <fileDesc>
            <titleStmt>
                <title>Test Paper Title</title>
                <author>
                    <persName>
                        <forename>John</forename>
                        <surname>Doe</surname>
                    </persName>
                </author>
            </titleStmt>
            <publicationStmt>
                <date>2023</date>
            </publicationStmt>
        </fileDesc>
        <profileDesc>
            <abstract>This is a test abstract.</abstract>
        </profileDesc>
    </teiHeader>
    <text>
        <body>
            <div>
                <head>Introduction</head>
                <p>This is the introduction paragraph.</p>
                <div>
                    <head>Background</head>
                    <p>This is background information.</p>
                </div>
            </div>
            <div>
                <head>References</head>
                <p>Reference 1</p>
            </div>
        </body>
    </text>
</TEI>'''


@pytest.fixture
def extractor():
    """Create a GrobidArticleExtractor instance for testing."""
    return GrobidArticleExtractor(grobid_url="http://test-grobid:8070")


@pytest.fixture
def mock_response():
    """Create a mock response for requests."""
    mock = Mock()
    mock.status_code = 200
    mock.text = SAMPLE_XML_RESPONSE
    return mock


def test_init():
    """Test GrobidArticleExtractor initialization."""
    extractor = GrobidArticleExtractor()
    assert extractor.grobid_url == "http://localhost:8070"
    assert extractor.ns == {'tei': 'http://www.tei-c.org/ns/1.0'}

    custom_url = "http://custom:8070"
    extractor = GrobidArticleExtractor(grobid_url=custom_url)
    assert extractor.grobid_url == custom_url


def test_clean_text(extractor):
    """Test text cleaning functionality."""
    dirty_text = "  This   is  a\n\ntest   text  with   spaces  "
    clean_text = extractor._clean_text(dirty_text)
    assert clean_text == "This is a test text with spaces"


@patch('requests.post')
def test_process_pdf_success(mock_post, extractor, mock_response):
    """Test successful PDF processing."""
    mock_post.return_value = mock_response

    with patch('pathlib.Path.exists', return_value=True), \
            patch('builtins.open', mock_open(read_data=b'fake pdf content')):
        result = extractor.process_pdf("test.pdf")

    assert result == SAMPLE_XML_RESPONSE
    mock_post.assert_called_once()


@patch('requests.post')
def test_process_pdf_failure(mock_post, extractor):
    """Test PDF processing failure."""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_post.return_value = mock_response

    with patch('builtins.open', mock_open(read_data=b'fake pdf content')):
        result = extractor.process_pdf("test.pdf")

    assert result is None


def test_extract_metadata(extractor):
    """Test metadata extraction from XML."""
    # Clean up the sample XML by removing extra whitespace
    clean_xml = '\n'.join(line.strip() for line in SAMPLE_XML_RESPONSE.splitlines())
    result = extractor.extract_content(clean_xml)
    metadata = result['metadata']

    assert metadata['title'] == "Test Paper Title"
    assert len(metadata['authors']) == 1
    assert metadata['authors'][0].strip() == "John Doe"
    assert metadata['abstract'] == "This is a test abstract"
    assert metadata['publication_date'] == "2023"


def test_extract_content_structure(extractor):
    """Test content extraction and structure."""
    result = extractor.extract_content(SAMPLE_XML_RESPONSE)

    # Check basic structure
    assert 'metadata' in result
    assert 'sections' in result

    # Check sections
    sections = result['sections']
    assert len(sections) == 1  # References section should be skipped

    # Check first section
    first_section = sections[0]
    assert first_section['heading'] == "Introduction"
    assert "This is the introduction paragraph" in first_section['content'][0]

    # Check subsection
    assert len(first_section['subsections']) == 1
    subsection = first_section['subsections'][0]
    assert subsection['heading'] == "Background"
    assert "This is background information" in subsection['content'][0]


def test_format_response(extractor):
    """Test response formatting."""
    # First extract content
    content = extractor.extract_content(SAMPLE_XML_RESPONSE)

    # Then format it
    formatted = extractor.format_response(content)

    # Check structure
    assert 'metadata' in formatted
    assert 'content' in formatted

    # Check content formatting
    assert 'Introduction' in formatted['content']
    intro_section = formatted['content']['Introduction']
    assert 'text' in intro_section
    assert 'subsections' in intro_section
    assert 'Background' in intro_section['subsections']


@pytest.fixture
def setup_test_environment(tmp_path):
    """Setup test environment with mock PDF files and output directory."""
    # Create input directory with test PDFs
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()

    # Create some test PDF files
    (pdf_dir / "test1.pdf").write_bytes(b"fake pdf 1")
    (pdf_dir / "test2.pdf").write_bytes(b"fake pdf 2")

    # Create output directory
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    return pdf_dir, output_dir


from click.testing import CliRunner


@patch('requests.post')
def test_main_function(mock_post, setup_test_environment, mock_response):
    """Test the main function with multiple PDF files."""
    pdf_dir, output_dir = setup_test_environment
    mock_post.return_value = mock_response

    # Mock Path.exists to return True for PDF files
    def mock_exists(path):
        return str(path).endswith('.pdf') or Path(path).exists()

    runner = CliRunner()

    with patch('pathlib.Path.exists', side_effect=mock_exists), \
            patch('builtins.open', mock_open(read_data=b'fake pdf content')):
        # Test with default options
        result = runner.invoke(main, [str(pdf_dir)])
        assert result.exit_code == 0
        assert "Found 2 PDF files to process" in result.output
        assert mock_post.call_count == 2  # Should be called once for each PDF

        # Reset mock for next test
        mock_post.reset_mock()

        # Test with custom options
        result = runner.invoke(main, [
            str(pdf_dir),
            '--output-dir', str(output_dir),
            '--grobid-url', 'http://custom:8070',
            '--no-preview'
        ])
        assert result.exit_code == 0
        assert "Found 2 PDF files to process" in result.output
        assert "Preview" not in result.output  # Preview should be disabled
        assert mock_post.call_count == 2


if __name__ == '__main__':
    pytest.main([__file__])
