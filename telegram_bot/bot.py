from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from config import TELEGRAM_BOT_TOKEN
from . import handlers


def run():
    """Inicia o bot do Telegram para receber atualiazações."""
    if not TELEGRAM_BOT_TOKEN:
        print("Erro: TELEGRAM_API_TOKEN não está definido. Verifique!")
        return
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Registra os handlers para cada tipo de interação.
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(MessageHandler(filters.Document.PDF, handlers.tratar_documento))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.tratar_localizacao))

    print("Bot do Telegram iniciado. Pressione Ctrl+C para encerrar.")

    # Inicia o bot para que ele comece a receber mensagens.
    application.run_polling()