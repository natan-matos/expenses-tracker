import datetime
import boto3
from decimal import Decimal
import telebot
import pandas as pd

# constants
TOKEN = '6826005571:AAGTXt-l02duSH5nDRUzEMj2_gtWbOnXJg8'
URL = f'https://api.telegram.org/bot{TOKEN}/'

#-------------------------------------------------------------------
bot = telebot.TeleBot(TOKEN)

# Connect to AWS dynamodb
dynamodb = boto3.resource( 'dynamodb', region_name='us-east-2')
table = dynamodb.Table( 'ExpensesTable' )

# expenses and date lists
expenses = []
date = []

# define tags
valid_tags = []

#----------------------------------------------------------------------i
def store_data( expenses, date, tags, table ):
    df = pd.DataFrame({
        'Expense': expenses,
        'Date': date,
        'Tag': tags
    })

    for index, row in df.iterrows():
        table.put_item(
            Item={
                'Date': row['Date'],
                'Expense': Decimal( str( row['Expense'] ) ),
                'Tag': row['Tag']
            }
        )

#------------------------------------------------------------------------------
# @bot.message_handler(commands=['1'])
# def option1(message):
#     msg = bot.send_message(message.chat.id, 'Insert the value:')
#     bot.register_next_step_handler(msg, process_expense_step)

# def process_expense_step(message):
#     try:
#         expense = float(message.text)
#         expenses.append(expense)

#         current_date = datetime.datetime.now().strftime( '%Y-%m-%d' ) #datetime.now().strftime('%d-%m-%Y')
#         date.append(current_date)
#         store_data(expenses, date, table)

#         bot.reply_to(message, 'Value Added')
#     except ValueError:
#         bot.reply_to(message, 'Value Invalid!')

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

# def process_tag_step(message, expense):
#     tag = message.text
#     if tag not in valid_tags:
#         bot.reply_to(message, 'Invalid tag! Please use one of the following tags: ' + ', '.join(valid_tags))
#         return

#     valid_tags.append(tag)
#     expenses.append(expense)

#     current_date = datetime.datetime.now().strftime('%Y-%m-%d')
#     date.append(current_date)
#     store_data(expenses, date, valid_tags, table)

#     bot.reply_to(message, 'Value Added')
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

#--------------------------------------------------------------------------
# def send_message( chat_id, text, reply_markup=None ):
#     url = f'https://api.telegram.org/bot{TOKEN}/'
#     url = url + f'sendMessage?chat_id={chat_id}'
    
#     payload = {'text': text}
#     if reply_markup:
#         payload['reply_markup'] = reply_markup

#     r = requests.post( url, json=payload )
#     print( f'Staus Code{r.status_code}' )

#     return None
#------------------------------------------------------------------------------
# def parse_message( message ):
#     chat_id = message['message']['chat']['id']
#     value = message['message']['text']

#     value = value.replace( '/', '' )

#     try:
#         value = float( value )
#     except ValueError:
#         value = 'error'
#     return chat_id, value
#--------------------------------------------------------------------------------
# def handle_command( chat_id, command ):
#     if command == 'start':
#         keyboard = InlineKeyboardMarkup( inline_keyboard=[
#             [InlineKeyboardButton( text='Input new expenses', callback_data='input_expenses')],
#             [InlineKeyboardButton( text='See total expenses for Month', callback_data='see_expenses')],
#             [InlineKeyboardMarkup( text='Exit', callback_data='exit')]
#         ])
#         send_message( chat_id, 'Choose an Option:', reply_markup=keyboard )
#     elif command == 'input_expenses':
#         send_message( chat_id, 'Value added' )
#         pass 
#     elif command == 'see_expenses':
#         send_message( chat_id, 'Total expenses:')
#         pass
#     elif command == 'exit':
#         send_message(chat_id, 'Goodby')
#         pass
#-----------------------------------------------------------------------------------------
# API init
# app = Flask(__name__)

# @app.route( '/', methods=['GET', 'POST'] )
# def index():
#     if request.method == 'POST':
#         message = request.get_json()

#         chat_id, value = parse_message( message )

#         if value != 'error':
#             #write the value and date in the database
#             send_message( chat_id, 'Correct Value')
#             handle_command( chat_id, value )
#             return Response( 'OK', status=200 )
#         else:
#             send_message( chat_id, 'Invalid Value' )
#             return Response( 'Ok', status=200 )
    
#     else:
#         return '<h1> Expense Tracker Bot </h1>'


# if __name__ == '__main__':
#     port = os.environ.get( 'PORT', 5000)
#     app.run( host='0.0.0.0', port=port)