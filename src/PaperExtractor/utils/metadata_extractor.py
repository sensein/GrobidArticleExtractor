# -*- coding: utf-8 -*-
"""Metadata extraction utilities from GROBID XML."""

from lxml import etree
from typing import Dict, List
import hashlib
import re
from datetime import datetime

from .text_utils import clean_text
from .xml_parser import get_namespaces, get_xml_id, extract_coordinates


def extract_metadata(root: etree._Element, ns: Dict[str, str]) -> Dict:
    """
    Extract enhanced metadata from the XML content.
    
    Args:
        root: Root XML element
        ns: Namespace mapping
        
    Returns:
        Dictionary containing extracted metadata
    """
    metadata = {}
    
    # Extract title
    title_elem = root.find('.//tei:titleStmt/tei:title', ns)
    if title_elem is not None and title_elem.text:
        metadata['title'] = clean_text(title_elem.text, preserve_references=False)

    # Extract authors with affiliations
    authors = []
    author_details = []
    titleStmt = root.find('.//tei:titleStmt', ns)
    if titleStmt is not None:
        for author in titleStmt.findall('.//tei:author', ns):
            author_info = {}
            persName = author.find('.//tei:persName', ns)
            if persName is not None:
                forename = persName.find('.//tei:forename', ns)
                surname = persName.find('.//tei:surname', ns)
                if forename is not None and surname is not None:
                    author_name = f"{forename.text or ''} {surname.text or ''}".strip()
                else:
                    author_name = ' '.join(persName.itertext()).strip()
                
                if author_name:
                    # Clean author name to remove junk characters
                    author_name = clean_text(author_name, preserve_references=False)
                    author_info['name'] = author_name
                    authors.append(author_name)
            
            # Extract email
            email_elem = author.find('.//tei:email', ns)
            if email_elem is not None and email_elem.text:
                author_info['email'] = clean_text(email_elem.text, preserve_references=False)
            
            # Extract affiliation
            affiliation = author.find('.//tei:affiliation', ns)
            if affiliation is not None:
                org_name = affiliation.find('.//tei:orgName', ns)
                if org_name is not None and org_name.text:
                    author_info['affiliation'] = clean_text(org_name.text, preserve_references=False)
                
                # Extract full affiliation text (including address, country, etc.)
                affiliation_text = ' '.join(affiliation.itertext()).strip()
                if affiliation_text and affiliation_text != author_info.get('affiliation', ''):
                    author_info['affiliation_full'] = clean_text(affiliation_text, preserve_references=False)
            
            if author_info:
                author_details.append(author_info)
        
        # If no authors found in titleStmt, try fileDesc/sourceDesc
        if not authors:
            sourceDesc = root.find('.//tei:fileDesc/tei:sourceDesc', ns)
            if sourceDesc is not None:
                    for author in sourceDesc.findall('.//tei:author', ns):
                        persName = author.find('.//tei:persName', ns)
                        if persName is not None:
                            author_name = ' '.join(persName.itertext()).strip()
                            if author_name:
                                # Clean author name to remove junk characters
                                author_name = clean_text(author_name, preserve_references=False)
                                authors.append(author_name)
                                author_details.append({'name': author_name})
    
    if authors:
        metadata['authors'] = list(dict.fromkeys(authors))
    if author_details:
        metadata['author_details'] = author_details

    # Extract abstract (as string for backward compatibility)
    abstract_elem = root.find('.//tei:abstract', ns)
    if abstract_elem is not None:
        abstract_text = ' '.join(abstract_elem.itertext()).strip()
        if abstract_text:
            metadata['abstract'] = clean_text(abstract_text, preserve_references=True)
    
    # Extract abstract as array (for reference format)
    abstract_paragraphs = []
    if abstract_elem is not None:
        # Extract abstract paragraphs/sentences
        for para in abstract_elem.findall('.//tei:p', ns):
            para_text = clean_text(''.join(para.itertext()), preserve_references=True)
            if para_text:
                abstract_paragraphs.append({
                    'id': len(abstract_paragraphs),
                    'text': para_text,
                    'coords': [],
                    'refs': []
                })
        # If no paragraphs, treat entire abstract as one
        if not abstract_paragraphs and abstract_text:
            abstract_paragraphs.append({
                'id': 0,
                'text': clean_text(abstract_text, preserve_references=True),
                'coords': [],
                'refs': []
            })
    
    if abstract_paragraphs:
        metadata['abstract_array'] = abstract_paragraphs

    # Extract publication date
    date_elem = root.find('.//tei:publicationStmt/tei:date', ns)
    if date_elem is not None:
        if date_elem.text:
            date_text = date_elem.text.strip()
            metadata['publication_date'] = date_text
            
            # Try to extract year
            year_match = re.search(r'\b(19|20)\d{2}\b', date_text)
            if year_match:
                metadata['publication_year'] = int(year_match.group())
            
            # Try to parse as ISO date
            try:
                # Try various date formats
                for fmt in ['%Y-%m-%d', '%Y-%m', '%Y', '%d %b %Y', '%d %B %Y', '%b %d, %Y', '%B %d, %Y']:
                    try:
                        parsed_date = datetime.strptime(date_text, fmt)
                        metadata['publication_date_iso'] = parsed_date.strftime('%Y-%m-%d')
                        if 'publication_year' not in metadata:
                            metadata['publication_year'] = parsed_date.year
                        break
                    except ValueError:
                        continue
            except Exception:
                pass
        
        # Try to get type attribute
        date_type = date_elem.get('type', '')
        if date_type:
            metadata['publication_date_type'] = date_type

    # Extract identifiers (DOI, arXiv, MD5, etc.)
    idno_elems = root.findall('.//tei:idno', ns)
    identifiers = {}
    for idno in idno_elems:
        id_type = idno.get('type', '').lower()
        if idno.text:
            id_value = idno.text.strip()
            if id_type == 'doi':
                identifiers['doi'] = id_value
            elif id_type == 'arxiv':
                identifiers['arxiv'] = id_value
            elif id_type == 'md5':
                identifiers['md5'] = id_value
            else:
                # Store other identifier types
                if 'identifiers' not in identifiers:
                    identifiers['identifiers'] = {}
                identifiers['identifiers'][id_type] = id_value
    
    if identifiers:
        metadata['identifiers'] = identifiers
        # For backward compatibility, also set doi directly if present
        if 'doi' in identifiers:
            metadata['doi'] = identifiers['doi']
        # Use GROBID's MD5 hash if available, otherwise generate our own
        if 'md5' in identifiers:
            metadata['hash_grobid'] = identifiers['md5']

    # Extract journal/publication info
    source_elem = root.find('.//tei:sourceDesc/tei:biblStruct/tei:monogr', ns)
    if source_elem is not None:
        # Journal title
        journal_elem = source_elem.find('.//tei:title[@level="j"]', ns)
        if journal_elem is not None and journal_elem.text:
            metadata['journal'] = clean_text(journal_elem.text)
        
        # Publisher
        publisher_elem = source_elem.find('.//tei:publisher/tei:orgName', ns)
        if publisher_elem is not None and publisher_elem.text:
            metadata['publisher'] = clean_text(publisher_elem.text)
        
        # Volume and issue
        bibl_scope = source_elem.findall('.//tei:biblScope', ns)
        for scope in bibl_scope:
            unit = scope.get('unit', '')
            if unit == 'volume' and scope.text:
                metadata['volume'] = scope.text.strip()
            elif unit == 'issue' and scope.text:
                metadata['issue'] = scope.text.strip()
            elif unit == 'page' and scope.text:
                pages = scope.text.strip()
                metadata['pages'] = pages
                # Try to extract page_start and page_end
                if '-' in pages:
                    parts = pages.split('-')
                    if len(parts) == 2:
                        try:
                            metadata['page_start'] = parts[0].strip()
                            metadata['page_end'] = parts[1].strip()
                        except (ValueError, IndexError):
                            pass

    # Generate hash for biblio (based on title and authors)
    hash_string = ""
    if metadata.get('title'):
        hash_string += metadata['title']
    if metadata.get('authors'):
        hash_string += ''.join(metadata['authors'])
    if hash_string:
        metadata['hash'] = hashlib.md5(hash_string.encode()).hexdigest().upper()

    return metadata
