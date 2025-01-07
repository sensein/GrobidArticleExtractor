# GrobidArticleExtractor

This Python tool extracts content from PDF files using GROBID and organizes it by sections. It provides a structured way
to extract both metadata and content from academic papers and other structured documents.

## Features

- Direct PDF processing using GROBID API
- Metadata extraction (title, authors, abstract, publication date)
- Hierarchical section organization with subsections

## Prerequisites

1. Install GROBID:
   ```bash
   # Using Docker (recommended)
   docker pull lfoppiano/grobid:0.7.3
   docker run -t --rm -p 8070:8070 lfoppiano/grobid:0.7.3
   ```

2. Install Python dependencies:
   ```bash
    pip install poetry
   ```
   ```bash
    poetry install
   ```

## Usage

### Command Line Interface

The tool provides a user-friendly command-line interface for batch processing PDF files:

```bash
# Basic usage (processes PDFs from 'pdfs' directory)
python cli.py

# Process PDFs from a specific directory
python cli.py path/to/pdfs

# Specify custom output directory
python cli.py path/to/pdfs -o path/to/output

# Use custom GROBID server and disable content preview
python cli.py path/to/pdfs --grobid-url http://custom:8070 --no-preview
```

Available options:

```bash
$ python cli.py --help
Usage: cli.py [OPTIONS] [INPUT_FOLDER]

  Process PDF files from INPUT_FOLDER and extract their content using GROBID.

  The extracted content is saved as JSON files in the output directory.
  Each JSON file is named after its source PDF file.

Options:
  -o, --output-dir PATH  Directory to save extracted JSON files (default: output)
  -g, --grobid-url TEXT  GROBID service URL (default: http://localhost:8070)
  --preview / --no-preview
                        Show preview of extracted content (default: True)
  --help                Show this message and exit.

Example:
  python cli.py path/to/pdfs -o path/to/output
```

### Python API Usage

You can also use the tool programmatically in your Python code:

```python
from GrobidArticleExtractor import GrobidArticleExtractor

# Initialize extractor (default GROBID URL: http://localhost:8070)
extractor = GrobidArticleExtractor()

# Process a PDF file
xml_content = extractor.process_pdf("path/to/your/paper.pdf")

if xml_content:
   # Extract and organize content
   result = extractor.extract_content(xml_content)

   # Access metadata
   print(result['metadata'])

   # Access sections
   for section in result['sections']:
      print(section['heading'])
      if 'content' in section:
         print(section['content'])
```

Custom GROBID server:

```python
extractor = GrobidArticleExtractor(grobid_url="http://your-grobid-server:8070")
```

## Output Structure

The extracted content is organized as follows:

```python
{
   'metadata': {
      'title': 'Paper Title',
      'authors': ['Author 1', 'Author 2'],
      'abstract': 'Paper abstract...',
      'publication_date': '2023'
   },
   'sections': [
      {
         'heading': 'Introduction',
         'content': ['Paragraph 1...', 'Paragraph 2...'],
         'subsections': [
            {
               'heading': 'Background',
               'content': ['Subsection content...']
            }
         ]
      }
      # More sections...
   ]
}
```

## Project Structure

The project is organized into two main files:

- `app.py` - Contains the core `GrobidArticleExtractor` class with all the PDF processing and content extraction
  functionality
- `cli.py` - Contains the command-line interface implementation using Click

## Error Handling

The tool includes comprehensive error handling for common scenarios:

- PDF file not found
- GROBID service unavailable
- XML parsing errors
- Invalid content structure

All errors are logged with appropriate messages using Python's logging module.

## Contributing

Feel free to submit issues and enhancement requests!

## License

MIT License
