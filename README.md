# GrobidArticleExtractor

This Python tool extracts content from PDF files using GROBID and organizes it by sections. It provides a structured way
to extract both metadata and content from academic papers and other structured documents.

## Features

- Direct PDF processing using GROBID API
- Metadata extraction (title, authors, abstract, publication date)
- Hierarchical section organization with subsections

## Prerequisites

1. Start GROBID Service:

   ```bash 
   docker pull lfoppiano/grobid:0.8.0
   docker run --init -p 8070:8070 -e JAVA_OPTS="-XX:+UseZGC" lfoppiano/grobid:0.8.0
   ```
   `JAVA_OPTS="-XX:+UseZGC"` helps to resolve the following error in mac os.
    ```bash
    [thread 44 also had an error]
    
    A fatal error has been detected by the Java Runtime Environment:
    
    SIGSEGV (0xb) at pc=0x00007ffffef8ad07, pid=8, tid=47
    
    JRE version: OpenJDK Runtime Environment (17.0.2+8) (build 17.0.2+8-86)
    Java VM: OpenJDK 64-Bit Server VM (17.0.2+8-86, mixed mode, sharing, tiered, compressed oops, compressed class ptrs, parallel gc, linux-amd64)
    Problematic frame:
    [thread 41 also had an error]
    [thread 45 also had an error]
    [thread 46 also had an error]
    ```

2. Installation :

   Install this package via :

   ```sh
   pip install GrobidArticleExtractor
   ```

   Or get the newest development version via:

   ```sh
   pip install git+https://github.com/sensein/GrobidArticleExtractor.git
   ```

   Note: If upgrading from a previous version, you may need to reinstall the package to ensure the CLI command is
   properly installed:
   ```sh
   pip uninstall GrobidArticleExtractor
   pip install GrobidArticleExtractor
   ```

## Usage

### Command Line Interface

The tool provides a user-friendly command-line interface for batch processing PDF files:

```bash
# Basic usage (processes PDFs from 'pdfs' directory)
grobidextractor

# Process PDFs from a specific directory
grobidextractor path/to/pdfs

# Specify custom output directory
grobidextractor path/to/pdfs -o path/to/output

# Use custom GROBID server and disable content preview
grobidextractor path/to/pdfs --grobid-url http://custom:8070 --no-preview
```

Available options:

```bash
$ grobidextractor --help
Usage: grobidextractor [OPTIONS] [INPUT_FOLDER]  

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
  grobidextractor path/to/pdfs -o path/to/output
```

### Python API Usage

You can also use the tool programmatically in your Python code:

```python
from GrobidArticleExtractor.app import GrobidArticleExtractor

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
