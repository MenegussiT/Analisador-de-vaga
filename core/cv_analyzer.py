import google.generativeai as genai
from config import GOOGLE_API_KEY
from typing import Dict, Optional
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def analisar_cv(texto_cv: str) -> Optional[Dict]:
    """
    Usa o Google Gemini para analisar o CV e extrair informações relevantes,
    garantindo uma saída JSON mais robusta e precisa.
    """
    if not GOOGLE_API_KEY:
        logging.error("ERRO: GOOGLE_API_KEY não configurado no arquivo .env ou config.py.")
        return None

    try:
        genai.configure(api_key=GOOGLE_API_KEY)

        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"""
        Aja como um recrutador generalista sênior, com experiência em diversas áreas de atuação.
        Sua tarefa é analisar o texto do currículo abaixo e extrair as seguintes informações de forma objetiva.
        Retorne APENAS um objeto JSON válido.

        1. "cargo_ideal": Determine o título de cargo mais apropriado para o candidato. Sua lógica deve ser:
           - ETAPA 1: Priorize o título do cargo mais recente ou o cargo principal listado no resumo/título do currículo.
           - ETAPA 2: Se o currículo não tiver um cargo claro, deduza a profissão com base nas experiências e habilidades descritas (ex: se fala em processos, petições e leis, o cargo pode ser "Advogado").
           - ETAPA 3: O cargo deve ser um título comum usado no mercado de trabalho para facilitar a busca de vagas.

        2. "nivel_experiencia": O nível de senioridade (ex: "Júnior", "Pleno", "Sênior", "Estagiário"). Para definir este campo, siga esta lógica:
           - ETAPA 1: Procure por palavras-chave explícitas no texto como 'júnior', 'estágio', 'iniciante', 'pleno', 'sênior', 'especialista'. Se encontrar, use essa classificação.
           - ETAPA 2: Se não houver palavras-chave, estime a senioridade somando o tempo total de experiência profissional na área principal do candidato. Use como base: menos de 2 anos = "Júnior"; 2 a 5 anos = "Pleno"; mais de 5 anos = "Sênior".

        3. "habilidades_chave": Uma lista com as 5 competências (técnicas ou comportamentais) mais relevantes para a profissão do candidato, conforme descrito no currículo.

        Texto do Currículo:
        ---
        {texto_cv}
        ---
        """

        logging.info("Analisando o CV com a API Gemini...")

        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json"
            }
        )

        # Tenta pegar o texto
        json_text = response.text or response.candidates[0].content.parts[0].text

        dados_analisados = json.loads(json_text)
        return dados_analisados

    except json.JSONDecodeError as e:
        logging.error(f"ERRO ao decodificar o JSON: {e}")
        logging.error(f"Texto recebido da API que causou o erro: {json_text}")
        return None
    except Exception as e:
        logging.error(f"ERRO ao comunicar com a API do Google Gemini: {e}")
        return None
