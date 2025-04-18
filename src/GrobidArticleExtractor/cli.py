# -*- coding: utf-8 -*-
import click
from pathlib import Path

from .app import GrobidArticleExtractor


@click.command()
@click.argument('input_folder', type=click.Path(exists=True, file_okay=False, dir_okay=True), default='pdfs')
@click.option('--output-dir', '-o', type=click.Path(file_okay=False, dir_okay=True), default='output',
              help='Directory to save extracted JSON files (default: output)')
@click.option('--grobid-url', '-g', default='http://localhost:8070',
              help='GROBID service URL (default: http://localhost:8070)')
@click.option('--preview/--no-preview', default=True,
              help='Show preview of extracted content (default: True)')
def main(input_folder, output_dir, grobid_url, preview):
    """Process PDF files from INPUT_FOLDER and extract their content using GROBID.

    The extracted content is saved as JSON files in the output directory.
    Each JSON file is named after its source PDF file.

    Example:
        grobidextractor path/to/pdfs -o path/to/output
    """
    input_folder = Path(input_folder)
    output_dir = Path(output_dir)

    # Create output directory
    output_dir.mkdir(exist_ok=True)
    click.echo(f"Output directory created/verified: {output_dir}")

    # Initialize extractor with custom GROBID URL if provided
    extractor = GrobidArticleExtractor(grobid_url=grobid_url)

    # Process all PDF files in the input folder
    pdf_files = list(input_folder.glob("*.pdf"))
    if not pdf_files:
        click.echo(f"No PDF files found in {input_folder}", err=True)
        return

    click.echo(f"Found {len(pdf_files)} PDF files to process")

    with click.progressbar(pdf_files, label='Processing PDFs') as bar:
        for pdf_path in bar:
            # Process PDF file
            xml_content = extractor.process_pdf(pdf_path)

            if xml_content:
                # Extract and organize content
                result = extractor.extract_content(xml_content)

                # Generate output filename based on input PDF name
                output_path = output_dir / pdf_path.stem
                output_path = output_path.with_suffix('.json')

                # Format response and save to file
                formatted_result = extractor.format_response(
                    result,
                    save_to_file=True,
                    output_path=str(output_path)
                )

                if preview and formatted_result['content']:
                    click.echo(f"\nProcessed: {pdf_path.name}")
                    first_section = next(iter(formatted_result['content'].items()))
                    click.echo(f"Preview of first section ({first_section[0]}):")
                    text = first_section[1].get('text', '')
                    click.echo(text[:200] + '...' if len(text) > 200 else text)
            else:
                click.echo(f"\nFailed to process {pdf_path.name}", err=True)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
