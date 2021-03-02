import responder

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from pathlib import Path
import os
import yaml

# with open(Path(__file__).parent / "config.yaml") as f:
#     config = yaml.safe_load(f)
#
# line_bot_api = LineBotApi(config["access_token"])
# handler = WebhookHandler(config["channel_secret"])
line_bot_api = LineBotApi(os.environ["ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["CHANNEL_SECRET"])

api = responder.API()


@api.route("/")
def index(req, resp):
    resp.text = req.method


@api.route("/endpoint")
async def endpoint(req, resp):
    if req.method != "post":
        resp.status = 400
    signature = req.headers["X-Line-Signature"]

    print(req.method)
    print(req.headers)
    body = await req.media()

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        resp.status = 400

    # なんやかんやで調べる本の名前を取り出す

    # fetch book info

    # print(req.header)


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(event.reply_token,
                               TextSendMessage(text=event.message.text))


if __name__ == "__main__":
    api.run(debug=True)
