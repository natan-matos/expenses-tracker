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
from collections import defaultdict

# Connect to AWS dynamodb
access_key = os.getenv('AWS_ACCESS_KEY_ID')
secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')

session = boto3.Session(
    aws_access_key_id = access_key,
    aws_secret_access_key = secret_key,
    )
dynamodb = session.resource( 'dynamodb', region_name='us-east-2')
table = dynamodb.Table( 'ExpensesTable' )


# data = table.scan(FilterExpression=Key['Date'])
data = table.scan()
print(data)