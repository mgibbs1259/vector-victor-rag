import pdfplumber
import polars as pl
from pypdf import PdfReader


def analyze_pdf_text_content(file_path: str) -> pl.DataFrame:
    """
    Analyzes the text content of each page in a PDF file to determine which pages contain text.

    Args:
        file_path (str): The path to the PDF file.

    Returns:
        pl.DataFrame: A Polars DataFrame with columns: "page_number", "contains_text", "extracted_text".
            - "page_number": The page number in the PDF.
            - "contains_text": A binary indicator (1) indicating whether the page contains text.
            - "extracted_text": The extracted text.
    """
    reader = PdfReader(file_path)

    data = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text().strip()

        if text:
            data.append({"page_number": i, "contains_text": 1, "extracted_text": text})

    return pl.DataFrame(data)


def analyze_pdf_image_content(file_path: str) -> pl.DataFrame:
    """
    Analyzes the image content of each page in a PDF file to determine which pages contain images.

    Args:
        file_path (str): The path to the PDF file.

    Returns:
        pl.DataFrame: A Polars DataFrame with columns: "page_number", "contains_images", "image_number".
            - "page_number": The page number in the PDF.
            - "contains_images": A binary indicator (1) indicating whether the page contains images.
            - "image_number": The order of the images on the page.
    """
    reader = PdfReader(file_path)

    data = []
    for i, page in enumerate(reader.pages, start=1):
        images = page.images

        if images:
            for j, _ in enumerate(images, start=1):
                data.append({"page_number": i, "contains_images": 1, "image_number": j})

    return pl.DataFrame(data)


def analyze_pdf_table_content(file_path: str) -> pl.DataFrame:
    """
    Analyzes the table content of each page in a PDF file to determine which pages contain tables.

    Args:
        file_path (str): The path to the PDF file.

    Returns:
        pl.DataFrame: A Polars DataFrame with columns:
            - "page_number": The page number in the PDF.
            - "contains_tables": A binary indicator (1) indicating that the page contains tables.
            - "table_number": The order of the tables on the page.
            - "extracted_table_text": A string representation of a dictionary where keys are column headers and values are lists of column values.
                - Each dictionary represents the data of one table on a specific page.
    """
    data = []

    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()

            for table_num, table in enumerate(tables, start=1):
                if table and table[0] != [""]:
                    headers = table[0]  # First row as headers
                    extracted_table = {header: [] for header in headers}

                    for row in table[1:]:
                        if len(row) == len(headers):  # Ensure row length matches headers length
                            for header, value in zip(headers, row):
                                extracted_table[header].append(value)

                    data.append(
                        {
                            "page_number": page_num,
                            "contains_tables": 1,
                            "table_number": table_num,
                            "extracted_table_text": str(extracted_table),
                        }
                    )

    df = pl.DataFrame(data)
    return df
