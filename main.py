import os
import sys

import aiohttp

from fastapi import Request, FastAPI, HTTPException, Header


from linebot import (
    WebhookHandler, LineBotApi
)
from linebot.aiohttp_async_http_client import AiohttpAsyncHttpClient
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, URIAction, AccountLinkEvent
)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.environ["LINE_CHANNEL_SECRET"]
channel_access_token = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]

if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

app = FastAPI(title="connect line demo", description="this is test!")

line_bot_api = LineBotApi(channel_access_token=channel_access_token)
handler = WebhookHandler(channel_secret=channel_secret)

@app.post("/callback")
async def callback(request: Request, x_line_signature: str = Header(None)):
    body = await request.body()
    try:
        handler.handle(body.decode("utf-8"), x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(
            status_code=400, detail='invalid signature. Please check your channel access token, channel secret')
    return 'CallBack success'


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    if event.message.text == "連携する":
        link_token_response = line_bot_api.issue_link_token(event.source.user_id)
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(
                alt_text='連携する',
                template=ButtonsTemplate(
                    title='連携',
                    text='連携する場合は下記ボタンをクリックしてください',
                    actions=[
                        URIAction(
                            label='連携する',
                            uri='｛設定したLINE連携用ログインURL｝'+str(link_token_response.link_token)
                        )
                    ]
                )
            )
        )
    elif event.message.text == "連携を解除する":
        #Data APIで解除時にBubbleのnonceを削除する
        line_bot_api.unlink_rich_menu_from_user(event.source.user_id)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ご利用ありがとうございました。\n再び連携したい場合は、メニューボタンより連携してください。")
        )

    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="下記メニューのボタンをクリックしてください")
        )
    return 'MessegeEvent-TextMessage success'

@handler.add(AccountLinkEvent)
def send_thank_message(event):
    profile = line_bot_api.get_profile(event.source.user_id)
    line_bot_api.link_rich_menu_to_user(event.source.user_id, '｛作成したリッチメニューのＩＤ｝')
    line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"{profile.display_name} 様\n連携ありがとうございます\nこのアカウントではイベント情報やクーポンを配信します\n今後ともよろしくお願いします。")
        )

@app.get("/")
def root():
    return {"title": app.title, "description": app.description}