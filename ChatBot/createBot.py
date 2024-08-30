from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import requests

# Autenticação na API do GLPI
def authenticate_glpi(api_url: str, app_token: str, user_token: str) -> str:
    headers = {
        'Content-Type': 'application/json',
        'App-Token': app_token,
        'Authorization': f'user_token {user_token}',
    }
    
    response = requests.get(f'{api_url}/initSession', headers=headers)
    
    if response.status_code != 200:
        raise Exception(f'Erro ao autenticar: {response.text}')
    
    return response.json().get('session_token')

# Criação de ticket
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
    
    response = requests.post(f'{api_url}/Ticket', json=data, headers=headers)
    
    if response.status_code != 201:
        raise Exception(f'Erro ao criar ticket: {response.text}')
    
    return response.json()

# Configurações
API_URL = 'http://172.10.1.71/glpi/apirest.php/'
APP_TOKEN = 'suSIv5m8fW300bMnYj12TIE7Bcp1JU0SantcPr1t'
USER_TOKEN = 'lVCnekYcMtXWnDKA3P5rW2OvhMThhYzB4erEH4Id'
TELEGRAM_BOT_TOKEN = '6693359099:AAGplQUrNOrUrG9kNcFXacdoQgmEJCNBc7w'

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Bem-vindo! Use /ticket <título> <descrição> para abrir um chamado.')

def ticket(update: Update, context: CallbackContext) -> None:
    try:
        if len(context.args) < 2:
            update.message.reply_text('Uso incorreto. Use /ticket <título> <descrição>.')
            return
        
        title = context.args[0]
        description = ' '.join(context.args[1:])
        
        # Autenticação e abertura de chamado
        session_token = authenticate_glpi(API_URL, APP_TOKEN, USER_TOKEN)
        response = create_ticket(API_URL, session_token, APP_TOKEN, title, description, lVCnekYcMtXWnDKA3P5rW2OvhMThhYzB4erEH4Id=1)
        
        update.message.reply_text(f'Chamado criado com sucesso! ID: {response["id"]}')
    except Exception as e:
        update.message.reply_text(f'Ocorreu um erro: {str(e)}')

def main():
    # Inicializa o Updater com o token do bot do Telegram
    updater = Updater(TELEGRAM_BOT_TOKEN)
    
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("ticket", ticket))
    
    updater.start_polling()
    
    updater.idle()

if __name__ == '__main__':
    main()
