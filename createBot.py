from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

#Config
API_URL = 'https://seu-glpi.com/apirest.php'
APP_TOKEN = 'seu-app-token'
USER_TOKEN = 'seu-user-token'

def start(update:Update, context: CallbackContext) -> None:
    update.message.reply_text('Bem-vindo! Use /ticket <título> <descrição> para abrir um chamado.')
    
def start(update:Update, context: CallbackContext) -> None:
    try:
        title = context.args[0]
        description = ''.join(context.args[1:])
        
        #Autenticação e abertura de chamado
        session_token = authenticate_glpi(API_URL, APP_TOKEN, USER_TOKEN)
        
        response = create_ticket(API_URL, session_token, APP_TOKEN, title, description, user_id=1)
        #substitua user_id pelo ID do usuario no glpi
        
        update.message.reply_text(f'Chamado criado com sucesso! ID:{response["id"]}')
    except Exception as e:
        update.message.reply_text(f'Ocorreu um erro: {str(e)}')