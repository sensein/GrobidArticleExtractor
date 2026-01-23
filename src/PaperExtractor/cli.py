# -*- coding: utf-8 -*-
import click
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Tuple, Optional, Union

from .app import PaperExtractor
from . import __version__


@click.command()
@click.option('--version', '-V', is_flag=True, help='Show the version and exit.')
@click.argument('input_path', type=click.Path(exists=False, file_okay=True, dir_okay=True), required=False, default='pdfs')
@click.option('--output', '-o', 'output_path', type=click.Path(file_okay=True, dir_okay=True), default=None,
              help='Output file path (for single PDF) or directory (for multiple PDFs). Default: output directory or input filename with .json/.md extension')
@click.option('--grobid-url', '-g', default='http://localhost:8070',
              help='GROBID service URL (default: http://localhost:8070)')
@click.option('--format', '-f', 'output_format', type=click.Choice(['json', 'markdown', 'xml'], case_sensitive=False),
              default='json', help='Output format: json, markdown, or xml (default: json)')
@click.option('--service', '-s', type=click.Choice(['fulltext', 'header', 'references'], case_sensitive=False),
              default='fulltext', help='GROBID service to use (default: fulltext)')
@click.option('--include-citations/--no-citations', default=False,
              help='Include in-text citation information (default: False)')
@click.option('--segment-sentences/--no-segment-sentences', default=False,
              help='Segment paragraphs into individual sentences (default: False)')
@click.option('--no-figures', is_flag=True, default=False,
              help='Exclude figures from extraction')
@click.option('--no-tables', is_flag=True, default=False,
              help='Exclude tables from extraction')
@click.option('--no-references', is_flag=True, default=False,
              help='Exclude references from extraction')
@click.option('--section-level', is_flag=True, default=False,
              help='Extract content organized by sections (default: paragraph-level)')
@click.option('--no-figure-ocr', is_flag=True, default=False,
              help='Disable OCR processing for figures (default: OCR enabled)')
@click.option('--preview/--no-preview', default=True,
              help='Show preview of extracted content (default: True)')
@click.option('--timeout', type=int, default=300,
              help='Request timeout in seconds (default: 300)')
@click.option('--max-retries', type=int, default=3,
              help='Maximum number of retry attempts (default: 3)')
@click.option('--concurrency', '-c', type=int, default=1,
              help='Number of parallel workers for processing PDFs (default: 1, sequential)')
