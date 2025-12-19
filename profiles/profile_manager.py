import sqlite3
import json
import re
from typing import Dict, Optional

DB_PATH = "bot_database.db"

def inicializar_banco():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Tabela de Perfis
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS perfis (
            user_id INTEGER PRIMARY KEY,
            cargo_ideal TEXT,
            habilidades_chave TEXT
        );
        """)
        conn.commit()

        # Migração de colunas (caso o banco antigo não tenha)
        cursor.execute("PRAGMA table_info(perfis);")
        existing_cols = {row[1] for row in cursor.fetchall()}

        for col in ("nome", "sobrenome", "telefone"):
            if col not in existing_cols:
                cursor.execute(f"ALTER TABLE perfis ADD COLUMN {col} TEXT DEFAULT ''")
        conn.commit()

        # Tabela de Histórico de Vagas (Para evitar duplicatas)
        # Ajustei o UNIQUE para ser a combinação de user_id + link
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico_vagas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            job_link TEXT,
            data_envio DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, job_link)
        );
        """)
        conn.commit()


def _normalize_phone(telefone: str) -> str:
    if not telefone:
        return ""
    telefone = telefone.strip()
    if telefone.startswith("+"):
        digits = re.sub(r"\D", "", telefone[1:])
        return f"+{digits}"
    return re.sub(r"\D", "", telefone)

def _validar_telefone(telefone: str) -> bool:
    if not telefone:
        return False
    t = _normalize_phone(telefone)
    t_digits = t[1:] if t.startswith("+") else t
    return 8 <= len(t_digits) <= 15

def salvar_perfil(user_id: int, perfil: Dict):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT cargo_ideal, habilidades_chave, nome, sobrenome, telefone FROM perfis WHERE user_id = ?;", (user_id,))
        existente = cursor.fetchone()
        
        # Lógica de merge (manter dados antigos se os novos forem vazios)
        cargo = perfil.get("cargo_ideal") if perfil.get("cargo_ideal") is not None else (existente["cargo_ideal"] if existente else "")
        
        if "habilidades_chave" in perfil:
            habilidades = perfil.get("habilidades_chave") or []
        else:
            try:
                habilidades = json.loads(existente["habilidades_chave"]) if existente and existente["habilidades_chave"] else []
            except Exception:
                habilidades = []

        nome = perfil.get("nome") or (existente["nome"] if existente else "")
        sobrenome = perfil.get("sobrenome") or (existente["sobrenome"] if existente else "")
        telefone_raw = perfil.get("telefone") or (existente["telefone"] if existente else "")
        telefone = _normalize_phone(telefone_raw)

        cursor.execute("""
            INSERT OR REPLACE INTO perfis (user_id, cargo_ideal, habilidades_chave, nome, sobrenome, telefone)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (user_id, cargo, json.dumps(habilidades, ensure_ascii=False), nome, sobrenome, telefone))
        conn.commit()

def carregar_perfil(user_id: int) -> Optional[Dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT cargo_ideal, habilidades_chave, nome, sobrenome, telefone FROM perfis WHERE user_id = ?;", (user_id,))
        row = cursor.fetchone()
        if row:
            try:
                habilidades = json.loads(row["habilidades_chave"]) if row["habilidades_chave"] else []
            except Exception:
                habilidades = []
            return {
                "cargo_ideal": row["cargo_ideal"],
                "habilidades_chave": habilidades,
                "nome": row["nome"],
                "sobrenome": row["sobrenome"],
                "telefone": row["telefone"],
            }
    return None

# --- NOVAS FUNÇÕES PARA CONTROLE DE VAGAS ---

def vaga_ja_enviada(user_id: int, link: str) -> bool:
    """Retorna True se o link já foi enviado para este usuário."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM historico_vagas WHERE user_id = ? AND job_link = ?", 
            (user_id, link)
        )
        return cursor.fetchone() is not None

def registrar_envio(user_id: int, link: str):
    """Registra o envio da vaga para não enviar novamente."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        try:
            # INSERT OR IGNORE evita erro se tentar inserir duplicado
            cursor.execute(
                "INSERT OR IGNORE INTO historico_vagas (user_id, job_link) VALUES (?, ?)", 
                (user_id, link)
            )
            conn.commit()
        except Exception as e:
            print(f"Erro ao registrar vaga: {e}")

# --- FUNÇÕES DE CONSOLE (MANTIDAS) ---

def cadastrar_via_chat_console(user_id: int):
    print("Vou cadastrar suas informações de contato. Se quiser pular, enter vazio.")
    nome = input("Nome: ").strip()
    sobrenome = input("Sobrenome: ").strip()
    telefone = input("Telefone (ex: +5511999998888 ou 11999998888): ").strip()

    if telefone and not _validar_telefone(telefone):
        print("Telefone inválido. Verifique o formato e tente novamente.")
        return False

    perfil = {
        "nome": nome,
        "sobrenome": sobrenome,
        "telefone": telefone
    }
    salvar_perfil(user_id, perfil)
    print("Cadastro atualizado com sucesso.")
    return True

def listar_perfis():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, cargo_ideal, nome, sobrenome, telefone FROM perfis;")
        return cursor.fetchall()