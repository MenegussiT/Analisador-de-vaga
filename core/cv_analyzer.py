import google.generativeai as genai
from config import GOOGLE_API_KEY
from typing import Dict, Optional
import json

def analisar_cv(texto_cv : str) -> Optional[Dict]:
    """
    Usa o Google Gemini para analisar o CV e extrair informações relevantes.
    """
    if not GOOGLE_API_KEY:
        print("ERRO: GOOGLE_API_KEY não configurado no arquivo .env ou config.py.")
        return None
    
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt =f"""
        Aja como um recrutador técnico especialista. Analise o texto do currículo abaixo.
        Sua tarefa é extrair as seguintes informações e retornar APENAS um objeto JSON válido, sem nenhum texto ou formatação extra.

        1. "cargo_ideal": Um título de cargo conciso para buscas (exemplo: "Desenvolvedor Python").
        2. "nivel_experiencia": O nível de senioridade (exemplo: "Júnior", "Pleno", "Sênior"). Para definir este campo, siga esta lógica de duas etapas:
           - ETAPA 1: Primeiro, procure por palavras-chave explícitas no texto como 'júnior', 'estágio', 'iniciante', 'pleno', 'sênior'. Se encontrar, use essa classificação.
           - ETAPA 2: Se nenhuma palavra-chave explícita for encontrada, estime a senioridade somando o tempo de atividade em cada experiência profissional listada. Use as seguintes durações como base: menos de 2 anos de experiência total = "Júnior"; de 2 a 5 anos = "Pleno"; mais de 5 anos = "Sênior".
        3. "habilidades_chave": Uma lista com as 5 habilidades técnicas mais relevantes.

        Texto do Currículo:
        ---
        {texto_cv}
        ---

        Formato JSON esperado: {{"cargo_ideal": "string", "nivel_experiencia": "string", "habilidades_chave": ["string1", "string2"]}}
        """

        print(f"\n analisando o CV...")

        #Envia para o modelo
        response = model.generate_content(prompt)


        #Retornar JSON
        json_text = response.text.strip().replace("```json", "").replace("```", "")
        
        dados_analisados = json.loads(json_text)
        return dados_analisados
    
    except Exception as e:
        print(f"ERRO ao comunicar com a API do Google Gemini: {e}")
        return None