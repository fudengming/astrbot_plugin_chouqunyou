from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import requests
import json
import random
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
import astrbot.api.message_components as Comp

# 文案字典
MESSAGES = {
    "fetch_error": "获取出错!",
    "too_many_error": "抽取次数过大，不执行抽取操作",
    "single_draw_prefix": "这是你抽到的群友",
    "ten_draw_prefix": "这是你的十连抽结果：",
    "multi_draw_prefix": "这是你的{num_str}连抽结果：",
    "user_format": "{nickname}({user_id})",
}

@register("chouqunyou", "灵煞、FDMNya~（QWen3-Coder）", "抽取QQ群群员的插件", "1.0.0")
class ChouQunYou(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def _get_group_members(self, event: AstrMessageEvent):
        """获取群成员列表"""
        try:
            group_id = event.get_group_id()
        except Exception:
            return None

        if event.get_platform_name() == "aiocqhttp":
            assert isinstance(event, AiocqhttpMessageEvent)
            client = event.bot
            payload = {
                "group_id": group_id,
                "no_cache": True
            }
            response = await client.api.call_action('get_group_member_list', **payload)
            return response
        return None

    async def _draw_random_member(self, member_list):
        """从成员列表中随机抽取一个成员"""
        member_count = len(member_list)
        if member_count == 0:
            return None
        random_index = random.randint(0, member_count - 1)
        return member_list[random_index]

    @filter.command("抽取")
    async def draw_single_member(self, event: AstrMessageEvent):
        member_list = await self._get_group_members(event)
        if not member_list:
            yield event.plain_result(MESSAGES["fetch_error"])
            event.stop_event()
            return

        selected_member = await self._draw_random_member(member_list)
        if not selected_member:
            yield event.plain_result(MESSAGES["fetch_error"])
            event.stop_event()
            return

        user_id = selected_member.get('user_id')
        nickname = selected_member.get('nickname')
        result_text = MESSAGES["user_format"].format(nickname=nickname, user_id=user_id)
        avatar_url = f"https://q4.qlogo.cn/headimg_dl?dst_uin={user_id}&spec=640"

        message_chain = [
            Comp.At(qq=event.get_sender_id()),
            Comp.Plain(MESSAGES["single_draw_prefix"]),
            Comp.Image.fromURL(avatar_url),
            Comp.Plain(result_text)
        ]
        yield event.chain_result(message_chain)

    @filter.command("十连", alias={"十连抽"})
    async def draw_ten_members(self, event: AstrMessageEvent):
        member_list = await self._get_group_members(event)
        if not member_list:
            yield event.plain_result(MESSAGES["fetch_error"])
            event.stop_event()
            return

        selected_members = []
        for i in range(10):
            member = await self._draw_random_member(member_list)
            if member:
                nickname = member.get('nickname')
                user_id = member.get('user_id')
                selected_members.append(f"{i + 1}. {MESSAGES['user_format'].format(nickname=nickname, user_id=user_id)}")

        result_text = MESSAGES["ten_draw_prefix"] + "\n" + "\n".join(selected_members)
        message_chain = [
            Comp.At(qq=event.get_sender_id()),
            Comp.Plain(result_text)
        ]
        yield event.chain_result(message_chain)

    @filter.command("多抽", alias={"多连抽"})
    async def draw_multiple_members(self, event: AstrMessageEvent, count: int):
        # 消息过长会发送失败，懒得分段了干脆从源头上解决，限制一下抽取的次数
        if count > 500:
            yield event.plain_result(MESSAGES["too_many_error"])
            event.stop_event()
            return
            
        member_list = await self._get_group_members(event)
        if not member_list:
            yield event.plain_result(MESSAGES["fetch_error"])
            event.stop_event()
            return

        selected_members = []
        for i in range(count):
            member = await self._draw_random_member(member_list)
            if member:
                nickname = member.get('nickname')
                user_id = member.get('user_id')
                selected_members.append(f"{i + 1}. {MESSAGES['user_format'].format(nickname=nickname, user_id=user_id)}")

        result_text = f"{MESSAGES['multi_draw_prefix'].format(num_str=str(count))}" + "\n" + "\n".join(selected_members)
        message_chain = [
            Comp.At(qq=event.get_sender_id()),
            Comp.Plain(result_text)
        ]
        yield event.chain_result(message_chain)
