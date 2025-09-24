import logging
import os
import yt_dlp
import uuid
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# --- CONFIGURAÇÕES ---
TOKEN = '8265037048:AAHU9ModuYSrsm2zVxb8-FiKxbQF2zr4064'
SENHA_DO_BOT = 'minha_senha_secreta'

usuarios_autenticados = set()

# --- HANDLERS DE COMANDOS E MENSAGENS ---

async def start(update: Update, context) -> None:
    await update.message.reply_text('Olá! Este bot é protegido por senha. Por favor, envie a senha para ter acesso, usando o comando: /acessar <sua_senha>')

async def acessar(update: Update, context) -> None:
    if not context.args:
        await update.message.reply_text('Por favor, use o comando assim: /acessar <sua_senha>')
        return

    senha_digitada = context.args[0]
    user_id = update.effective_user.id

    if senha_digitada == SENHA_DO_BOT:
        usuarios_autenticados.add(user_id)
        await update.message.reply_text('Acesso concedido! Agora você pode enviar links do YouTube para download.')
        logging.info(f"Usuário {user_id} autenticado com sucesso.")
    else:
        await update.message.reply_text('Senha incorreta. Acesso negado.')
        logging.warning(f"Tentativa de acesso negado para o usuário {user_id}.")

async def download_video(update: Update, context) -> None:
    user_id = update.effective_user.id

    if user_id not in usuarios_autenticados:
        await update.message.reply_text('Você precisa se autenticar com a senha primeiro. Use o comando: /acessar <sua_senha>')
        return

    url = update.message.text
    chat_id = update.message.chat_id
    file_path = None

    try:
        await context.bot.send_message(chat_id=chat_id, text='Aguarde um momento... O download pode levar alguns minutos.')

        file_name = str(uuid.uuid4())
        file_path = f"{file_name}.mp4"

        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': file_path,
            'merge_output_format': 'mp4',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            title = info_dict.get('title', 'Vídeo')
            logging.info(f"Vídeo '{title}' baixado com sucesso.")

        await context.bot.send_video(
            chat_id=chat_id, 
            video=open(file_path, 'rb'),
            supports_streaming=True,
            caption=f'Vídeo baixado: {title}'
        )
        
        await context.bot.send_message(chat_id=chat_id, text='Vídeo baixado com sucesso!')

    except yt_dlp.utils.DownloadError as e:
        await context.bot.send_message(chat_id=chat_id, text=f'Não foi possível baixar o vídeo. Erro: {e}')
        logging.error(f"Erro ao baixar o vídeo: {e}")

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text='Ocorreu um erro inesperado. Por favor, tente novamente.')
        logging.error(f"Erro inesperado: {e}")

    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logging.info(f"Arquivo temporário {file_path} removido.")

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("acessar", acessar))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    application.run_polling()

if __name__ == '__main__':
    main()

