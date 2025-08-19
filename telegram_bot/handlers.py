#importar as bilbiotecas necessárias
import io
import asyncio
from telegram import Update, InputFile
from telegram.ext import ContextTypes

from core.pdf_parser import extrair_texto_pdf
from core.cv_analyzer import analisar_cv
from core.job_scraper import buscar_vagas
from profiles.profile_manager import inicializar_banco, salvar_perfil, carregar_perfil


async def start(update : Update, context: ContextTypes.DEFAULT_TYPE):
    "Responde ao comando /start"
    await update.message.reply_text(
        "Bem-vindo ao seu asssistente de busca de vagas!\n" \
        "Para começar, envie seu currículo em PDF"
    )

async def tratar_documento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    "Processa o documento enviado pelo usuário."
    user_id = update.message.from_user.id
    pdf_file = await context.bot.get_file(update.message.document.file_id)
    pdf_bytes = io.BytesIO(await pdf_file.download_as_bytearray()) # Lê o arquivo PDF como bytes para melhorar a segurança
    await update.message.reply_text("Recebido! Processando seu currículo...")

    try:
        text_cv = extrair_texto_pdf(pdf_bytes)
        if not text_cv:
            await update.message.reply_text("Erro: Não foi possível ler o arquivo PDF. Verifique se ele está no formato correto.")
            return
        
        analise_cv = analisar_cv(text_cv)
        if not analise_cv:
            await update.message.reply_text("Erro: Falha na análise do currículo.")
            return
        
        salvar_perfil(user_id, analise_cv)
        cargo = analise_cv.get("cargo_ideal", "N/A")

        await update.message.reply_text(
            f"Análise concluída.\n"
            f"Cargo ideal identificado: *{cargo}*\n\n"
            "Agora, informe a *localização* para a busca (ex: Remoto, São Paulo).",
            parse_mode='Markdown'
        )
        # Armazena o perfil para uso posterior
        context.user_data['cargo_para_busca'] = cargo

    except Exception as e:
        print(f"Erro crítico ao processar o documento: {e}")
        await update.message.reply_text("Erro: Ocorreu um problema ao processar o documento. Tente novamente.")
    
async def tratar_localizacao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    "Processa a localização informada pelo usuário."
    user_id = update.message.from_user.id
    localizacao = update.message.text.strip()

    if 'cargo_para_busca' not in context.user_data:
        await update.message.reply_text("Erro: Nenhum perfil encontrado. Por favor, envie seu currículo primeiro.")
        return

    cargo = context.user_data['cargo_para_busca']
    vagas = buscar_vagas(cargo, localizacao)

    if not vagas:
        await update.message.reply_text(f"Nenhuma vaga encontrada para o cargo *{cargo}* em *{localizacao}*.", parse_mode='Markdown')
        return

    resposta = f"Vagas encontradas para o cargo *{cargo}* em *{localizacao}*:\n\n"
    for vaga in vagas:
        resposta += f"- {vaga}\n"

    await update.message.reply_text(resposta, parse_mode='Markdown')

async def tratar_localizacao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lida com a localização informada pelo usuário."""
    if 'cargo_para_busca' not in context.user_data:
        await update.message.reply_text("Por favor, primeiro envie seu currículo para análise.")
        return
    
    localizacao = update.message.text
    cargo = context.user_data['cargo_para_busca']

    await update.message.reply_text(f"Ok! 🚀 Buscando as melhores oportunidades para *{cargo}* em *{localizacao}*. Um momento, por favor...", parse_mode='Markdown')
    

    vagas = buscar_vagas(cargo, localizacao)

    if vagas:
        lista_de_vagas_texto = []
        for vaga in vagas[:5]:
            vaga_formatada = (
                f"*{vaga['titulo']}*\n"
                f"_{vaga['empresa']}_\n"
                f"📍 {vaga['local']}\n"
                f"[Ver Vaga]({vaga['link']})"
            )
            lista_de_vagas_texto.append(vaga_formatada)
        
        # Define um separador claro entre cada vaga.
        separador = "\n\n" + ("-" * 25) + "\n\n"
        corpo_da_mensagem = separador.join(lista_de_vagas_texto)

        mensagem_final = f"Busca finalizada. {len(vagas)} vagas encontradas. Exibindo as principais:\n\n{corpo_da_mensagem}"

        # Envia a mensagem única e completa para o usuário.
        await update.message.reply_text(mensagem_final, parse_mode='Markdown', disable_web_page_preview=True)
    else:
        await update.message.reply_text("Nenhuma vaga foi encontrada para os critérios informados.")
    
   # Limpa o contexto para encerrar a conversa atual.
    context.user_data.clear()