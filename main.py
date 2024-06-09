import asyncio
import threading
import websockets
from ocr import ocr
from urllib.parse import unquote
import requests
from bigmodel import *
import pickle
import keyboard
import os

default_prompt = "你在一个群聊中与他人对话，请你尽可能隐藏自己是个机器人的事实，回答尽可能符合人类，简短。你有自己的兴趣爱好等，特殊消息已处理"

if os.path.exists('save.pkl'):
    pass
else:
    chat_prompt = {}
    private_chat_prompt = {}
    group_messages = {}
    private_messages = {}
    chat_history = {}
    private_chat_history = {}
    in_chat_groups = []
    in_chat_users = []
    with open('save.pkl', 'wb') as f:
        pickle.dump(chat_prompt, f)
        pickle.dump(private_chat_prompt, f)
        pickle.dump(group_messages, f)
        pickle.dump(private_messages, f)
        pickle.dump(chat_history, f)
        pickle.dump(private_chat_history, f)
        pickle.dump(in_chat_groups, f)

with open('save.pkl', 'rb') as f:
    chat_prompt = pickle.load(f)
    private_chat_prompt = pickle.load(f)
    group_messages = pickle.load(f)
    private_messages = pickle.load(f)
    chat_history = pickle.load(f)
    private_chat_history = pickle.load(f)
    in_chat_groups = pickle.load(f)


