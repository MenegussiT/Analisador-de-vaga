
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    filters,
    ConversationHandler
)
from config import TELEGRAM_BOT_TOKEN
from . import handlers

def run():
    """Inicia o bot do Telegram e configura o ConversationHandler."""
    if not TELEGRAM_BOT_TOKEN:
        print("Erro: TELEGRAM_BOT_TOKEN não está definido. Verifique!")
        return
        
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # --- Configuração do ConversationHandler ---
    conv_handler = ConversationHandler(
        entry_points=[
            # A conversa pode começar com o comando /start ou diretamente com o envio de um PDF
            CommandHandler("start", handlers.start),
            MessageHandler(filters.Document.PDF, handlers.receber_cv)
        ],
        states={
            # Mapeia cada estado para a função de handler correspondente
            handlers.AGUARDANDO_NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.receber_nome)],
            handlers.AGUARDANDO_SOBRENOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.receber_sobrenome)],
            handlers.AGUARDANDO_TELEFONE: [
                CommandHandler("pular", handlers.pular_telefone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.receber_telefone)
            ],
            handlers.AGUARDANDO_LOCALIZACAO: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.receber_localizacao_e_buscar)],
        },
        fallbacks=[
            # Define um comando de "saída de emergência"
            CommandHandler("cancelar", handlers.cancelar)
        ]
    )

    # Adiciona o ConversationHandler ao bot. Ele gerenciará todo o fluxo.
    application.add_handler(conv_handler)
    
    # Adiciona um handler para o comando /start fora da conversa, para o caso do usuário se perder.
    application.add_handler(CommandHandler("start", handlers.start))

    print("Bot do Telegram iniciado com ConversationHandler. Pressione Ctrl+C para encerrar.")
    application.run_polling()