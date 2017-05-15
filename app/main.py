#-*- coding:utf-8 -*-
# encoding: utf-8
from __future__ import unicode_literals
from app import app
from flask import Flask, request,abort
from pymongo import *
from bson.json_util import dumps
import json,sys,os,time,requests,random,re,datetime,signal
import requests
reload(sys)
sys.setdefaultencoding("utf-8")

from linebot.exceptions import (
    InvalidSignatureError
)

from linebot.models import *

handler = app.config['HANDLER']
line_bot_api = app.config['LINEBOTAPI']

url = app.config['STOCK_URL']
db_url = app.config['DB_URL']

client =  MongoClient(db_url)
db = client['stockdb']

stat ={}

@app.route('/',methods=["GET"])
def hello():
    return "hello World!!!"

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

def Usage(event):
    push_msg(event,"add:stock_code\n ex -> add:0050 (目前只能單張增加)\
                    \ndel:stock_code\n ex -> del:0050 (目前只能單張刪除)\
                    \n/stocks  查詢已登記的股票\
                    \n/reltime 目前所選的股票即時報價\
                    \n/start  啟動自動看盤功能，當漲幅超過5%下跌超過4%時會給予提醒\
                    \n預設於下午1:30分收盤時自動停止\
                    \n/end  手動結束自動看盤\
                    \n--h或/help看使用說明\
                    \n\nPS：群組暫不開放以上功能")

def Get_Stock(code):
    stack_code = "TPE:{0}".format(code)
    params = {"client":"ig", "q":stack_code}
    try:
        r = requests.get(url, params = params )
        r_slipt = r.text[3:] #remove '//'
        data = json.loads(r_slipt)
    except ValueError as e:
        data = 'None'

    return data

#  get realtime stocks info
#
#  stock_code => 股票代號
#  data => 股票資料
#  uid => 使用者的名字及id
#
def Stockinfo(stock_code,data,uid):
    if data != 'None':
        stock_msg = u"股票:"+data[0]['t']+" | "+u"成交價："+data[0]['l']+" | "+u"漲跌幅度："+data[0]['cp']+"% | "+u"漲跌："+data[0]['c']+"元 | "+u"昨日收盤價："+data[0]['pcls_fix']
        return stock_msg
    else:
        #if can't get stock data will be remove from database
        db.users.delete_one({uid['name']:uid['uid'],'stock':stock_code})
        return stock_code+":"+"no found,remove this stock from database!!"


def Stockcp(stock_code,data,uid):
    stock_up = u'注意注意!!!{0}漲幅度超過5%了~~~'.format(stock_code)
    stock_down = u'注意注意!!!{0}下跌幅度超過4%了~~~'.format(stock_code)
    if data != 'None':
        stock_msg = u"股票:"+data[0]['t']+" | "+u"成交價："+data[0]['l']+" | "+u"漲跌幅度："+data[0]['cp']+"% | "+u"漲跌："+data[0]['c']+" 元| "+u"昨日收盤價："+data[0]['pcls_fix']
        # 漲跌幅度 = (成交價-昨日收盤) / 昨日收盤 * 100 %
        cp =  (float(data[0]['l']) - float(data[0]['pcls_fix'])) / float(data[0]['pcls_fix']) * 100
        if cp > 5:
            return  stock_up+stock_msg
        elif cp < -4:
            return  stock_down+stock_msg
        return ''
    else:
        db.users.delete_one({uid['name']:uid['uid'],'stock':stock_code})
        return stock_code+":"+"no found,remove this stock from database!!"

# add stock in database
# 依使用者id及名字各別存入要自動看盤的股票
#
def add_stock(event,uid):
    stocks = event.message.text[4:]

    data = {uid['name']:uid['uid'],'stock':stocks}
    db.users.insert(data)
    push_msg(event,'已加入:'+stocks)


# get self stock from database
# 列出自已的股票
#

def find_stock(event,uid):
    lists=[]
    comma = ' , '

    for code in db.users.find({uid['name']:uid['uid']}):
        stock_code =  code['stock']
        lists.append(stock_code)
            #print lists
    push_msg(event,"目前監看的股票有:"+comma.join(lists))


# delete self stock from database
#
#
def del_stock(event,uid):
    stocks = event.message.text[4:]
    db.users.delete_one({uid['name']:uid['uid'],'stock':stocks})
    push_msg(event,'已刪除'+stocks)

def push_msg(event,msg):
    try:
        user_id = event.source.user_id
        line_bot_api.push_message(user_id,TextSendMessage(text=msg))
    except:
        room_id = event.source.room_id
        line_bot_api.push_message(room_id,TextSendMessage(text=msg))

def reply_msg(event,msg):
    line_bot_api.reply_message(event.reply_token,messages=TextSendMessage(text=msg))

def get_user_profile(event):
    uid = {}
    try:
        profile = line_bot_api.get_profile(event.source.user_id)
        uid = {'name':profile.display_name,'uid':profile.user_id}
    except:
        push_msg(event,'未開放群組使用此功能')
        uid = {'name':'none','uid':'none'}
    return uid

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    endtime = "13:30:00" # 自動結束時間
    emsg =  event.message.text
    try:
        uid = get_user_profile(event)
    except:
        push_msg(event,'未開放群組使用此功能')

    if uid['name'] != "none":
        if re.match("/start",emsg):
            push_msg(event,"股票漲幅背景監視中.....當漲幅大於5%或小於-4%會給予警訊!!")
            stat[uid['uid']] = 'keep'
            while True:
                now = datetime.datetime.now().strftime("%H:%M:%S")
                if endtime < now:
                    push_msg(event,"今日交易已結束，自動看盤已停止~~明日請早")
                    break
                try:
                    for index in db.users.find({uid['name']:uid['uid']}):
                        code = index['stock']
                        data = Get_Stock(code)
                        print data
                        info =  Stockcp(code,data,uid)
                        if info !="":
                            push_msg(event,info)
                        time.sleep(10)
                except:
                    push_msg(event,"被踢了~~~請輸入/start 重新再來一次")
                if stat[uid['uid']] =='exit':
                    push_msg(event,"自動看盤停止~~")
                    break

        if re.match("/end",emsg):
            stat[uid['uid']] ='exit'

        if emsg=='/realtime':
            push_msg(event,'------即時股價回報開始------------')
            for index in db.users.find({uid['name']:uid['uid']}):
                code = index['stock']
                data = Get_Stock(code)
                info =  Stockinfo(code,data,uid)
                if info !="":
                    push_msg(event,info)
                time.sleep(3)
            push_msg(event,'-------即時股價回報結束------------')

        if re.match(u'add:',emsg):
            add_stock(event,uid)
        if re.match(u'del:',emsg):
            del_stock(event,uid)
        if re.match('/stocks|/Stocks',emsg):
            find_stock(event,uid)

    if re.match('/help|--h|/Help|--H',emsg):
        buttons_template = TemplateSendMessage(
            alt_text='Buttons template',
            template=ButtonsTemplate(
                title='自動看盤使用說明',
                text='請選擇',
                actions=[
                    MessageTemplateAction(
                        label='使用方法',
                        text=':usage'
                    ),
                    MessageTemplateAction(
                        label='即時股票資訊',
                        text='/realtime'
                    ),
                    MessageTemplateAction(
                        label='開始自動看盤',
                        text='/start'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
        return 0
    if re.match(':usage',emsg):
        Usage(event)
