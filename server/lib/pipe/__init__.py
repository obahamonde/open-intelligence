from .load_docx import DocxLoader
from .load_html import HTMLoader
from .load_jsonl import JsonLoader
from .load_markdown import MarkdownLoader
from .load_pdf import PdfLoader
from .load_pptx import PptxLoader
from .load_xlsx import ExcelLoader
from ._base import Artifact

__all__ = [
    "DocxLoader",
    "PdfLoader",
    "PptxLoader",
    "ExcelLoader",
    "MarkdownLoader",
    "JsonLoader",
    "HTMLoader",
    "Artifact",  # for backward compatibility, to be removed in next major version.
]