async def handle_message(messages, group_id, websocket):
    global chat_history, chat_prompt, first_time
    append_data = ""
    message_send = ""
    if group_id not in group_messages:
        group_messages[group_id] = []
    for message in messages:
        if message["type"] == "text":
            message_text = message["data"]["text"]
            if append_data == "":
                append_data = message_text
            else:
                append_data = append_data + " " + message_text
        elif message["type"] == "image":
            url = unquote(message["data"]["url"]).replace(
                "https://", "http://")
            response = requests.get(url)
            with open('image.png', 'wb') as file:
                file.write(response.content)
            text = ocr()
            if text != None:
                img_text = "图片文字:" + text
            else:
                img_text = "图片无文字"
            if append_data == "":
                append_data = img_text
            else:
                append_data = append_data + " " + img_text
        elif message["type"] == "json":
            text = json.loads(message["data"]["data"])
            if append_data == "":
                append_data = "分享卡片:" + text["prompt"]
            else:
                append_data = append_data + " " + "分享卡片:" + text["prompt"]
        elif message["type"] == "file":
            if append_data == "":
                append_data = append_data + "文件名:" + message["data"]["file"]
            else:
                append_data = append_data + " " + \
                    "文件名:" + message["data"]["name"]
        elif message["type"] == "video":
            if append_data == "":
                append_data = "无法处理的视频"
            else:
                append_data = append_data + " " + "无法处理的视频"
        elif message["type"] == "record":
            if append_data == "":
                append_data = append_data + "无法处理的语音"
            else:
                append_data = append_data + " " + "无法处理的语音"
        elif message["type"] == "at":
            if append_data == "":
                append_data = "@"
            else:
                append_data = append_data + " " + " @"
        elif message["type"] == "reply":
            if append_data == "":
                append_data = "回复:"
            else:
                append_data = append_data + " " + "回复:"
        else:
            print("发生错误")
            print(message)
    # bot内容
    if append_data[:1] == ".":
        text5 = append_data[:5]
        if text5 == ".say ":
            text = append_data.replace(".say ", "")
            voice_gen(text)
            message_send = "无法处理的语音"
            await send_group_message(websocket, group_id, r"[CQ:record,file=file:///C:\Users\Administrator\Desktop\qqbot\2\output.wav]")
        elif text5 == ".sum ":
            text_split = append_data.split()
            sum_length = int(text_split[1])
            group_messages_choose = f"{group_messages[group_id][-sum_length:]}"[
                1:][:-1]
            message_send = ask_glm("这是一个群聊的聊天记录，你需要进行简洁、全面的总结，特殊消息已处理",
                                   group_messages_choose)
            await send_group_message(websocket, group_id, message_send)
        elif text5 == ".ask ":
            text_split = append_data.split()
            if len(text_split) < 3:
                user_ask = append_data.replace(".ask ", "")
                message_send = ask_glm("简短回答", user_ask)
                await send_group_message(websocket, group_id, message_send)
            else:
                sum_length = int(text_split[1])
                group_messages_choose = f"{group_messages[group_id][-sum_length:]}"[
                    1:][:-1]
                user_ask = text_split[2]
                message_send = ask_glm(
                    "这是一个群聊的聊天记录，用户提问在最后使用'/'隔开，你需要精准回答，特殊消息已处理",
                    group_messages_choose + "/" + user_ask)
                await send_group_message(websocket, group_id, message_send)
        elif text5 == ".hlp":
            message_send = '''.say [内容] 生成语音
.sum [数量] 总结消息
.ask <数量> [问题] 提问AI关于群聊内容/直接提问
.cht 聊天模式，开启后，可以进行聊天
.drw [内容] 画图，一张0.1元
.pmt <内容> 更改聊天模式提示词，留空来恢复默认
.hlp 帮助信息
请适当使用有关AI的功能，API要钱的
在使用AI功能时，除了分隔命令，不 要 使 用 空 格'''
            await send_group_message(websocket, group_id, message_send)
        elif text5 == ".cht":
            if group_id in in_chat_groups:
                message_send = "聊天模式已关闭"
                in_chat_groups.remove(group_id)
                await send_group_message(websocket, group_id, message_send)
            else:
                if group_id not in chat_prompt:
                    chat_prompt[group_id] = default_prompt
                message_send = "聊天模式已开启"
                in_chat_groups.append(group_id)
                chat_history[group_id] = [{"role": "system",
                                           "content": chat_prompt}, ]
                first_time = True
                await send_group_message(websocket, group_id, message_send)
        elif text5 == ".drw ":
            prompt = append_data.replace(".drw ", "")
            rsp = draw_cogview(prompt)
            if rsp["status"]:
                img_url = rsp["result"]
                message_send = "图片无文字"
                await send_group_message(websocket, group_id, f"[CQ:image,file={img_url}]")
            else:
                message_send = rsp["result"]
                await send_group_message(websocket, group_id, message_send)
        elif text5 == ".egg":
            message_send = "你找到了彩蛋！"
            await send_group_message(websocket, group_id, message_send)
        elif text5 == ".pmt ":
            user_input = append_data.replace(".pmt ", "")
            if user_input == "":
                chat_prompt[group_id] = default_prompt
                message_send = "设置成功，默认提示为：" + default_prompt
            else:
                chat_prompt[group_id] = user_input
                message_send = "设置成功"
            await send_group_message(websocket, group_id, message_send)

    group_messages[group_id].append(append_data)
    if message_send != "":
        group_messages[group_id].append(message_send)
    if group_id in in_chat_groups:
        if first_time:
            first_time = False
        else:
            chat_history[group_id].append(
                {"role": "user", "content": append_data})
            message_send = glm(chat_history[group_id])
            chat_history[group_id].append(
                {"role": "assistant", "content": message_send})
            await send_group_message(websocket, group_id, message_send)
            if len(chat_history[group_id]) > 100:
                chat_history[group_id].pop(1)
                chat_history[group_id].pop(1)

    if len(group_messages[group_id]) > 1000:
        group_messages[group_id].pop(0)


