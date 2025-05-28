from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import requests
import json
import random
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
import astrbot.api.message_components as Comp

@register("chouqunyou", "灵煞", "抽取QQ群群员的插件", "1.0.0")
class chouqunyou(Star):
    def __init__(self, context: Context):
        super().__init__(context)
    
    @filter.command("抽取")
    async def wife(self, event: AstrMessageEvent,):
        try:
            group_id=event.get_group_id()
        except:
            yield event.plain_result(f"获取出错!")
            event.stop_event()

        if event.get_platform_name() == "aiocqhttp":
            assert isinstance(event, AiocqhttpMessageEvent)
            client = event.bot # 得到 client
            payloads = {
                "group_id": group_id,
                "no_cache": True
            }
            ret = await client.api.call_action('get_group_member_list', **payloads) # 调用 协议端  API
            
        length = len(ret)
        num = random.randint(0, length - 1)
        theone = ret[num]
        user_id = theone.get('user_id')
        nick_name = theone.get('nickname')
        avatar_url = f"https://q4.qlogo.cn/headimg_dl?dst_uin={user_id}&spec=640"
        chain = [
            Comp.At(qq=event.get_sender_id()), # At 消息发送者
            Comp.Plain("这是你抽到的群友"),
            Comp.Image.fromURL(avatar_url), # 从 URL 发送图片
            Comp.Plain(nick_name)
        ]
        yield event.chain_result(chain)


