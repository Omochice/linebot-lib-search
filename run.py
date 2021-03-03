import responder
from scrape import Scraper

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from pathlib import Path
import os
import json

line_bot_api = LineBotApi(os.environ["ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["CHANNEL_SECRET"])

api = responder.API()
searcher = Scraper(os.environ["CHROME_DRIVER_PATH"])


@api.route("/")
def index(req, resp):
    resp.text = req.method


@api.route("/endpoint")
async def endpoint(req, resp):
    with open("log.log", "a") as f:
        print(req.method)
    if req.method != "post":
        resp.status = 400
    signature = req.headers["X-Line-Signature"]

    # print(req.method)
    # print(req.headers)
    body = await req.media()
    body = json.dumps(body, ensure_ascii=False).replace(" ", "")

    try:
        handler.handle(body, signature)
        resp.status_code = 200
    except InvalidSignatureError:
        resp.status_code = 400

    # なんやかんやで調べる本の名前を取り出す

    # fetch book info

    # print(req.header)


def construct_message():
    pass


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    rst = searcher.scrape(event.message.text)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"{rst}"))


if __name__ == "__main__":
    api.run(debug=True)
