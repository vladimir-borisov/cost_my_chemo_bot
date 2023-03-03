import os

SERVER_ADDRESS = 'https://30db-109-2522222-187-75.eu.ngrok.io'
TELEGRAM_BOT_TOKEN = '6116026507:AAH10R3OLovWxeKdAPYaH1j9BAdK7TvbLd0'

os.system(f'curl -F "url={SERVER_ADDRESS}" "https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"')