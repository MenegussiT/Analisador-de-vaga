import sqlite3
import json
from typing import Dict, Optional

# O nome do arquivo do banco de dados, definido como uma constante.
DB_PATH = "bot_database.db"

def inicializar_banco():

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # A tabela armazena o ID do usuário, o cargo e as habilidades.
        # O user_id é a chave primária para garantir que cada usuário seja único.
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS perfis (
            user_id INTEGER PRIMARY KEY,
            cargo_ideal TEXT NOT NULL,
            habilidades_chave TEXT NOT NULL
        );
        """)
        conn.commit()

def salvar_perfil(user_id: int, perfil: Dict):
    """Salva ou atualiza o perfil de um usuário no banco de dados."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Converte a lista de habilidades em uma string JSON para poder ser salva.
        habilidades_json = json.dumps(perfil.get("habilidades_chave", []))
        
        # "INSERT OR REPLACE" é o comando ideal para inserir um novo perfil
        # ou atualizar um existente com base no user_id.
        cursor.execute("""
        INSERT OR REPLACE INTO perfis (user_id, cargo_ideal, habilidades_chave)
        VALUES (?, ?, ?);
        """, (user_id, perfil.get("cargo_ideal"), habilidades_json))
        conn.commit()

def carregar_perfil(user_id: int) -> Optional[Dict]:
    """Carrega o perfil de um usuário do banco de dados, se existir."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT cargo_ideal, habilidades_chave FROM perfis WHERE user_id = ?;", (user_id,))
        resultado = cursor.fetchone()
        
        if resultado:
            # Converte a string JSON de habilidades de volta para uma lista Python.
            habilidades = json.loads(resultado[1])
            return {"cargo_ideal": resultado[0], "habilidades_chave": habilidades}
            
    return None