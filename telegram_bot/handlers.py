import io
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

# Importa as funções principais
from core.pdf_parser import extrair_texto_pdf
from core.cv_analyzer import analisar_cv
from core.job_scraper import buscar_vagas

# Importamos as novas funções de controle de histórico
from profiles.profile_manager import (
    salvar_perfil, 
    _validar_telefone, 
    carregar_perfil, 
    vaga_ja_enviada, 
    registrar_envio
)

# --- DEFINIÇÃO DOS ESTADOS DA CONVERSA ---
AGUARDANDO_NOME, AGUARDANDO_SOBRENOME, AGUARDANDO_TELEFONE, AGUARDANDO_LOCALIZACAO, ESCOLHER_ACAO = range(5)

# --- FUNÇÕES DO FLUXO DE CONVERSA ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Inicia a interação. Verifica perfil existente e oferece menu.
    """
    user_id = update.effective_user.id
    perfil_existente = carregar_perfil(user_id)

    if perfil_existente and perfil_existente.get('cargo_ideal'):
        context.user_data['perfil'] = perfil_existente
        
        nome = perfil_existente.get('nome', 'Candidato')
        cargo = perfil_existente.get('cargo_ideal', 'N/A')

        msg = (
            f"Olá de novo, *{nome}*! 👋\n"
            f"Lembro que você busca vagas de: *{cargo}*.\n\n"
            "O que você deseja fazer hoje?"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔍 Buscar Vagas (Usar perfil salvo)", callback_data="acao_buscar")],
            [InlineKeyboardButton("📄 Enviar Novo Currículo", callback_data="acao_novo_cv")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode='Markdown')
        return ESCOLHER_ACAO
    else:
        await update.message.reply_text(
            "Olá! Sou seu assistente de busca de vagas.\n\n"
            "Para começar, por favor, envie seu currículo em formato PDF. "
            "A qualquer momento, você pode digitar /cancelar para encerrar."
        )
        return ConversationHandler.END

async def botao_acao_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Lida com o clique nos botões."""
    query = update.callback_query
    await query.answer()

    if query.data == "acao_buscar":
        await query.edit_message_text(
            "Ótimo! Vamos usar seus dados salvos.\n\n"
            "Para onde deseja buscar as vagas? (ex: Rio de Janeiro, Remoto, São Paulo)"
        )
        return AGUARDANDO_LOCALIZACAO

    elif query.data == "acao_novo_cv":
        await query.edit_message_text(
            "Entendido. Por favor, envie o *novo arquivo PDF* do seu currículo.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

async def receber_cv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa o CV, salva o perfil e verifica dados existentes."""
    user_id = update.message.from_user.id
    
    try:
        pdf_file = await context.bot.get_file(update.message.document.file_id)
        pdf_bytes = io.BytesIO(await pdf_file.download_as_bytearray())
        await update.message.reply_text("Currículo recebido! Analisando as informações com a IA... 🧠")

        texto_cv = extrair_texto_pdf(pdf_bytes)
        if not texto_cv:
            await update.message.reply_text("❌ Erro: Não consegui ler o texto do PDF.")
            return ConversationHandler.END

        perfil_ia = analisar_cv(texto_cv)
        if not perfil_ia:
            await update.message.reply_text("❌ Erro: A análise do currículo falhou. Tente novamente.")
            return ConversationHandler.END
        
        salvar_perfil(user_id, perfil_ia)
        context.user_data['perfil'] = perfil_ia 

        # Se já tem cadastro completo, pula para localização
        perfil_banco = carregar_perfil(user_id)
        if perfil_banco and perfil_banco.get('nome') and perfil_banco.get('telefone'):
             context.user_data['perfil'] = perfil_banco
             await update.message.reply_text(
                f"Currículo atualizado! Novo cargo detectado: *{perfil_ia.get('cargo_ideal')}*.\n"
                f"Como já tenho seus dados, informe a *localização* para a busca.",
                parse_mode='Markdown'
             )
             return AGUARDANDO_LOCALIZACAO

        await update.message.reply_text(
            f"Análise concluída! Cargo ideal identificado: *{perfil_ia.get('cargo_ideal', 'N/A')}*\n\n"
            "Para finalizar, qual é o seu *primeiro nome*?",
            parse_mode='Markdown'
        )
        return AGUARDANDO_NOME 

    except Exception as e:
        print(f"Erro crítico ao processar o CV: {e}")
        await update.message.reply_text("❌ Ocorreu um erro inesperado.")
        return ConversationHandler.END

async def receber_nome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    nome = update.message.text.strip()
    salvar_perfil(user_id, {"nome": nome})
    await update.message.reply_text(f"Ótimo, {nome}! Agora, qual o seu *sobrenome*?")
    return AGUARDANDO_SOBRENOME

async def receber_sobrenome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    sobrenome = update.message.text.strip()
    salvar_perfil(user_id, {"sobrenome": sobrenome})
    await update.message.reply_text("Informe seu *telefone* (com DDD) ou digite /pular.")
    return AGUARDANDO_TELEFONE

async def receber_telefone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    telefone = update.message.text.strip()
    if not _validar_telefone(telefone):
        await update.message.reply_text("❌ Telefone inválido. Tente novamente ou digite /pular.")
        return AGUARDANDO_TELEFONE 
    salvar_perfil(user_id, {"telefone": telefone})
    await update.message.reply_text("✅ Telefone salvo! Informe a *localização* para a busca.", parse_mode='Markdown')
    return AGUARDANDO_LOCALIZACAO

async def pular_telefone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Ok. Informe a *localização* para a busca.", parse_mode='Markdown')
    return AGUARDANDO_LOCALIZACAO

async def receber_localizacao_e_buscar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe a localização, busca vagas e filtra duplicatas."""
    localizacao = update.message.text.strip()
    perfil = context.user_data.get('perfil')
    user_id = update.effective_user.id

    if not perfil or 'cargo_ideal' not in perfil:
        await update.message.reply_text("❌ Erro de perfil. Digite /start.")
        return ConversationHandler.END

    cargo = perfil['cargo_ideal']
    await update.message.reply_text(f"🚀 Buscando vagas de *{cargo}* em *{localizacao}*...", parse_mode='Markdown')

    vagas = buscar_vagas(cargo, localizacao)

    if vagas:
        lista_vagas_texto = []
        contador_novas = 0
        
        # Itera sobre todas as vagas encontradas para filtrar as já enviadas
        for vaga in vagas:
            # Verifica se já enviou
            if vaga_ja_enviada(user_id, vaga['link']):
                continue
                
            # Formatação HTML
            vaga_formatada = (
                f"<b>{vaga['titulo']}</b>\n"
                f"<i>{vaga['empresa']}</i>\n"
                f"📍 {vaga['local']}\n"
                f"<a href='{vaga['link']}'>Ver Vaga</a>"
            )
            lista_vagas_texto.append(vaga_formatada)
            
            # Registra como enviada no banco
            registrar_envio(user_id, vaga['link'])
            
            contador_novas += 1
            if contador_novas >= 5: # Limita a mostrar 5 vagas NOVAS por vez
                break
        
        if not lista_vagas_texto:
            # Se encontrou vagas no scraper, mas todas já tinham sido enviadas antes
            await update.message.reply_text(
                "🔎 Encontrei vagas, mas parece que eu já te enviei todas elas anteriormente!\n"
                "Tente buscar novamente amanhã ou mude a região da busca."
            )
        else:
            separador = "\n\n" + ("-" * 25) + "\n\n"
            corpo_mensagem = separador.join(lista_vagas_texto)
            mensagem_final = f"✅ Encontrei estas vagas *NOVAS* para você:\n\n{corpo_mensagem}"
            
            await update.message.reply_text(mensagem_final, parse_mode='HTML', disable_web_page_preview=True)
            
    else:
        await update.message.reply_text("😕 Nenhuma vaga encontrada para os critérios informados.")

    await update.message.reply_text("Busca encerrada. Digite /start se quiser fazer uma nova busca!")
    return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Conversa encerrada.")
    return ConversationHandler.END