async def handle_private_message(messages, user_id, websocket):
    global private_chat_history, private_chat_prompt, first_time
    append_data = ""
    message_send = ""
    if user_id not in private_messages:
        private_messages[user_id] = []
    for message in messages:
        if message["type"] == "text":
            message_text = message["data"]["text"]
            if append_data == "":
                append_data = message_text
            else:
                append_data = append_data + " " + message_text
        elif message["type"] == "image":
            url = unquote(message["data"]["url"]).replace(
                "https://", "http://")
            response = requests.get(url)
            with open('image.png', 'wb') as file:
                file.write(response.content)
            text = ocr()
            if text != None:
                img_text = "图片文字:" + text
            else:
                img_text = "图片无文字"
            if append_data == "":
                append_data = img_text
            else:
                append_data = append_data + " " + img_text
        elif message["type"] == "json":
            text = json.loads(message["data"]["data"])
            if append_data == "":
                append_data = "分享卡片:" + text["prompt"]
            else:
                append_data = append_data + " " + "分享卡片:" + text["prompt"]
        elif message["type"] == "file":
            if append_data == "":
                append_data = append_data + "文件名:" + message["data"]["file"]
            else:
                append_data = append_data + " " + \
                    "文件名:" + message["data"]["name"]
        elif message["type"] == "video":
            if append_data == "":
                append_data = "无法处理的视频"
            else:
                append_data = append_data + " " + "无法处理的视频"
        elif message["type"] == "record":
            if append_data == "":
                append_data = append_data + "无法处理的语音"
            else:
                append_data = append_data + " " + "无法处理的语音"
        elif message["type"] == "at":
            if append_data == "":
                append_data = "@"
            else:
                append_data = append_data + " " + " @"
        elif message["type"] == "reply":
            if append_data == "":
                append_data = "回复:"
            else:
                append_data = append_data + " " + "回复:"
        else:
            print("发生错误")
            print(message)
    # bot内容
    if append_data[:1] == ".":
        text5 = append_data[:5]
        if text5 == ".say ":
            text = append_data.replace(".say ", "")
            voice_gen(text)
            message_send = "无法处理的语音"
            await send_private_message(websocket, user_id, r"[CQ:record,file=file:///C:\Users\Administrator\Desktop\qqbot\2\output.wav]")
        elif text5 == ".sum ":
            text_split = append_data.split()
            sum_length = int(text_split[1])
            private_messages_choose = f"{private_messages[user_id][-sum_length:]}"[
                1:][:-1]
            message_send = ask_glm("这是一个群聊的聊天记录，你需要进行简洁、全面的总结，特殊消息已处理",
                                   private_messages_choose)
            await send_private_message(websocket, user_id, message_send)
        elif text5 == ".ask ":
            text_split = append_data.split()
            if len(text_split) < 3:
                user_ask = append_data.replace(".ask ", "")
                message_send = ask_glm("简短回答", user_ask)
                await send_private_message(websocket, user_id, message_send)
            else:
                sum_length = int(text_split[1])
                private_messages_choose = f"{private_messages[user_id][-sum_length:]}"[
                    1:][:-1]
                user_ask = text_split[2]
                message_send = ask_glm(
                    "这是一个群聊的聊天记录，用户提问在最后使用'/'隔开，你需要精准回答，特殊消息已处理",
                    private_messages_choose + "/" + user_ask)
                await send_private_message(websocket, user_id, message_send)
        elif text5 == ".hlp":
            message_send = '''.say [内容] 生成语音
.sum [数量] 总结消息
.ask <数量> [问题] 提问AI关于群聊内容/直接提问
.cht 聊天模式，开启后，可以进行聊天
.drw [内容] 画图，一张0.1元
.pmt <内容> 更改聊天模式提示词，留空来恢复默认
.hlp 帮助信息
请适当使用有关AI的功能，API要钱的
在使用AI功能时，除了分隔命令，不 要 使 用 空 格'''
            await send_private_message(websocket, user_id, message_send)
        elif text5 == ".cht":
            if user_id in in_chat_groups:
                message_send = "聊天模式已关闭"
                in_chat_groups.remove(user_id)
                await send_private_message(websocket, user_id, message_send)
            else:
                if user_id not in private_chat_prompt:
                    private_chat_prompt[user_id] = default_prompt
                message_send = "聊天模式已开启"
                in_chat_groups.append(user_id)
                private_chat_history[user_id] = [{"role": "system",
                                                  "content": private_chat_prompt},]
                first_time = True
                await send_private_message(websocket, user_id, message_send)
        elif text5 == ".drw ":
            prompt = append_data.replace(".drw ", "")
            rsp = draw_cogview(prompt)
            if rsp["status"]:
                img_url = rsp["result"]
                message_send = "图片无文字"
                await send_private_message(websocket, user_id, f"[CQ:image,file={img_url}]")
            else:
                message_send = rsp["result"]
                await send_private_message(websocket, user_id, message_send)
        elif text5 == ".egg":
            message_send = "你找到了彩蛋！"
            await send_private_message(websocket, user_id, message_send)
        elif text5 == ".pmt ":
            user_input = append_data.replace(".pmt ", "")
            if user_input == "":
                private_chat_prompt[user_id] = default_prompt
                message_send = "设置成功，默认提示为：" + default_prompt
            else:
                private_chat_prompt[user_id] = user_input
                message_send = "设置成功"
            await send_private_message(websocket, user_id, message_send)

    private_messages[user_id].append(append_data)
    if message_send != "":
        private_messages[user_id].append(message_send)
    if user_id in in_chat_groups:
        if first_time:
            first_time = False
        else:
            private_chat_history[user_id].append(
                {"role": "user", "content": append_data})
            message_send = glm(private_chat_history[user_id])
            private_chat_history[user_id].append(
                {"role": "assistant", "content": message_send})
            await send_private_message(websocket, user_id, message_send)
            if len(private_chat_history[user_id]) > 100:
                private_chat_history[user_id].pop(1)
                private_chat_history[user_id].pop(1)

    if len(private_messages[user_id]) > 1000:
        private_messages[user_id].pop(0)


