自動看盤機器人
==========================

Line Bot +　Flask + Mongodb + Google Stock API
可自訂自已的股票倉庫，即時回報股價或自動看盤當漲幅超過預期再給予提醒


### 環境設定

    export LINE_BOT_CHANNEL_ACCESS_TOKEN= xxxxxxxxxxxxx
    export LINE_BOT_CHANNEL_ACCESS_SECRET= xxxxxxxxxxxx
    export MOGODB_STOCK_URL= xxxxxxxxxxxx

### 使用方法
* 加入股票

    add:stock_code

    ex -> add:0050 (目前只能單張增加)

* 刪除股票

    del:stock_code

    ex -> del:0050 (目前只能單張刪除)

* 查詢已記錄的股票

    /stocks

* 目前所選的股票即時報價

    /realtime

* 啟動自動看盤功能

  /start

  當漲幅超過5%下跌超過4%時會給予提醒, 預設於下午1:30分收盤時自動停止

* 結束自動看盤

  /end

* 使用說明

  --h

  /help

* 使用說明(電腦版的Line無法顯示時改用此指令)
  :usage

PS：群組暫不開放以上功能

執行環境
-----
* python2.7

Reference
---------------
* [line-bot-sdk-python](https://github.com/line/line-bot-sdk-python)
* [使用Yahoo/Google API取得歷史股價資料](http://lovecoding.logdown.com/posts/257928-use-yahoo-api-to-obtain-historical-stock-price-data)
* [MongoDB](https://mlab.com/)
* [pymongo](https://api.mongodb.com/python/current/)

License
----------------
MIT license
