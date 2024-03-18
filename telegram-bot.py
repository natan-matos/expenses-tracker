import datetime
import boto3
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

# expenses, date & tags lists
expenses = []
date = []
valid_tags = []
#----------------------------------------------------------------------------
def store_data(expenses, date, tags, table):
    df = pd.DataFrame({
        'Expense': expenses,
        'Date': date,
        'Tag': tags
    })

    for index, row in df.iterrows():
        # Generate a unique ID for each item
        item_id = str(uuid.uuid4())

        table.put_item(
            Item={
                'id': item_id,
                'Date': row['Date'],
                'Expense': Decimal(str(row['Expense'])),
                'Tag': row['Tag']
            }
        )
    expenses.clear()
    date.clear()
    tags.clear()

#------------------------------------------------------------------------------
@bot.message_handler(commands=['1'])
def option1(message):
    msg = bot.send_message(message.chat.id, 'Insert the value:')
    bot.register_next_step_handler(msg, process_expense_step)

def process_expense_step(message):
    try:
        expense = float(message.text)

        msg = bot.send_message(message.chat.id, 'Insert Tag: ')

        bot.register_next_step_handler(msg, lambda message: process_tag_step(message, expense))
    except ValueError:
        bot.reply_to(message, 'Value Invalid!')

def process_tag_step(message, expense):
    tag = message.text

    valid_tags.append(tag)
    expenses.append(expense)

    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    date.append(current_date)
    store_data(expenses, date, valid_tags, table)

    bot.reply_to(message, 'Value Added')
    show_menu( message )

#-------------------------------------------------------------------------
# Define a dictionary to store the states of the users
user_states = {}

@bot.message_handler(commands=['2'])
def option2( message ):
    # Set the user's state to 'AWAITING_DATE'
    user_states[message.chat.id] = 'AWAITING_DATE'
    bot.reply_to(message, "Insira Mês e Ano assim: 3 2024")

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'AWAITING_DATE')
def handle_date(message):
    # Split the message text into parts
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "eueu Mês e Ano assim: 3 2024")
        return

    # Parse the month and year from the message
    month = int(parts[0])
    year = int(parts[1])

    # Define the function to get the expenses
    def get_expenses_for_month(month, year, table):
        response = table.scan()
        items = response['Items']
        total = 0
        for item in items:
            date = datetime.datetime.strptime(item['Date'], '%Y-%m-%d')

            if date.month == month and date.year == year:
                total += float(item['Expense'])
        return total

    # Call the function to get the expenses
    total = get_expenses_for_month(month, year, table)

    # Send a reply with the total expenses
    bot.reply_to(message, f"Total expenses for {month}/{year}: {total}")
    show_menu( message )

    # Reset the user's state
    user_states[message.chat.id] = None


#------------------------------------------------------------------------------

def check( message ):
    return True

def show_menu( message ):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row_width = 2
    keyboard.add( types.InlineKeyboardButton('Inserir novos valores', callback_data='op1' ) )
    keyboard.add( types.InlineKeyboardButton('Consultar Gastos', callback_data='op2' ) )
    keyboard.add( types.InlineKeyboardButton('Sair', callback_data='op3' ) )
    bot.send_message( message.chat.id, 'Escolha:', reply_markup=keyboard )

@bot.message_handler( commands=['start'] )
def start( message ):
    show_menu( message )

@bot.callback_query_handler( func=lambda call: True )
def callback_query( call ):
    if call.data == 'op1':
        option1( call.message )
    elif call.data == 'op2':
        bot.answer_callback_query( call.id, 'Consultar Gastos' )
        option2( call.message )
        
    elif call.data == 'op3':
        bot.answer_callback_query( call.id, 'Sair' )
        

@bot.message_handler( commands=['1'] )
def option1( message ):
    msg = bot.send_message( message.chat.id, 'Insert the value:' )
    bot.register_next_step_handler( msg, process_expense_step )



bot.infinity_polling()

