import json
from zhipuai import ZhipuAI
import dashscope
from dashscope.audio.tts import SpeechSynthesizer
api_key = ""# 替换为你的API密钥
dashscope.api_key = ''# 替换为你的API密钥


def ask_glm(prompt, content):
    client = ZhipuAI(api_key=api_key)
    response = client.chat.completions.create(
        model="glm-4-air",
        messages=[{"role": "system", "content": prompt},
                  {"role": "user", "content": content}],
        stream=False
    ).json()
    response_dict = json.loads(response)
    return response_dict["choices"][0]["message"]["content"]


def draw_cogview(prompt):
    try:
        client = ZhipuAI(api_key=api_key)
        response = client.images.generations(
            model="cogview-3",
            prompt=prompt)
        return {"status": 1, "result": response.data[0].url}
    except:
        return {"status": 0, "result": "Failed"}


def glm(messages):
    client = ZhipuAI(api_key=api_key)
    response = client.chat.completions.create(
        model="glm-4-air",
        messages=messages,
        stream=False
    ).json()
    response_dict = json.loads(response)
    return response_dict["choices"][0]["message"]["content"]


def voice_gen(text):
    result = SpeechSynthesizer.call(model='sambert-zhimiao-emo-v1',
                                    text=text,
                                    sample_rate=48000,
                                    format='wav')
    if result.get_audio_data() is not None:
        with open('output.wav', 'wb') as f:
            f.write(result.get_audio_data())
