import requests, json

url = 'https://ca-sereneapp.braveisland-f409e30d.southeastasia.azurecontainerapps.io/'

# Mendapatkan token
def get_token():
    token_url = url+'auth/token'
    token_response = requests.post(token_url, data={'username': 'johndoe', 'password': 'password123'})
    token = token_response.json().get('access_token')
    return token

# Menggunakan token untuk mengakses endpoint tertentu
def get_psychologist_list():
    headers = {'Authorization': f'Bearer {get_token()}'}
    psychologist = requests.get(url+'psychologist/', headers=headers)
    return psychologist.json()

def get_user_list():
    headers = {'Authorization': f'Bearer {get_token()}'}
    user = requests.get(url+'user/', headers=headers)
    return user.json()