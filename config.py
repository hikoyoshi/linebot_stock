#-*- coding:utf-8 -*-
from flask import Flask
import os
from linebot import (
    LineBotApi, WebhookHandler
)

LINEBOTAPI = LineBotApi(os.getenv('LINE_BOT_CHANNEL_ACCESS_TOKEN'))
HANDLER = WebhookHandler(os.getenv('LINE_BOT_CHANNEL_ACCESS_SECRET'))

STOCK_URL ='http://finance.google.com/finance/info'
DB_URL = os.getenv('MOGODB_STOCK_URL')
