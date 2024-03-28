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

@app.route(f'/', methods=['POST'])
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
    itembtn1 = types.InlineKeyboardButton('Novos valores', callback_data='input')
    itembtn2 = types.InlineKeyboardButton('Consultar Gastos', callback_data='query')
    itembtn3 = types.InlineKeyboardButton('Exit', callback_data='exit')
    markup.add(itembtn1, itembtn2, itembtn3)
    bot.send_message(message.chat.id, "Escolha uma opção:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'input')
def ask_for_value(call):
    sent = bot.send_message(call.message.chat.id, 'Insira um valor:')
    bot.register_next_step_handler(sent, process_value_step)

def process_value_step(message):
    user_data['Expense'] = message.text
    markup = types.InlineKeyboardMarkup()
    tags = ['mercado', 'farmacia', 'lanche', 'casa', 'outro']
    for tag in tags:
        markup.add(types.InlineKeyboardButton(tag, callback_data=f'tag_{tag}'))
    bot.send_message(message.chat.id, 'Escolha uma tag:', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('tag_'))
def process_tag_step(call):
    user_data['Tag'] = call.data.split('_')[1]
    user_data['Date'] = datetime.datetime.now().strftime('%Y-%m-%d')
    user_data['id'] = str(uuid.uuid4())
    table.put_item(Item=user_data)
    bot.send_message(call.message.chat.id, 'Valor salvo.')
    send_welcome(call.message)

def get_month():
    response = table.scan()
    data = response['Items']
    df = []
    for item in data:
        row = {
            'id': item['id'],
            'Date': item['Date'],
            'Expense': item['Expense'],
            'Tag': item['Tag']
        }
        df.append(row)
    df1 = pd.DataFrame( df )
    df1['Date'] = pd.to_datetime( df1['Date']).dt.normalize()
    df1['Month'] = df1['Date'].dt.month
    months = df1['Month'].unique()
    return months

@bot.callback_query_handler(func=lambda call: call.data == 'query')
def ask_for_month(call):
    # user_data['Expense'] = message.text
    markup = types.InlineKeyboardMarkup()
    tags = get_month()
    for tag in tags:
        markup.add(types.InlineKeyboardButton(tag, callback_data=tag))
    # bot.send_message(call.message.chat.id, 'Escolha uma tag:', reply_markup=markup)

    sent = bot.send_message(call.message.chat.id, 'Escolha o Mês', reply_markup=markup)
    bot.register_next_step_handler(sent, process_month_step)


def process_month_step(message):
    month, year = map(int, message.text.split('-'))

    response = table.scan(
        FilterExpression=Key('Date').begins_with(f'{year}-{month:02d}')
    )

    expenses_by_tag = {}
    for item in response['Items']:
        tag = item['Tag']
        expense = float(item['Expense'])
        expenses_by_tag.setdefault(tag, 0)  # Initialize tag if not present
        expenses_by_tag[tag] += expense

    # Format and send the grouped expenses
    bot.send_message(message.chat.id, f'Total Gastos em {month}-{year}:')
    for tag, total_expense in expenses_by_tag.items():
        bot.send_message(message.chat.id, f'- {tag}: {total_expense:.2f}')

<<<<<<< HEAD
<<<<<<< HEAD
=======
    # Calculate the percentage change for each tag
    for tag, expense in expenses_by_tag.items():
        prev_expense = prev_expenses_by_tag.get(tag, 0)
        if prev_expense > 0:
            percent_change = ((expense - prev_expense) / prev_expense) * 100
        else:
            percent_change = 100  # If there were no expenses in the previous month, consider it as a 100% increase
        bot.send_message(message.chat.id, f'{tag_emojis[tag]} {tag} em {month}-{year}: {expense} ({percent_change:+.2f}%)')

    bot.send_message(message.chat.id, f'Total Gastos em {month}-{year}: {total_expenses:+2f}')
>>>>>>> parent of 4dc5ab8 (decimal place set as 2)
=======
>>>>>>> parent of 26af02f (Merge branch 'hotfix')
    send_welcome(message)

@bot.callback_query_handler(func=lambda call: call.data == 'exit')
def process_exit_step(call):
    send_welcome(call.message)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
