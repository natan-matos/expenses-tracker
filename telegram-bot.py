import datetime
import boto3
from boto3.dynamodb.conditions import Attr, Key
from decimal import Decimal
import telebot
from telebot import types
import pandas as pd
import os
import uuid

# constants
TOKEN = '6826005571:AAGTXt-l02duSH5nDRUzEMj2_gtWbOnXJg8'
URL = f'https://api.telegram.org/bot{TOKEN}/'

#-------------------------------------------------------------------
bot = telebot.TeleBot(TOKEN)

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

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    itembtn1 = types.KeyboardButton('Input new values')
    itembtn2 = types.KeyboardButton('Query total expenses')
    itembtn3 = types.KeyboardButton('Exit')
    markup.add(itembtn1, itembtn2, itembtn3)
    bot.send_message(message.chat.id, "Choose an option:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == 'Input new values')
def ask_for_value(message):
    sent = bot.send_message(message.chat.id, 'Please enter the value:')
    bot.register_next_step_handler(sent, process_value_step)

def process_value_step(message):
    user_data['Expense'] = message.text
    markup = types.ReplyKeyboardMarkup(row_width=1)
    for i in range(1, 6):
        markup.add(types.KeyboardButton(f'Tag {i}'))
    sent = bot.send_message(message.chat.id, 'Please choose a tag:', reply_markup=markup)
    bot.register_next_step_handler(sent, process_tag_step)

def process_tag_step(message):
    user_data['Tag'] = message.text
    user_data['Date'] = datetime.datetime.now().strftime('%Y-%m-%d')
    user_data['id'] = str(uuid.uuid4())
    table.put_item(Item=user_data)
    bot.send_message(message.chat.id, 'Value saved successfully.')
    send_welcome(message)

@bot.message_handler(func=lambda message: message.text == 'Query total expenses')
def ask_for_month(message):
    sent = bot.send_message(message.chat.id, 'Please enter the Month and Year (format: MM-YYYY):')
    bot.register_next_step_handler(sent, process_month_step)

def process_month_step(message):
    month, year = map(int, message.text.split('-'))
    response = table.scan(
        FilterExpression=Key('Date').begins_with(f'{year}-{month:02d}')
    )
    total_expenses = sum(float(item['Expense']) for item in response['Items'])
    bot.send_message(message.chat.id, f'Total expenses for {month}-{year}: {total_expenses}')
    send_welcome(message)

@bot.message_handler(func=lambda message: message.text == 'Exit')
def process_exit_step(message):
    send_welcome(message)

bot.polling()