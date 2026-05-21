from pypdf import PdfReader


def extract_pdf_text(pdf_path: str) -> str:

    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:

        extracted = page.extract_text()

        if extracted:
            text += extracted + "\n"

    return text