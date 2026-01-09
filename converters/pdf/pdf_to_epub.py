from pathlib import Path
from PyPDF2 import PdfReader
from ebooklib import epub


class PDFToEPUBError(Exception):
    """Custom exception for PDF to EPUB conversion"""
    pass


def pdf_to_epub(pdf_path, epub_path, title=None, author=None):
    """
    Convert a single PDF file to EPUB.

    Args:
        pdf_path (str | Path)
        epub_path (str | Path)
        title (str, optional)
        author (str, optional)

    Returns:
        Path: path of generated EPUB
    """

    pdf_path = Path(pdf_path)
    epub_path = Path(epub_path)

    if not pdf_path.exists():
        raise PDFToEPUBError("PDF file does not exist")

    if pdf_path.suffix.lower() != ".pdf":
        raise PDFToEPUBError("Invalid file type. Only PDF allowed")

    epub_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        reader = PdfReader(str(pdf_path))
        book = epub.EpubBook()

        book.set_identifier(pdf_path.stem)
        book.set_title(title or pdf_path.stem)
        book.set_language("en")

        if author:
            book.add_author(author)

        chapters = []

        for page_no, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""

            if not text.strip():
                continue

            chapter = epub.EpubHtml(
                title=f"Page {page_no}",
                file_name=f"page_{page_no:04d}.xhtml",
                lang="en",
            )

            content = "".join(
                f"<p>{line}</p>" for line in text.splitlines() if line.strip()
            )

            chapter.content = f"<h2>Page {page_no}</h2>{content}"

            book.add_item(chapter)
            chapters.append(chapter)

        if not chapters:
            raise PDFToEPUBError("No readable text found in PDF")

        book.spine = ["nav"] + chapters
        book.toc = chapters
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        epub.write_epub(str(epub_path), book)

        return epub_path

    except Exception as e:
        raise PDFToEPUBError(str(e))
