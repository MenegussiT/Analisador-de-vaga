import io
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

# Importa as funções principais
from core.pdf_parser import extrair_texto_pdf
from core.cv_analyzer import analisar_cv
from core.job_scraper import buscar_vagas
from profiles.profile_manager import salvar_perfil, _validar_telefone, carregar_perfil

# --- DEFINIÇÃO DOS ESTADOS DA CONVERSA ---
# Adicionamos ESCOLHER_ACAO para o menu de botões
AGUARDANDO_NOME, AGUARDANDO_SOBRENOME, AGUARDANDO_TELEFONE, AGUARDANDO_LOCALIZACAO, ESCOLHER_ACAO = range(5)

# --- FUNÇÕES DO FLUXO DE CONVERSA ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Inicia a interação.
    Verifica se o usuário já tem perfil salvo. Se sim, oferece menu. Se não, pede CV.
    """
    user_id = update.effective_user.id
    perfil_existente = carregar_perfil(user_id)

    if perfil_existente:
        # Salva no contexto para uso imediato se ele escolher buscar vagas
        context.user_data['perfil'] = perfil_existente
        
        nome = perfil_existente.get('nome', 'Candidato')
        cargo = perfil_existente.get('cargo_ideal', 'N/A')

        msg = (
            f"Olá de novo, *{nome}*! 👋\n"
            f"Encontrei seu perfil salvo para o cargo de *{cargo}*.\n\n"
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
        # Usuário novo
        await update.message.reply_text(
            "Olá! Sou seu assistente de busca de vagas.\n\n"
            "Para começar, por favor, envie seu currículo em formato PDF. "
            "A qualquer momento, você pode digitar /cancelar para encerrar."
        )
        return ConversationHandler.END # Retorna END para permitir que o MessageHandler de PDF pegue o arquivo

async def botao_acao_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Lida com o clique nos botões do menu inicial."""
    query = update.callback_query
    await query.answer() # Confirma o clique para parar o 'loading' no botão

    if query.data == "acao_buscar":
        # Pula direto para a pergunta da localização
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
        return ConversationHandler.END # Encerra este estado para deixar o handler de PDF (receber_cv) assumir

async def receber_cv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa o CV, salva o perfil inicial e pede o nome."""
    user_id = update.message.from_user.id
    
    try:
        pdf_file = await context.bot.get_file(update.message.document.file_id)
        pdf_bytes = io.BytesIO(await pdf_file.download_as_bytearray())
        await update.message.reply_text("Currículo recebido! Analisando as informações com a IA... 🧠")

        texto_cv = extrair_texto_pdf(pdf_bytes)
        if not texto_cv:
            await update.message.reply_text("❌ Erro: Não consegui ler o texto do arquivo PDF. Tente enviar um arquivo diferente.")
            return ConversationHandler.END

        perfil_ia = analisar_cv(texto_cv)
        if not perfil_ia:
            await update.message.reply_text("❌ Erro: A análise do currículo falhou. Tente novamente mais tarde.")
            return ConversationHandler.END
        
        # Salva o perfil extraído pela IA
        salvar_perfil(user_id, perfil_ia)
        context.user_data['perfil'] = perfil_ia 

        # Verifica se o usuário já tinha nome/telefone salvos para não perguntar de novo se for apenas atualização de CV
        perfil_banco = carregar_perfil(user_id)
        if perfil_banco and perfil_banco.get('nome') and perfil_banco.get('telefone'):
             # Se já tem cadastro completo, só avisa e vai pra localização
             # Atualiza o contexto com os dados completos do banco (que agora tem o cargo novo da IA + nome antigo)
             context.user_data['perfil'] = carregar_perfil(user_id)
             await update.message.reply_text(
                f"Currículo atualizado! Novo cargo detectado: *{perfil_ia.get('cargo_ideal')}*.\n"
                f"Como já tenho seus dados, informe a *localização* para a busca.",
                parse_mode='Markdown'
             )
             return AGUARDANDO_LOCALIZACAO

        await update.message.reply_text(
            f"Análise concluída! Cargo ideal identificado: *{perfil_ia.get('cargo_ideal', 'N/A')}*\n\n"
            "Para personalizar sua experiência, vamos completar seu cadastro.",
            parse_mode='Markdown'
        )
        await update.message.reply_text("Qual é o seu *primeiro nome*?", parse_mode='Markdown')
        
        return AGUARDANDO_NOME 

    except Exception as e:
        print(f"Erro crítico ao processar o CV: {e}")
        await update.message.reply_text("❌ Ocorreu um erro inesperado. Tente novamente.")
        return ConversationHandler.END

async def receber_nome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Salva o nome e pede o sobrenome."""
    user_id = update.message.from_user.id
    nome = update.message.text.strip()
    
    salvar_perfil(user_id, {"nome": nome})
    
    await update.message.reply_text(f"Ótimo, {nome}! Agora, qual o seu *sobrenome*?", parse_mode='Markdown')
    
    return AGUARDANDO_SOBRENOME

