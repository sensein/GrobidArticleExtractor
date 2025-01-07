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
# @Software: PyCharm


from lxml import etree
from typing import Dict, List, Optional, Union
import requests
import logging
from pathlib import Path
import re
import json

class GrobidArticleExtractor:
    """A class to handle PDF content extraction using GROBID and organize content by sections."""
    
    def __init__(self, grobid_url: str = "http://localhost:8070"):
        """
        Initialize the GROBID PDF extractor.
        
        Args:
            grobid_url (str): URL of the GROBID service
        """
        self.grobid_url = grobid_url
        self.logger = self._setup_logger()
        self.ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

    def _setup_logger(self) -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.getLogger('GrobidArticleExtractor')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

    def process_pdf(self, pdf_path: Union[str, Path]) -> Optional[str]:
        """
        Process PDF file using GROBID service.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Optional[str]: XML content if successful, None otherwise
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            self.logger.error(f"PDF file not found: {pdf_path}")
            return None

        try:
            with open(pdf_path, 'rb') as pdf_file:
                files = {'input': (pdf_path.name, pdf_file, 'application/pdf')}
                response = requests.post(
                    f"{self.grobid_url}/api/processFulltextDocument",
                    files=files,
                    timeout=300
                )
                
                if response.status_code == 200:
                    return response.text
                else:
                    self.logger.error(
                        f"GROBID processing failed with status code: {response.status_code}"
                    )
                    return None
                    
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error communicating with GROBID service: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error processing PDF: {e}")
            return None

    def _clean_text(self, text: str) -> str:
        """Clean and format extracted text."""
        # Remove multiple whitespaces
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters while preserving necessary punctuation
        text = re.sub(r'[^\w\s.,;:!?()-]', '', text)
        return text.strip()

    def _extract_metadata(self, root: etree._Element) -> Dict[str, str]:
        """Extract metadata from the XML content."""
        metadata = {}
        
        # Extract title
        title_elem = root.find('.//tei:titleStmt/tei:title', self.ns)
        if title_elem is not None and title_elem.text:
            metadata['title'] = self._clean_text(title_elem.text)

        # Extract authors from titleStmt only (to avoid references authors)
        authors = []
        titleStmt = root.find('.//tei:titleStmt', self.ns)
        if titleStmt is not None:
            for author in titleStmt.findall('.//tei:author', self.ns):
                persName = author.find('.//tei:persName', self.ns)
                if persName is not None:
                    author_name = ' '.join(persName.itertext()).strip()
                    if author_name:
                        authors.append(author_name)
            
            # If no authors found in titleStmt, try fileDesc/sourceDesc
            if not authors:
                sourceDesc = root.find('.//tei:fileDesc/tei:sourceDesc', self.ns)
                if sourceDesc is not None:
                    for author in sourceDesc.findall('.//tei:author', self.ns):
                        persName = author.find('.//tei:persName', self.ns)
                        if persName is not None:
                            author_name = ' '.join(persName.itertext()).strip()
                            if author_name:
                                authors.append(author_name)
        
        if authors:
            metadata['authors'] = list(dict.fromkeys(authors))  # Remove duplicates while preserving order

        # Extract abstract
        abstract_elem = root.find('.//tei:abstract', self.ns)
        if abstract_elem is not None:
            abstract_text = ' '.join(abstract_elem.itertext()).strip()
            if abstract_text:
                metadata['abstract'] = self._clean_text(abstract_text)

        # Extract publication date
        date_elem = root.find('.//tei:publicationStmt/tei:date', self.ns)
        if date_elem is not None and date_elem.text:
            metadata['publication_date'] = date_elem.text.strip()

        return metadata

    def _should_skip_section(self, section_elem: etree._Element) -> bool:
        """
        Check if a section should be skipped (e.g., references, bibliography).
        
        Args:
            section_elem: The section element to check
            
        Returns:
            bool: True if section should be skipped, False otherwise
        """
        # Check section heading
        head_elem = section_elem.find(f'tei:head', self.ns)
        if head_elem is not None and head_elem.text:
            heading = head_elem.text.lower().strip()
            skip_keywords = {'references', 'bibliography', 'acknowledgments', 'acknowledgements'}
            return any(keyword in heading for keyword in skip_keywords)
        return False

    def _process_section(self, section_elem: etree._Element, level: int = 1) -> Optional[Dict[str, Union[str, List[str], List[Dict]]]]:
        """
        Process a section element recursively to handle nested sections.
        
        Args:
            section_elem: The section element to process
            level: Current section nesting level
            
        Returns:
            Optional[Dict]: Dictionary containing section content and subsections, or None if section should be skipped
        """
        # Skip references and similar sections
        if self._should_skip_section(section_elem):
            return None

        section_data: Dict[str, Union[str, List[str], List[Dict]]] = {
            'heading': '',
            'content': [],
            'subsections': []
        }
        
        # Process section heading
        head_elem = section_elem.find(f'tei:head', self.ns)
        section_data['heading'] = (
            self._clean_text(head_elem.text) if head_elem is not None and head_elem.text 
            else f"Untitled Section {level}"
        )

        # Process paragraphs and other content
        for elem in section_elem:
            if elem.tag == f"{{{self.ns['tei']}}}p":
                text_content = self._clean_text(''.join(elem.itertext()))
                if text_content:
                    section_data['content'].append(text_content)
            elif elem.tag == f"{{{self.ns['tei']}}}div" or elem.tag == f"{{{self.ns['tei']}}}section":
                subsection = self._process_section(elem, level + 1)
                if subsection:
                    section_data['subsections'].append(subsection)

        # Return None if section is empty
        if not section_data['content'] and not section_data['subsections']:
            return None

        return section_data

    def extract_content(self, xml_content: str) -> Dict[str, Union[Dict[str, Union[str, List[str]]], List[Dict]]]:
        """
        Extract and organize content from GROBID XML output.
        
        Args:
            xml_content: XML string from GROBID
            
        Returns:
            Dict containing metadata and organized content, excluding references and similar sections
        """
        try:
            root = etree.fromstring(xml_content.encode('utf-8'))
            
            # Initialize result structure
            result = {
                'metadata': {
                    'title': '',
                    'authors': [],
                    'abstract': '',
                    'publication_date': ''
                },
                'sections': []
            }

            # Extract metadata
            metadata = self._extract_metadata(root)
            result['metadata'].update(metadata)

            # Process main text body
            body = root.find('.//tei:body', self.ns)
            if body is None:
                self.logger.warning("No body found in the XML content")
                return result

            # Process each top-level section
            xpath_expr = './/tei:div[parent::tei:body] | .//tei:section[parent::tei:body]'
            for div in root.xpath(xpath_expr, namespaces=self.ns):
                section_data = self._process_section(div)
                if section_data:
                    result['sections'].append(section_data)

            return result

        except etree.ParseError as e:
            self.logger.error(f"Error parsing XML content: {e}")
            return {'metadata': {}, 'sections': []}
        except Exception as e:
            self.logger.error(f"Unexpected error processing XML content: {e}")
            return {'metadata': {}, 'sections': []}

    def format_response(self, result: Dict, save_to_file: bool = False, output_path: Optional[str] = None) -> Dict[str, Union[Dict[str, Union[str, List[str]]], Dict[str, str]]]:
        """
        Format the extraction result into a clean dictionary structure.
        
        Args:
            result: Raw extraction result
            
        Returns:
            Dict: Formatted response with metadata and section content
        """
        formatted_response = {
            'metadata': result['metadata'],
            'content': {}
        }
        
        def process_section(section: Dict) -> Dict[str, Union[str, Dict]]:
            section_content = {
                'text': '\n'.join(section['content']) if 'content' in section else ''
            }
            
            if 'subsections' in section:
                section_content['subsections'] = {}
                for subsection in section['subsections']:
                    section_content['subsections'][subsection['heading']] = process_section(subsection)
            
            return section_content
        
        # Process all sections
        for section in result['sections']:
            formatted_response['content'][section['heading']] = process_section(section)
        
        # Save to file if requested
        if save_to_file:
            output_path = output_path or "extracted_content.json"
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(formatted_response, f, indent=2, ensure_ascii=False)
                self.logger.info(f"Saved extracted content to {output_path}")
            except Exception as e:
                self.logger.error(f"Error saving to file: {e}")

        return formatted_response

