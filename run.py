from linebot.webhook import WebhookPayload
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
searcher = Scraper(os.environ["CHROME_DRIVER_PATH"], os.environ["CHROME_PATH"])


@api.route("/")
def index(req, resp):
    resp.text = req.method


@api.route("/endpoint")
async def endpoint(req, resp):
    if req.method != "post":
        resp.status = 400
    signature = req.headers["X-Line-Signature"]

    body = await req.media()
    body = json.dumps(body, ensure_ascii=False).replace(" ", "")

    try:
        handler.handle(body, signature)
        resp.status_code = 200
    except InvalidSignatureError:
        resp.status_code = 400


def construct_message(search_rst: dict) -> str:
    if search_rst["n_books"] == 0:
        message = "ヒットはありませんでした。\n"
    elif search_rst["n_books"] <= 10:
        message = f"{search_rst['n_books']}件がヒットしました。\n"
    else:
        message = f"{search_rst['n_books']}件がヒットしました。(上位10件を表示中)\n"
    message += "----------\n"
    for book in search_rst["books"]:
        if book["loanable"]:
            loanable_text = f"貸出可\n"
            loanable_text += "\n".join(map(lambda x: f"\t{x}", book["location"]))
        else:
            loanable_text = "貸出中"
        message += f"""{book['title']}({book['url']})
{loanable_text}\n
"""
    return message


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    rst = searcher.scrape(event.message.text)
    line_bot_api.reply_message(event.reply_token,
                               TextSendMessage(text=construct_message(rst)))


if __name__ == "__main__":
    api.run(debug=True)
