from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext, ConversationHandler, MessageHandler, filters
import requests
import logging
import os


# Configuração de logging para depuração
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


# Função para autenticar na API do GLPI
def authenticate_glpi(api_url, user_token):
    headers = {
        'Authorization': f'user_token {user_token}',
    }
    
    try:
        logger.info(f'Tentando conectar à API em {api_url}/initSession')
        response = requests.get(f'{api_url}/initSession', headers=headers, timeout=60)
        response.raise_for_status()
        logger.info('Resposta recebida da API.')
        session_token = response.json().get('session_token')
        if not session_token:
            raise Exception('Sessão não foi iniciada. Token não retornado.')
        return session_token
    except requests.RequestException as e:
        logger.error(f'Erro ao autenticar: {e}')
        raise

# Função para criar uma sessão na API do GLPI
def create_session(api_url, user_token):
    session_token = authenticate_glpi(api_url, user_token)
    return session_token


# Função para criar um ticket na API do GLPI
def create_ticket(api_url: str, session_token: str, app_token: str, title: str, description: str, user_id: str) -> dict:
    headers = {
        'Content-Type': 'application/json',
        'App-Token': app_token,
        'Authorization': f'session_token {session_token}',
    }

    data = {
        "input": {
            "name": title,
            "content": description,
            "users_id_requester": user_id
        }
    }
    
    try:
        logger.info(f'Tentando criar ticket na API em {api_url}/Ticket')
        response = requests.post(f'{api_url}/Ticket', json=data, headers=headers, timeout=60)
        response.raise_for_status()
        logger.info('Ticket criado com sucesso.')
    except requests.RequestException as e:
        logger.error(f'Erro ao criar ticket: {e}')
        raise
    
    result = response.json()
    if 'id' not in result:
        logger.error('ID do ticket não retornado.')
        raise Exception('ID do ticket não retornado.')
    
    return result


# Configurações - TOKENS
API_URL = 'http://172.10.1.71/glpi/apirest.php/'
API_TOKEN = os.getenv('GLPI_API_TOKEN', 'Jvf5uHEb31AML874hsuk35hevDt8wjGKBWXZvsf1')
APP_TOKEN = os.getenv('GLPI_APP_TOKEN', 'suSIv5m8fW300bMnYj12TIE7Bcp1JU0SantcPr1t ')
USER_TOKEN = os.getenv('GLPI_USER_TOKEN', 'jSTThxI6nBdLCHKg0a9MDLzVHJHL7WDGlcDf0177')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '6693359099:AAGplQUrNOrUrG9kNcFXacdoQgmEJCNBc7w')
 

# Estados da Conversa
NAME, EMAIL, PREFERENCE_HOUR = range(3)

async def start(update: Update, context: CallbackContext) -> int:
    logger.info('Iniciando conversa: solicitando e-mail.')
    await update.message.reply_text('Bem-vindo! Por favor, informe seu E-mail.')
    return EMAIL

async def receive_email(update: Update, context: CallbackContext) -> int:
    context.user_data['email'] = update.message.text
    logger.info(f'E-mail recebido: {context.user_data["email"]}')
    await update.message.reply_text('Agora, informe seu nome completo:')
    return NAME

async def receive_name(update: Update, context: CallbackContext) -> int:
    context.user_data['name'] = update.message.text
    logger.info(f'Nome recebido: {context.user_data["name"]}')
    
    try:
        await update.message.reply_text('Qual seria o horário de sua preferência?')
    except Exception as e:
        logger.error(f'Erro ao enviar mensagem: {e}')
    
    return PREFERENCE_HOUR

async def receive_preference_hour(update: Update, context: CallbackContext) -> int:
    name = context.user_data.get('name')
    email = context.user_data.get('email')
    preference_hour = update.message.text
    logger.info(f'Nome: {name}')
    logger.info(f'E-mail: {email}')
    logger.info(f'Horário de preferência: {preference_hour}')

    
    title = "Novo Chamado"
    description = f"Nome: {name}\nE-mail: {email}\nHorário de preferência: {preference_hour}"
    
    try:
        session_token = authenticate_glpi(API_URL, USER_TOKEN)
        response = create_ticket(API_URL, session_token, APP_TOKEN, title, description, USER_TOKEN)
        await update.message.reply_text(f'Chamado criado com sucesso! ID: {response["id"]}')
    except requests.RequestException as e:
        await update.message.reply_text(f'Ocorreu um erro ao se comunicar com a API: {str(e)}')
        logger.error(f'Ocorreu um erro ao se comunicar com a API: {str(e)}')
    except Exception as e:
        await update.message.reply_text(f'Ocorreu um erro inesperado: {str(e)}')
        logger.error(f'Ocorreu um erro inesperado: {str(e)}')
    
    return ConversationHandler.END


def main():
    # Inicializa o Application com o token do bot do Telegram
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_email)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
            PREFERENCE_HOUR: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_preference_hour)]
        },
        fallbacks=[],
    )
    
    application.add_handler(conv_handler)
    
    application.run_polling()
    

if __name__ == '__main__':
    main()