import datetime
import boto3
from decimal import Decimal
from flask import Flask, request, Response
from Monthly2 import Month
import requests
import os

# constants
TOKEN = '6826005571:AAGTXt-l02duSH5nDRUzEMj2_gtWbOnXJg8'
URL = f'https://api.telegram.org/bot{TOKEN}/'

#chat id
# 627469904

# getMe - Bot info
# https://api.telegram.org/bot6826005571:AAGTXt-l02duSH5nDRUzEMj2_gtWbOnXJg8/getMe

# getUpdates - recive messages
# https://api.telegram.org/bot6826005571:AAGTXt-l02duSH5nDRUzEMj2_gtWbOnXJg8/getUpdates

# sendMessage
# https://api.telegram.org/bot6826005571:AAGTXt-l02duSH5nDRUzEMj2_gtWbOnXJg8/sendMessage?chat_id=627469904&text=I%27m%20working 

# setWebhook
# https://api.telegram.org/bot6826005571:AAGTXt-l02duSH5nDRUzEMj2_gtWbOnXJg8/setWebhook?url=https://c0feb63cc043f9.lhr.life

def send_message( chat_id, text ):
    url = f'https://api.telegram.org/bot{TOKEN}/'
    url = url + f'sendMessage?chat_id={chat_id}'

    r = requests.post( url, json={'text': text} )
    print( f'Staus Code{r.status_code}' )

    return None

def parse_message( message ):
    chat_id = message['message']['chat']['id']
    value = message['message']['text']

    value = value.replace( '/', '' )

    try:
        value = float( value )
    except ValueError:
        value = 'error'
    return chat_id, value




# API init
app = Flask(__name__)

@app.route( '/', methods=['GET', 'POST'] )
def index():
    if request.method == 'POST':
        message = request.get_json()

        chat_id, value = parse_message( message )

        if value != 'error':
            #write the value and date in the database
            send_message( chat_id, 'Correct Value')
            return Response( 'OK', status=200 )
        else:
            send_message( chat_id, 'Invalid Value' )
            return Response( 'Ok', status=200 )
    
    else:
        return '<h1> Expense Tracker Bot </h1>'


if __name__ == '__main__':
    port = os.environ.get( 'PORT', 5000)
    app.run( host='0.0.0.0', port=port)