async def receber_sobrenome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Salva o sobrenome e pede o telefone."""
    user_id = update.message.from_user.id
    sobrenome = update.message.text.strip()

    salvar_perfil(user_id, {"sobrenome": sobrenome})

    await update.message.reply_text(
        "Certo. Agora, por favor, informe seu *telefone* (com DDD).\n"
        "Se não quiser informar, digite /pular.",
        parse_mode='Markdown'
    )

    return AGUARDANDO_TELEFONE

async def receber_telefone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Valida, salva o telefone e pede a localização."""
    user_id = update.message.from_user.id
    telefone = update.message.text.strip()

    if not _validar_telefone(telefone):
        await update.message.reply_text("❌ Telefone inválido. Por favor, tente novamente no formato (XX) XXXXX-XXXX ou digite /pular.")
        return AGUARDANDO_TELEFONE 

    salvar_perfil(user_id, {"telefone": telefone})
    
    await update.message.reply_text(
        "✅ Telefone salvo com sucesso!\n\n"
        "Para finalizar, informe a *localização* onde deseja buscar vagas (ex: São Paulo, Remoto, etc.).",
        parse_mode='Markdown'
    )
    
    return AGUARDANDO_LOCALIZACAO

async def pular_telefone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Pula a etapa do telefone e pede a localização."""
    await update.message.reply_text(
        "Ok, pulamos o telefone.\n\n"
        "Agora, informe a *localização* para a busca de vagas (ex: São Paulo, Remoto).",
        parse_mode='Markdown'
    )
    return AGUARDANDO_LOCALIZACAO

async def receber_localizacao_e_buscar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe a localização, busca as vagas e encerra a conversa."""
    localizacao = update.message.text.strip()
    perfil = context.user_data.get('perfil')

    if not perfil or 'cargo_ideal' not in perfil:
        await update.message.reply_text("❌ Algo deu errado, não encontrei seu perfil. Por favor, digite /start e comece novamente.")
        return ConversationHandler.END

    cargo = perfil['cargo_ideal']
    await update.message.reply_text(f"🚀 Buscando vagas para *{cargo}* em *{localizacao}*. Isso pode levar um momento...", parse_mode='Markdown')

    vagas = buscar_vagas(cargo, localizacao)

    if vagas:
        lista_vagas_texto = []
        for vaga in vagas[:5]: 
            # Parse HTML para evitar erros com caracteres especiais em links
            vaga_formatada = (
                f"<b>{vaga['titulo']}</b>\n"
                f"<i>{vaga['empresa']}</i>\n"
                f"📍 {vaga['local']}\n"
                f"<a href='{vaga['link']}'>Ver Vaga</a>"
            )
            lista_vagas_texto.append(vaga_formatada)
        
        separador = "\n\n" + ("-" * 25) + "\n\n"
        corpo_mensagem = separador.join(lista_vagas_texto)
        mensagem_final = f"✅ Busca finalizada! Aqui estão as 5 principais:\n\n{corpo_mensagem}"
        
        await update.message.reply_text(mensagem_final, parse_mode='HTML', disable_web_page_preview=True)
    else:
        await update.message.reply_text("😕 Nenhuma vaga encontrada para os critérios informados.")

    await update.message.reply_text("Busca encerrada. Digite /start se quiser fazer uma nova busca!")
    
    return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela e encerra a conversa."""
    await update.message.reply_text("Tudo bem, conversa encerrada. Se precisar de algo, é só chamar!")
    return ConversationHandler.END