import asyncio
import websockets
import json
import threading
from zhipuai import ZhipuAI
from flask import Flask, request, render_template_string

group_messages = {}
specific_group_ids = []# 这里填入你的群号


async def handle_message(data, group_id):
    if group_id not in group_messages:
        group_messages[group_id] = []
    group_messages[group_id].append(data["message"])

    if len(group_messages[group_id]) > 500:
        group_messages[group_id].pop(0)


async def handler(websocket):
    async for message in websocket:
        data = json.loads(message)
        try:
            if data['post_type'] == 'message' and data['message_type'] == 'group' and data['group_id'] in specific_group_ids:
                await handle_message(data, data["group_id"])
        except:
            pass


app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-cn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Q群总结</title>
</head>
<body>
    <h4>总结</h4>
    <h5>密码</h5>
    <form action="/submit_sum" method="post">
        <input type="text" name="input1">
    <h5>大群填1，小群填2</h5>
        <input type="text" name="input2">
    <h5>总结条数（<500）</h5>
        <input type="text" name="input3">
        <button type="submit">提交</button>
    </form>
    <h4>询问</h4>
    <h5>密码</h5>
    <form action="/submit_ask" method="post">
        <input type="text" name="input1">
    <h5>大群填1，小群填2</h5>
        <input type="text" name="input2">
    <h5>装载条数（<500）</h5>
        <input type="text" name="input3">
    <h5>询问内容</h5>
        <input type="text" name="input4">
        <button type="submit">提交</button>
    </form>
</body>
</html>
'''


@app.route('/home')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/submit_sum', methods=['POST'])
def submit_sum():
    input_data1 = request.form.get('input1')
    if input_data1 == "12345":
        input_data2 = request.form.get('input2')
        input_data3 = int(request.form.get('input3'))
        if input_data2 == "2":
            group_id_choose = # 这里填入你的群号
        elif input_data2 == "1":
            group_id_choose = # 这里填入你的群号
        group_messages_choose = str(group_messages[group_id_choose][-input_data3:])
        client = ZhipuAI(api_key="")# 这里填入智谱AI APIKEY
        response = client.chat.completions.create(
            model="glm-3-turbo",
            messages=[{"role": "system", "content": "这是一个群聊的聊天记录，你需要进行简洁、全面的总结"},
                      {"role": "user", "content": group_messages_choose}],
            stream=False
        ).json()
        response_dict = json.loads(response)
        sum_result = response_dict["choices"][0]["message"]["content"]
        render_template_string = f'''
        <!DOCTYPE html>
        <html lang="zh-cn">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>结果</title>
        </head>
        <body>
            <h5>{sum_result}</h5>
        </body>
        </html>
        '''
        return render_template_string


@app.route('/submit_ask', methods=['POST'])
def submit_ask():
    input_data1 = request.form.get('input1')
    if input_data1 == "12345":
        input_data2 = request.form.get('input2')
        input_data3 = int(request.form.get('input3'))
        if input_data2 == "2":
            group_id_choose = # 这里填入你的群号
        elif input_data2 == "1":
            group_id_choose = # 这里填入你的群号
        group_messages_choose = str(group_messages[group_id_choose][-input_data3:])
        user_ask = request.form.get('input4')
        client = ZhipuAI(api_key="")# 这里填入智谱AI APIKEY
        response = client.chat.completions.create(
            model="glm-3-turbo",
            messages=[{"role": "system", "content": "这是一个群聊的聊天记录，用户提问在最后，你需要精准回答提问"},
                      {"role": "user", "content": group_messages_choose + "；" + user_ask}],
            stream=False
        ).json()
        response_dict = json.loads(response)
        sum_result = response_dict["choices"][0]["message"]["content"]
        render_template_string = f'''
        <!DOCTYPE html>
        <html lang="zh-cn">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>结果</title>
        </head>
        <body>
            <h5>{sum_result}</h5>
        </body>
        </html>
        '''
        return render_template_string


start_server = websockets.serve(handler, "0.0.0.0", 8080)
if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(start_server)
    threading.Thread(target=app.run, kwargs={"host": "0.0.0.0", "port": 80}).start()
    asyncio.get_event_loop().run_forever()
