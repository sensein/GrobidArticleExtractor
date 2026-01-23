# -*- coding: utf-8 -*-
"""HTTP client utilities for GROBID API requests."""

import time
import logging
from pathlib import Path
from typing import Optional, Dict, Union
import requests


class GrobidHTTPClient:
    """HTTP client for GROBID API with retry logic."""
    
    def __init__(
        self,
        base_url: str,
        timeout: int = 300,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize GROBID HTTP client.
        
        Args:
            base_url: Base URL of GROBID service
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            logger: Logger instance (optional)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logger or logging.getLogger(__name__)
    
    def build_params(
        self,
        generate_ids: bool = False,
        consolidate_citations: bool = False,
        include_raw_citations: bool = False,
        include_raw_affiliations: bool = False,
        tei_coordinates: bool = False,
        segment_sentences: bool = False
    ) -> Dict[str, str]:
        """
        Build GROBID API parameters.
        
        Args:
            generate_ids: Generate IDs for elements
            consolidate_citations: Consolidate citations
            include_raw_citations: Include raw citations
            include_raw_affiliations: Include raw affiliations
            tei_coordinates: Include coordinates in TEI output
            segment_sentences: Segment sentences
            
        Returns:
            Dictionary of API parameters
        """
        params = {}
        if generate_ids:
            params['generateId'] = '1'
        if consolidate_citations:
            params['consolidateCitations'] = '1'
        if include_raw_citations:
            params['includeRawCitations'] = '1'
        if include_raw_affiliations:
            params['includeRawAffiliations'] = '1'
        if tei_coordinates:
            # GROBID expects teiCoordinates as space-separated string
            params['teiCoordinates'] = 's head note ref figure table'
        if segment_sentences:
            params['segmentSentences'] = '1'
        
        return params
    
    def post_pdf(
        self,
        pdf_path: Union[str, Path],
        service: str,
        params: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """
        Post PDF file to GROBID service with retry logic.
        
        Args:
            pdf_path: Path to PDF file
            service: GROBID service endpoint
            params: Optional API parameters
            
        Returns:
            Response text if successful, None otherwise
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            self.logger.error(f"PDF file not found: {pdf_path}")
            return None
        
        params = params or {}
        
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                with open(pdf_path, 'rb') as pdf_file:
                    files = {'input': (pdf_path.name, pdf_file, 'application/pdf')}
                    response = requests.post(
                        f"{self.base_url}/api/{service}",
                        files=files,
                        params=params,
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        return response.text
                    elif response.status_code == 503:
                        # Service unavailable, retry
                        if attempt < self.max_retries - 1:
                            wait_time = self.retry_delay * (2 ** attempt)
                            self.logger.warning(
                                f"Service unavailable (503), retrying in {wait_time}s "
                                f"(attempt {attempt + 1}/{self.max_retries})"
                            )
                            time.sleep(wait_time)
                            continue
                    else:
                        self.logger.error(
                            f"GROBID processing failed with status code: {response.status_code}"
                        )
                        return None
                        
            except requests.exceptions.Timeout as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    self.logger.warning(
                        f"Request timeout, retrying in {wait_time}s "
                        f"(attempt {attempt + 1}/{self.max_retries})"
                    )
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Request timeout after {self.max_retries} attempts: {e}")
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    self.logger.warning(
                        f"Request error, retrying in {wait_time}s "
                        f"(attempt {attempt + 1}/{self.max_retries}): {e}"
                    )
                    time.sleep(wait_time)
                else:
                    self.logger.error(
                        f"Error communicating with GROBID service after {self.max_retries} attempts: {e}"
                    )
            except Exception as e:
                self.logger.error(f"Unexpected error processing PDF: {e}")
                return None
        
        return None