async def send_private_message(websocket, user_id, message):
    # 别删!!!
    if f"{message}" == "" or message.split() == "":
        pass
    else:
        response_json = json.dumps({
            "action": "send_private_msg",
            "params": {
                "user_id": user_id,
                "message": f"{message}"
            },
        })
        await websocket.send(response_json)


async def send_group_message(websocket, group_id, message):
    # 别删!!!
    if f"{message}" == "" or message.split() == "":
        pass
    else:
        response_json = json.dumps({
            "action": "send_group_msg",
            "params": {
                "group_id": group_id,
                "message": f"{message}"
            },
        })
        await websocket.send(response_json)


async def handler(websocket):
    async for message in websocket:
        data = json.loads(message)
        if "message_type" in data:
            if data["message_type"] == "group":
                await handle_message(data["message"], data["group_id"], websocket)
            elif data["message_type"] == "private":
                await handle_private_message(data["message"], data["user_id"], websocket)


def stop_program():
    with open('save.pkl', 'wb') as f:
        pickle.dump(chat_prompt, f)
        pickle.dump(private_chat_prompt, f)
        pickle.dump(group_messages, f)
        pickle.dump(private_messages, f)
        pickle.dump(chat_history, f)
        pickle.dump(private_chat_history, f)
        pickle.dump(in_chat_groups, f)
    if event_loop is not None and event_loop.is_running():
        # 停止事件循环
        event_loop.call_soon_threadsafe(event_loop.stop)
        # 等待事件循环真正停止
        event_loop_thread = threading.Thread(target=event_loop.stop)
        event_loop_thread.start()
        event_loop_thread.join()


def hotkey_listener():
    keyboard.add_hotkey('F1', stop_program)


def start_server():
    global event_loop
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    threading.Thread(target=hotkey_listener).start()
    start_server = websockets.serve(handler, "0.0.0.0", 8080)
    event_loop.run_until_complete(start_server)
    event_loop.run_forever()


start_server()