def main(input_path, output_path, grobid_url, output_format, service, include_citations,
         segment_sentences, no_figures, no_tables, no_references, section_level, no_figure_ocr, preview, timeout, max_retries, concurrency, version):
    """Process PDF file(s) and extract their content using GROBID.

    INPUT_PATH can be a single PDF file or a directory containing PDF files.
    The extracted content is saved as JSON or Markdown files.

    Examples:
        # Process a single PDF file
        paperextractor file.pdf -o output.json
        paperextractor file.pdf -o output/  # Save to directory
        
        # Process all PDFs in a directory
        paperextractor pdfs/ -o output/ --format markdown
        paperextractor pdfs/ --service header --include-citations
    """
    # Handle version flag - check this first before any other processing
    if version:
        click.echo(f"paperextractor, version {__version__}")
        return
    
    # Validate input path exists (only if not showing version)
    input_path = Path(input_path) if input_path else Path('pdfs')
    if not input_path.exists():
        click.echo(f"Error: Path '{input_path}' does not exist.", err=True)
        click.echo("Use 'paperextractor --help' for usage information.", err=True)
        return

    # Initialize extractor with custom GROBID URL and options
    extractor = PaperExtractor(
        grobid_url=grobid_url,
        timeout=timeout,
        max_retries=max_retries
    )

    # Determine GROBID service endpoint
    service_map = {
        'fulltext': 'processFulltextDocument',
        'header': 'processHeaderDocument',
        'references': 'processReferences'
    }
    service_endpoint = service_map[service]

    # Check if input is a single file or directory
    if input_path.is_file():
        # Single PDF file
        if not input_path.suffix.lower() == '.pdf':
            click.echo(f"Error: '{input_path}' is not a PDF file.", err=True)
            return
        
        pdf_files = [input_path]
        
        # Determine output path for single file
        if output_path:
            output_path = Path(output_path)
            # Check if it's an existing directory or has no extension (treat as directory)
            if output_path.exists() and output_path.is_dir():
                # Output is a directory, use PDF filename
                output_file = output_path / input_path.stem
                if output_format == 'markdown':
                    output_file = output_file.with_suffix('.md')
                elif output_format == 'xml':
                    output_file = output_file.with_suffix('.xml')
                else:
                    output_file = output_file.with_suffix('.json')
            elif not output_path.suffix or output_path.suffix not in ['.json', '.md', '.xml']:
                # No extension or unknown extension, treat as directory
                output_path.mkdir(parents=True, exist_ok=True)
                output_file = output_path / input_path.stem
                if output_format == 'markdown':
                    output_file = output_file.with_suffix('.md')
                elif output_format == 'xml':
                    output_file = output_file.with_suffix('.xml')
                else:
                    output_file = output_file.with_suffix('.json')
            else:
                # Output is a file path
                output_file = output_path
                # Ensure correct extension
                if output_format == 'markdown' and output_file.suffix != '.md':
                    output_file = output_file.with_suffix('.md')
                elif output_format == 'xml' and output_file.suffix != '.xml':
                    output_file = output_file.with_suffix('.xml')
                elif output_format == 'json' and output_file.suffix != '.json':
                    output_file = output_file.with_suffix('.json')
        else:
            # No output specified, use input filename with appropriate extension
            output_file = input_path.parent / input_path.stem
            if output_format == 'markdown':
                output_file = output_file.with_suffix('.md')
            elif output_format == 'xml':
                output_file = output_file.with_suffix('.xml')
            else:
                output_file = output_file.with_suffix('.json')
        
        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        click.echo(f"Processing: {input_path.name}")
        click.echo(f"Output: {output_file}")
        click.echo(f"Using service: {service}, output format: {output_format}")
        
        # For XML output, pass directly to process_pdf and save
        if output_format == 'xml':
            result = extractor.process_pdf(
                input_path,
                service=service_endpoint,
                output_format="xml"
            )
            if result:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result)
                click.echo(f"Successfully processed {input_path.name}")
                if preview:
                    preview_text = result[:300]
                    click.echo(f"Preview (first 300 chars):\n{preview_text}...")
            else:
                click.echo(f"Failed to process {input_path.name}", err=True)
                return
        else:
            # Process single PDF with full extraction enabled by default
            result = extractor.process_pdf(
                input_path,
                service=service_endpoint,
                output_format="dict",
                include_figures=not no_figures,
                include_tables=not no_tables,
                include_references=not no_references,
                include_citations=include_citations,
                segment_sentences=segment_sentences,
                section_level=section_level,
                enable_figure_ocr=not no_figure_ocr  # Default: True (full extraction)
            )
            
            if result:
                formatted_result = extractor.format_response(
                    result,
                    save_to_file=True,
                    output_path=str(output_file),
                    output_format=output_format
                )
                click.echo(f"Successfully processed {input_path.name}")
                if preview and formatted_result:
                    if isinstance(formatted_result, dict) and formatted_result.get('content'):
                        first_section = next(iter(formatted_result['content'].items()))
                        click.echo(f"Preview of first section ({first_section[0]}):")
                        text = first_section[1].get('text', '')
                        click.echo(text[:200] + '...' if len(text) > 200 else text)
                    elif isinstance(formatted_result, str):
                        preview_text = formatted_result[:300]
                        click.echo(f"Preview (first 300 chars):\n{preview_text}...")
            else:
                click.echo(f"Failed to process {input_path.name}", err=True)
                return
        
    elif input_path.is_dir():
        # Directory of PDF files
        output_dir = Path(output_path) if output_path else Path('output')
        output_dir.mkdir(parents=True, exist_ok=True)
        click.echo(f"Output directory: {output_dir}")

        # Process all PDF files in the input directory
        pdf_files = list(input_path.glob("*.pdf"))
        if not pdf_files:
            click.echo(f"No PDF files found in {input_path}", err=True)
            return

        click.echo(f"Found {len(pdf_files)} PDF files to process")
        click.echo(f"Using service: {service}, output format: {output_format}")

        def process_single_pdf(pdf_path: Path) -> Tuple[Path, Optional[Union[dict, str]], Optional[str]]:
            """Process a single PDF file and return results."""
            # Create a new extractor instance for thread safety
            thread_extractor = PaperExtractor(
                grobid_url=grobid_url,
                timeout=timeout,
                max_retries=max_retries
            )
            
            # For XML output, pass directly to process_pdf
            if output_format == 'xml':
                result = thread_extractor.process_pdf(
                    pdf_path,
                    service=service_endpoint,
                    output_format="xml"
                )
            else:
                # Process PDF file with structured output (full extraction by default)
                result = thread_extractor.process_pdf(
                    pdf_path,
                    service=service_endpoint,
                    output_format="dict",
                    include_figures=not no_figures,
                    include_tables=not no_tables,
                    include_references=not no_references,
                    include_citations=include_citations,
                    segment_sentences=segment_sentences,
                    section_level=section_level,
                    enable_figure_ocr=not no_figure_ocr  # Default: True (full extraction)
                )
            
            if result:
                # Generate output filename based on input PDF name
                output_file = output_dir / pdf_path.stem
                if output_format == 'markdown':
                    output_file = output_file.with_suffix('.md')
                elif output_format == 'xml':
                    output_file = output_file.with_suffix('.xml')
                else:
                    output_file = output_file.with_suffix('.json')
                
                # For XML, result is already a string, save directly
                if output_format == 'xml':
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(result)
                    return (pdf_path, result, None)
                else:
                    # Format response and save to file
                    formatted_result = thread_extractor.format_response(
                        result,
                        save_to_file=True,
                        output_path=str(output_file),
                        output_format=output_format
                    )
                    return (pdf_path, formatted_result, None)
            else:
                return (pdf_path, None, f"Failed to process {pdf_path.name}")

        # Process PDFs with optional parallelization
        if concurrency > 1:
            click.echo(f"Processing {len(pdf_files)} PDFs with {concurrency} parallel workers...")
            successful = 0
            failed = 0
            
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                # Submit all tasks
                future_to_pdf = {
                    executor.submit(process_single_pdf, pdf_path): pdf_path 
                    for pdf_path in pdf_files
                }
                
                # Process completed tasks with progress bar
                with click.progressbar(
                    length=len(pdf_files),
                    label='Processing PDFs'
                ) as bar:
                    for future in as_completed(future_to_pdf):
                        pdf_path, formatted_result, error = future.result()
                        bar.update(1)
                        
                        if error:
                            failed += 1
                            if preview:
                                click.echo(f"\n{error}", err=True)
                        else:
                            successful += 1
                            if preview and formatted_result:
                                click.echo(f"\nProcessed: {pdf_path.name}")
                                if isinstance(formatted_result, dict) and formatted_result.get('content'):
                                    first_section = next(iter(formatted_result['content'].items()))
                                    click.echo(f"Preview of first section ({first_section[0]}):")
                                    text = first_section[1].get('text', '')
                                    click.echo(text[:200] + '...' if len(text) > 200 else text)
                                elif isinstance(formatted_result, str):
                                    preview_text = formatted_result[:300]
                                    click.echo(f"Preview (first 300 chars):\n{preview_text}...")
            
            click.echo(f"\nCompleted: {successful} successful, {failed} failed")
        else:
            # Sequential processing (original behavior)
            with click.progressbar(pdf_files, label='Processing PDFs') as bar:
                for pdf_path in bar:
                    _, formatted_result, error = process_single_pdf(pdf_path)
                    
                    if error:
                        click.echo(f"\n{error}", err=True)
                    elif preview and formatted_result:
                        click.echo(f"\nProcessed: {pdf_path.name}")
                        if isinstance(formatted_result, dict) and formatted_result.get('content'):
                            first_section = next(iter(formatted_result['content'].items()))
                            click.echo(f"Preview of first section ({first_section[0]}):")
                            text = first_section[1].get('text', '')
                            click.echo(text[:200] + '...' if len(text) > 200 else text)
                        elif isinstance(formatted_result, str):
                            preview_text = formatted_result[:300]
                            click.echo(f"Preview (first 300 chars):\n{preview_text}...")


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
