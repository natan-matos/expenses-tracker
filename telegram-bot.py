import datetime
import boto3
from decimal import Decimal
from flask import Flask, request, Response
import requests
import os
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

# constants
TOKEN = '6826005571:AAGTXt-l02duSH5nDRUzEMj2_gtWbOnXJg8'
URL = f'https://api.telegram.org/bot{TOKEN}/'

#--------------------------------------------------------------------------
def send_message( chat_id, text, reply_markup=None ):
    url = f'https://api.telegram.org/bot{TOKEN}/'
    url = url + f'sendMessage?chat_id={chat_id}'
    
    payload = {'text': text}
    if reply_markup:
        payload['reply_markup'] = reply_markup

    r = requests.post( url, json=payload )
    print( f'Staus Code{r.status_code}' )

    return None
#------------------------------------------------------------------------------
def parse_message( message ):
    chat_id = message['message']['chat']['id']
    value = message['message']['text']

    value = value.replace( '/', '' )

    try:
        value = float( value )
    except ValueError:
        value = 'error'
    return chat_id, value
#--------------------------------------------------------------------------------
def handle_command( chat_id, command ):
    if command == 'start':
        keyboard = InlineKeyboardMarkup( inline_keyboard=[
            [InlineKeyboardButton( text='Input new expenses', callback_data='input_expenses')],
            [InlineKeyboardButton( text='See total expenses for Month', callback_data='see_expenses')],
            [InlineKeyboardMarkup( text='Exit', callback_data='exit')]
        ])
        send_message( chat_id, 'Choose an Option:', reply_markup=keyboard )
    elif command == 'input_expenses':
        send_message( chat_id, 'Value added' )
        pass 
    elif command == 'see_expenses':
        send_message( chat_id, 'Total expenses:')
        pass
    elif command == 'exit':
        send_message(chat_id, 'Goodby')
        pass
#-----------------------------------------------------------------------------------------
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