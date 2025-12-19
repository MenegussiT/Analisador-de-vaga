from google import genai # Alterado para o novo SDK
from config import GOOGLE_API_KEY
from typing import Dict, Optional
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def analisar_cv(texto_cv: str) -> Optional[Dict]:
    """
    Usa o novo SDK Google para analisar o CV e extrair informações relevantes,
    garantindo uma saída JSON robusta.
    """
    if not GOOGLE_API_KEY:
        logging.error("ERRO: GOOGLE_API_KEY não configurado no arquivo .env ou config.py.")
        return None

    try:
        # Inicializa o cliente com o novo SDK
        client = genai.Client(api_key=GOOGLE_API_KEY)

        prompt = f"""
        Aja como um recrutador generalista sênior, com experiência em diversas áreas de atuação.
        Sua tarefa é analisar o texto do currículo abaixo e extrair as seguintes informações de forma objetiva.
        Retorne APENAS um objeto JSON válido.

        1. "cargo_ideal": Determine o título de cargo mais apropriado para o candidato.
        2. "nivel_experiencia": O nível de senioridade (ex: "Júnior", "Pleno", "Sênior", "Estagiário").
        3. "habilidades_chave": Uma lista com as 5 competências mais relevantes.

        Texto do Currículo:
        ---
        {texto_cv}
        ---
        """

        logging.info("Analisando o CV com a API Gemini...")

        # Chamada corrigida para a sintaxe do novo SDK
        response = client.models.generate_content(
            model="gemini-2.0-flash", # Usando o ID estável
            contents=prompt,
            config={
                "response_mime_type": "application/json"
            }
        )

        # O novo SDK permite acessar o texto diretamente
        json_text = response.text

        dados_analisados = json.loads(json_text)
        return dados_analisados

    except json.JSONDecodeError as e:
        logging.error(f"ERRO ao decodificar o JSON: {e}")
        return None
    except Exception as e:
        logging.error(f"ERRO ao comunicar com a API do Google Gemini: {e}")
        return None