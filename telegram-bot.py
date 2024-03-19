from decimal import Decimal
import telebot
from telebot import types
import boto3
from boto3.dynamodb.conditions import Attr, Key
import datetime
import pandas as pd
import os
import uuid
from flask import Flask, request

# constants
TOKEN = '6497461668:AAHIy0QYyuGePFj-xTxaBxnxiPMtWzLzuRw'
URL = f'https://api.telegram.org/bot{TOKEN}/'

#-------------------------------------------------------------------
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Connect to AWS dynamodb
access_key = os.getenv('AWS_ACCESS_KEY_ID')
secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')

session = boto3.Session(
    aws_access_key_id = access_key,
    aws_secret_access_key = secret_key,
    )
dynamodb = session.resource( 'dynamodb', region_name='us-east-2')
table = dynamodb.Table( 'ExpensesTable' )

user_data = {}

@app.route('/', methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f'{URL}{TOKEN}')
    return "!", 200

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    itembtn1 = types.InlineKeyboardButton('Input new values', callback_data='input')
    itembtn2 = types.InlineKeyboardButton('Query total expenses', callback_data='query')
    itembtn3 = types.InlineKeyboardButton('Exit', callback_data='exit')
    markup.add(itembtn1, itembtn2, itembtn3)
    bot.send_message(message.chat.id, "Choose an option:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'input')
def ask_for_value(call):
    sent = bot.send_message(call.message.chat.id, 'Please enter the value:')
    bot.register_next_step_handler(sent, process_value_step)

def process_value_step(message):
    user_data['Expense'] = message.text
    markup = types.InlineKeyboardMarkup()
    tags = ['mercado', 'farmacia', 'lanche', 'casa', 'outro']
    for tag in tags:
        markup.add(types.InlineKeyboardButton(tag, callback_data=f'tag_{tag}'))
    bot.send_message(message.chat.id, 'Please choose a tag:', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('tag_'))
def process_tag_step(call):
    user_data['Tag'] = call.data.split('_')[1]
    user_data['Date'] = datetime.datetime.now().strftime('%Y-%m-%d')
    user_data['id'] = str(uuid.uuid4())
    table.put_item(Item=user_data)
    bot.send_message(call.message.chat.id, 'Value saved successfully.')
    send_welcome(call.message)

@bot.callback_query_handler(func=lambda call: call.data == 'query')
def ask_for_month(call):
    sent = bot.send_message(call.message.chat.id, 'Please enter the Month and Year (format: MM-YYYY):')
    bot.register_next_step_handler(sent, process_month_step)

def process_month_step(message):
    month, year = map(int, message.text.split('-'))
    response = table.scan(
        FilterExpression=Key('Date').begins_with(f'{year}-{month:02d}')
    )
    total_expenses = sum(float(item['Expense']) for item in response['Items'])
    bot.send_message(message.chat.id, f'Total expenses for {month}-{year}: {total_expenses}')
    send_welcome(message)

@bot.callback_query_handler(func=lambda call: call.data == 'exit')
def process_exit_step(call):
    send_welcome(call.message)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
