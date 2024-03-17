import datetime
import boto3
from decimal import Decimal
import telebot
import pandas as pd
import os

# constants
TOKEN = '6826005571:AAGTXt-l02duSH5nDRUzEMj2_gtWbOnXJg8'
URL = f'https://api.telegram.org/bot{TOKEN}/'

#-------------------------------------------------------------------
bot = telebot.TeleBot(TOKEN)

# Connect to AWS dynamodb
access_key = os.getenv('AWS_ACCESS_KEY_ID')
secret_key= os.getenv('AWS_SECRET_ACCESS_KEY')

session = boto3.Session(
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    )
dynamodb = session.resource( 'dynamodb', region_name='us-east-2')
table = dynamodb.Table( 'ExpensesTable' )

# expenses and date lists
expenses = []
date = []

# define tags
valid_tags = []

#----------------------------------------------------------------------i
# def store_data( expenses, date, tags, table ):
#     df = pd.DataFrame({
#         'Expense': expenses,
#         'Date': date,
#         'Tag': tags
#     })

#     for index, row in df.iterrows():
#         table.put_item(
#             Item={
#                 'Date': row['Date'],
#                 'Expense': Decimal( str( row['Expense'] ) ),
#                 'Tag': row['Tag']
#             }
#         )
def store_data(expenses, date, tags, table):
    # Retrieve existing data
    response = table.scan()
    existing_items = response['Items']
    
    # Merge existing data with new data
    new_data = []
    for exp, dt, tag in zip(expenses, date, tags):
        new_item = {
            'Date': dt,
            'Expense': Decimal(str(exp)),
            'Tag': tag
        }
        new_data.append(new_item)
    all_items = existing_items + new_data

    # Update table with new merged data
    with table.batch_writer() as batch:
        for item in all_items:
            batch.put_item(Item=item)


#------------------------------------------------------------------------------
@bot.message_handler(commands=['1'])
def option1(message):
    msg = bot.send_message(message.chat.id, 'Insert the value:')
    bot.register_next_step_handler(msg, process_expense_step)

def process_expense_step(message):
    try:
        expense = float(message.text)

        msg = bot.send_message(message.chat.id, 'Insert the tag:')
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


#-------------------------------------------------------------------------
# Define a dictionary to store the states of the users
user_states = {}

@bot.message_handler(commands=['2'])
def handle_expenses_command(message):
    # Set the user's state to 'AWAITING_DATE'
    user_states[message.chat.id] = 'AWAITING_DATE'
    bot.reply_to(message, "Please provide a month and year. '3 2024'")

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'AWAITING_DATE')
def handle_date(message):
    # Split the message text into parts
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "Please provide a month and year. '3 2024'")
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

    # Reset the user's state
    user_states[message.chat.id] = None


#---------------------------------------------------------------------------
@bot.message_handler( commands=['3'] )
def option3( message ):
    bot.reply_to( message, 'Goodbye' )

#------------------------------------------------------------------------------


def check( message ):
    return True

@bot.message_handler( func=check )
def send_message( message ):
    text = """
    Choose an Option:
    /1 Input new values
    /2 See total expenses on month
    /3 Exit"""
    bot.reply_to( message, text )

bot.polling()

