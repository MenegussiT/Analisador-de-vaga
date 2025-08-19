import fitz
from typing import Union
import io


def extrair_texto_pdf(fonte_pdf : Union[str, io.BytesIO]) -> str | None:
    '''
    Abre um arquivo PDF e retorna com o texto contido nele.
     
    '''
    try:
        with fitz.open(stream=fonte_pdf, filetype="pdf") as doc:
            texto_completo = "".join(page.get_text() for page in doc)
            return texto_completo
    except Exception as e:
        print(f"Erro ao ler o PDF: {e}")
        return None