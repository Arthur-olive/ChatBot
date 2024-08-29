import requests
def authenticate_glpi(api_url, app_token, user_token):
    headers = {
        'Content-Type':'application/json',
        'App-Token': app_token,
        'Authorization':f'user_token{user_token}',
    }
    
    response = requests.get(f'{api_url}/initSession', headers=headers)
    return response.json()['session_token']

#Criação de ticket
def create_ticket(api_url, session_token, app_token, title, description,user_id):
    headers = {
        'Content_Type':'application/json',
        'App-Token':app_token,
        'Session-Token':session_token
    }
    
    data = {
        "input": {
            "name" : title,
            "content" : description,
            "users_id_requester" : user_id
        }
    }
    
    response = requests.post(f'{api_url}/Ticket',json=data, headers=headers)
    return response.json