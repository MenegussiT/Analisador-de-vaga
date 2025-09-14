import sqlite3
import json
import re
from typing import Dict, Optional

DB_PATH = "bot_database.db"
def inicializar_banco():
    """Cria a tabela e adiciona colunas ausentes se necessário."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Cria tabela caso não exista
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS perfis (
            user_id INTEGER PRIMARY KEY,
            cargo_ideal TEXT,
            habilidades_chave TEXT
        );
        """)
        conn.commit()

        # Verifica colunas existentes
        cursor.execute("PRAGMA table_info(perfis);")
        existing_cols = {row[1] for row in cursor.fetchall()}

        # Adiciona colunas novas se não existirem
        for col in ("nome", "sobrenome", "telefone"):
            if col not in existing_cols:
                cursor.execute(f"ALTER TABLE perfis ADD COLUMN {col} TEXT DEFAULT ''")
        conn.commit()


def _normalize_phone(telefone: str) -> str:
    """Retira tudo que não é dígito e mantem '+' se existir no início (opcional)."""
    if not telefone:
        return ""
    # Remove espaços e caracteres não numéricos (mantendo + no começo)
    telefone = telefone.strip()
    if telefone.startswith("+"):
        digits = re.sub(r"\D", "", telefone[1:])
        return f"+{digits}"
    return re.sub(r"\D", "", telefone)

def _validar_telefone(telefone: str) -> bool:
    """Validação simples: entre 8 e 15 dígitos (após normalizar)."""
    if not telefone:
        return False
    t = _normalize_phone(telefone)
    # Remove leading + para contagem:
    t_digits = t[1:] if t.startswith("+") else t
    return 8 <= len(t_digits) <= 15

def salvar_perfil(user_id: int, perfil: Dict):
    """
    Salva ou atualiza o perfil. Faz merge com valores existentes para não sobrescrever campos não fornecidos.
    Espera que `perfil` possa conter: cargo_ideal, habilidades_chave (list), nome, sobrenome, telefone.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Buscar existente (se houver) para fazer merge seguro
        cursor.execute("SELECT cargo_ideal, habilidades_chave, nome, sobrenome, telefone FROM perfis WHERE user_id = ?;", (user_id,))
        existente = cursor.fetchone()

        # Recupera/mescla campos
        cargo = perfil.get("cargo_ideal") if perfil.get("cargo_ideal") is not None else (existente["cargo_ideal"] if existente else "")
        # habilidades: aceitar lista nova ou manter existente
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

        # Inserir ou substituir a linha (com todos os campos)
        cursor.execute("""
            INSERT OR REPLACE INTO perfis (user_id, cargo_ideal, habilidades_chave, nome, sobrenome, telefone)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (user_id, cargo, json.dumps(habilidades, ensure_ascii=False), nome, sobrenome, telefone))
        conn.commit()

def carregar_perfil(user_id: int) -> Optional[Dict]:
    """Carrega e retorna o perfil completo (ou None)."""
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

# Função utilitária de fluxo via console (exemplo). Se o "chat" for um bot, adapte os prompts
def cadastrar_via_chat_console(user_id: int):
    """Exemplo de fluxo interativo no console. Em um bot, substitua por handlers."""
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

# Função para debug
def listar_perfis():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, cargo_ideal, nome, sobrenome, telefone FROM perfis;")
        return cursor.fetchall()

