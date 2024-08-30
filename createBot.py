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
def authenticate_glpi(api_url: str, app_token: str, user_token: str) -> str:
    headers = {
        'Content-Type': 'application/json',
        'App-Token': app_token,
        'Authorization': f'user_token {user_token}',
    }
    
    try:
        response = requests.get(f'{api_url}/initSession', headers=headers, timeout=10)  # Timeout de 10 segundos
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f'Erro ao autenticar: {e}')
        raise
    
    session_token = response.json().get('session_token')
    if not session_token:
        logger.error('Sessão não foi iniciada. Token não retornado.')
        raise Exception('Sessão não foi iniciada. Token não retornado.')
    
    return session_token

# Função para criar um ticket na API do GLPI
def create_ticket(api_url: str, session_token: str, app_token: str, title: str, description: str, user_id: str) -> dict:
    headers = {
        'Content-Type': 'application/json',
        'App-Token': app_token,
        'Session-Token': session_token
    }
    
    data = {
        "input": {
            "name": title,
            "content": description,
            "users_id_requester": user_id
        }
    }
    
    try:
        response = requests.post(f'{api_url}/Ticket', json=data, headers=headers)  # Timeout de 10 segundos
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f'Erro ao criar ticket: {e}')
        raise
    
    result = response.json()
    if 'id' not in result:
        logger.error('ID do ticket não retornado.')
        raise Exception('ID do ticket não retornado.')
    
    return result

# Configurações
API_URL = 'http://172.10.1.71/glpi/apirest.php'
APP_TOKEN = os.getenv('GLPI_APP_TOKEN', 'suSIv5m8fW300bMnYj12TIE7Bcp1JU0SantcPr1t')
USER_TOKEN = os.getenv('GLPI_USER_TOKEN', 'lVCnekYcMtXWnDKA3P5rW2OvhMThhYzB4erEH4Id')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '6693359099:AAGplQUrNOrUrG9kNcFXacdoQgmEJCNBc7w')

# Estados da Conversa
CPF, PREFERENCE_HOUR = range(2)

async def start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text('Bem-vindo! Por favor, informe seu CPF.')
    return CPF

async def receive_cpf(update: Update, context: CallbackContext) -> int:
    context.user_data['cpf'] = update.message.text
    await update.message.reply_text('Qual seria o horário de sua preferência?')
    return PREFERENCE_HOUR

async def receive_preference_hour(update: Update, context: CallbackContext) -> int:
    cpf = context.user_data.get('cpf')
    preference_hour = update.message.text
    
    title = "Novo Chamado"
    description = f"CPF: {cpf}\nHorário de preferência: {preference_hour}"
    
    try:
        # Autenticação e abertura de chamado
        session_token = authenticate_glpi(API_URL, APP_TOKEN, USER_TOKEN)
        response = create_ticket(API_URL, session_token, APP_TOKEN, title, description, USER_TOKEN)
        
        await update.message.reply_text(f'Chamado criado com sucesso! ID: {response["id"]}')
    except Exception as e:
        await update.message.reply_text(f'Ocorreu um erro: {str(e)}')
        logger.error(f'Ocorreu um erro: {str(e)}')
    
    return ConversationHandler.END

def main():
    # Inicializa o Application com o token do bot do Telegram
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Cria o ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CPF: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_cpf)],
            PREFERENCE_HOUR: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_preference_hour)],
        },
        fallbacks=[],
    )
    
    # Adiciona handlers
    application.add_handler(conv_handler)
    
    # Inicia o polling
    application.run_polling()

if __name__ == '__main__':
    main()
