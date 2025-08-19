

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional


from config import LINKEDIN_URL, USER_AGENT

def buscar_vagas(cargo: str, localizacao: str) -> Optional[List[Dict]]:
    """
    Busca vagas de emprego no LinkedIn.
    Retorna uma lista de vagas ou None se ocorrer um erro.
    """
    print(f"\nBuscando vagas para '{cargo}' em '{localizacao}'...")

    if not LINKEDIN_URL:
        print("ERRO: URL do LinkedIn não configurada no arquivo .env ou config.py.")
        return None

 
    params = {
        'keywords': cargo,
        'location': localizacao,
        'trk': 'public_jobs_jobs-search-bar_search-submit', 
        'position': 1,
        'pageNum': 0
    }
    
  
    
    try:
        # A chamada GET agora usa  dicionário 'params' para construir a URL.
        resposta = requests.get(LINKEDIN_URL, headers={'User-Agent': USER_AGENT}, params=params)
        resposta.raise_for_status()

        soup = BeautifulSoup(resposta.text, 'html.parser')
        
        cards_vagas = soup.find_all('div', class_='base-card')
        
        if not cards_vagas:
            print("Nenhuma vaga encontrada com esses critérios.")
            return []

        lista_de_vagas = []
        for card in cards_vagas:
            try:
                titulo = card.find('h3', class_='base-search-card__title').text.strip()
                empresa = card.find('h4', class_='base-search-card__subtitle').text.strip()
                local = card.find('span', class_='job-search-card__location').text.strip()
                
                link_tag = card.find('a', class_='base-card__full-link')
                link = link_tag['href'] if link_tag else "Link não encontrado"
                
                lista_de_vagas.append({
                    "titulo": titulo, "empresa": empresa,
                    "local": local, "link": link
                })
            except AttributeError:
                continue
        
        return lista_de_vagas

    except requests.exceptions.RequestException as e:
        print(f"ERRO de conexão ao buscar vagas: {e}")
        return None