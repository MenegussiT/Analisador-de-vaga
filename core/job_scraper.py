import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
import random
from itertools import zip_longest
from config import LINKEDIN_URL, USER_AGENT

# Configuração de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def _scrape_linkedin(cargo: str, localizacao: str) -> List[Dict]:
    """Busca vagas no LinkedIn."""
    if not LINKEDIN_URL:
        logging.error("URL do LinkedIn não configurada.")
        return []

    params = {
        'keywords': cargo,
        'location': localizacao,
        'trk': 'public_jobs_jobs-search-bar_search-submit', 
        'position': 1,
        'pageNum': 0
    }
    
    vagas = []
    try:
        resposta = requests.get(LINKEDIN_URL, headers={'User-Agent': USER_AGENT}, params=params, timeout=10)
        
        # Se der erro 429 ou outros, não quebra o bot, apenas loga e retorna vazio
        if resposta.status_code != 200:
            logging.warning(f"LinkedIn retornou status {resposta.status_code}")
            return []

        soup = BeautifulSoup(resposta.text, 'html.parser')
        cards_vagas = soup.find_all('div', class_='base-card')
        
        for card in cards_vagas:
            try:
                titulo = card.find('h3', class_='base-search-card__title').text.strip()
                empresa = card.find('h4', class_='base-search-card__subtitle').text.strip()
                local = card.find('span', class_='job-search-card__location').text.strip()
                
                link_tag = card.find('a', class_='base-card__full-link')
                link = link_tag['href'] if link_tag else "Link não encontrado"
                
                vagas.append({
                    "titulo": titulo, 
                    "empresa": empresa,
                    "local": local, 
                    "link": link,
                    "fonte": "LinkedIn"
                })
            except AttributeError:
                continue
    except Exception as e:
        logging.error(f"Erro no LinkedIn: {e}")
    
    return vagas

def _scrape_riovagas(cargo: str) -> List[Dict]:
    """Busca vagas no RioVagas."""
    vagas = []
    termo_busca = cargo.replace(' ', '+')
    url = f"https://riovagas.com.br/?s={termo_busca}"
    
    try:
        resposta = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=10)
        
        if resposta.status_code != 200:
            return []
            
        soup = BeautifulSoup(resposta.text, 'html.parser')
        
        # Tenta encontrar os artigos de vagas
        artigos = soup.find_all('article')
        if not artigos:
            artigos = soup.find_all('div', class_='post') # Fallback de layout

        for art in artigos[:15]: # Pega até 15 para ter margem
            try:
                link_tag = art.find('a')
                if not link_tag: continue
                
                titulo = link_tag.text.strip()
                link = link_tag['href']
                
                # Filtros básicos de qualidade
                if "page" in link or "google" in link: continue

                vagas.append({
                    "titulo": titulo,
                    "empresa": "RioVagas / Diversas",
                    "local": "Rio de Janeiro, RJ",
                    "link": link,
                    "fonte": "RioVagas"
                })
            except Exception:
                continue
    except Exception as e:
        logging.error(f"Erro no RioVagas: {e}")
    
    return vagas

def buscar_vagas(cargo: str, localizacao: str) -> Optional[List[Dict]]:
    """
    Busca vagas em múltiplas fontes e mistura os resultados.
    """
    print(f"\n🔎 Iniciando busca unificada para '{cargo}' em '{localizacao}'...")
    
    lista_linkedin = _scrape_linkedin(cargo, localizacao)
    lista_riovagas = []

    # Verifica se a localização é no Rio de Janeiro (RJ, Rio, Niterói, etc)
    loc_lower = localizacao.lower()
    if "rio de janeiro" in loc_lower or "rj" in loc_lower or "rio" in loc_lower:
        print("📍 Localização RJ detectada! Adicionando fontes locais...")
        lista_riovagas = _scrape_riovagas(cargo)
    
    # --- LÓGICA DE MISTURA (INTERCALAÇÃO) ---
    # Isso garante que a lista final tenha: [1 LinkedIn, 1 RioVagas, 1 LinkedIn, 1 RioVagas...]
    # Assim o usuário vê variedade nas primeiras 5 vagas.
    
    lista_final = []
    # zip_longest pega o maior das duas listas e preenche com None quando a menor acaba
    for vaga_lk, vaga_rv in zip_longest(lista_linkedin, lista_riovagas):
        if vaga_lk:
            lista_final.append(vaga_lk)
        if vaga_rv:
            lista_final.append(vaga_rv)
            
    if not lista_final:
        print("😕 Nenhuma vaga encontrada nas fontes consultadas.")
        return []

    print(f"✅ Total consolidado: {len(lista_final)} vagas (LinkedIn: {len(lista_linkedin)}, RioVagas: {len(lista_riovagas)})")
    return lista_final