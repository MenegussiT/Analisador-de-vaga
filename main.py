# Salve este código em: main.py
from core.pdf_parser import extrair_texto_pdf
from core.cv_analyzer import analisar_cv
from core.job_scraper import buscar_vagas
from profiles.profile_manager import inicializar_banco, salvar_perfil, carregar_perfil
from telegram_bot.bot import run as run_bot

# --- CONFIGURAÇÃO DE TESTE ---

NOME_ARQUIVO_CV = "Curriculo_AlexandreCalabria.pdf" 

# Simula um usuário para o teste do banco de dados.
USER_ID_TESTE = 434568
# -----------------------------

def rodar_teste_completo_com_memoria():
    """
    Função de teste que executa o fluxo completo (IA + DB)
    usando um arquivo de CV fixo para facilitar os testes.
    """
    inicializar_banco()
    print(f"--- Iniciando teste para o Usuário ID: {USER_ID_TESTE} ---")

    perfil_para_busca = None
    perfil_salvo = carregar_perfil(USER_ID_TESTE)

    if perfil_salvo:
        print(f"\n> Perfil encontrado no banco de dados!")
        print(f"  Cargo Salvo: '{perfil_salvo.get('cargo_ideal')}'")
        # Para facilitar o teste, vamos assumir 's' (sim) automaticamente.
        # Se quiser que ele pergunte, descomente a linha abaixo e comente a seguinte.
        # usar_salvo = input("  Deseja usar este perfil? (s/n): ").lower()
        usar_salvo = 's' 
        print("  Usando o perfil salvo automaticamente para o teste.")
        if usar_salvo == 's':
            perfil_para_busca = perfil_salvo
    
    if not perfil_para_busca:
        print(f"\nNenhum perfil carregado. Analisando o arquivo '{NOME_ARQUIVO_CV}'...")
        
        texto_cv = extrair_texto_pdf(NOME_ARQUIVO_CV)
        if not texto_cv:
            print(f"Erro: Não foi possível ler o arquivo '{NOME_ARQUIVO_CV}'.")
            print("Verifique se o arquivo está na mesma pasta que o main.py.")
            return
        
        perfil_para_busca = analisar_cv(texto_cv)
        if not perfil_para_busca:
            print("Erro: Falha na análise do CV pela IA.")
            return
        
        salvar_perfil(USER_ID_TESTE, perfil_para_busca)
    
    if perfil_para_busca:
        cargo = perfil_para_busca.get("cargo_ideal", "N/A")
        print(f"\nPerfil definido. Iniciando busca para o cargo: '{cargo}'")

        # Para facilitar o teste, vamos fixar a localização também.
        # Se quiser que ele pergunte, descomente a linha abaixo e comente a seguinte.
        # localizacao = input("Informe a localização desejada: ")
        localizacao = input("Informe a localização desejada (deixe em branco para buscar em todas as localizações): ") or "todas as localizações"
        print(f"Buscando em localização de teste: '{localizacao}'")
        
        vagas = buscar_vagas(cargo, localizacao)

        if vagas:
            print(f"\n--- {len(vagas)} vagas encontradas ---")
            for vaga in vagas[:5]:
                print(f"Título: {vaga['titulo']}\nEmpresa: {vaga['empresa']}\nLocal: {vaga['local']}\nLink: {vaga['link']}\n" + "-"*20)
        else:
            print("\nNenhuma vaga encontrada para os critérios especificados.")

if __name__ == "__main__":
   inicializar_banco()
   run_bot()