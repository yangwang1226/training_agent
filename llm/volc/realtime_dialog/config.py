import uuid
import pyaudio

# 配置信息
ws_connect_config = {
    "base_url": "wss://openspeech.bytedance.com/api/v3/realtime/dialogue",
    "headers": {
        "X-Api-App-ID": "2922407283",
        "X-Api-Access-Key": "O11aUxRjYsYMDl_JW0ZgSI6Y_MQ0FB8m",
        "X-Api-Resource-Id": "volc.speech.dialog",  # 固定值
        "X-Api-App-Key": "PlgvMymc7f3tQnJ6",  # 固定值
        "X-Api-Connect-Id": str(uuid.uuid4()),
    }
}

start_session_req = {
    "asr": {
        "extra": {
            "end_smooth_window_ms": 1500,
        },
    },
    "tts": {
        "speaker": "saturn_zh_male_aiqilingren_tob",
        # "speaker": "zh_male_yunzhou_jupiter_bigtts",
        # "speaker": "S_XXXXXX",  // 指定自定义的复刻音色,需要填下character_manifest
        # "speaker": "ICL_zh_female_aojiaonvyou_tob" // 指定官方复刻音色，不需要填character_manifest
        "audio_config": {
            "channel": 1,
            "format": "pcm",
            "sample_rate": 24000
        },
    },
    "dialog": {
        "bot_name": "豆包",
        # "system_role": "你使用活泼灵动的女声，性格开朗，热爱生活。",
        # "speaking_style": "你的说话风格简洁明了，语速适中，语调自然。",
        "character_manifest": "你是一个人到中年的北京海淀家长，正在为孩子学习发愁",
        "location": {
          "city": "北京",
        },
        "extra": {
            "strict_audit": False,
            "audit_response": "支持客户自定义安全审核回复话术。",
            "recv_timeout": 10,
            "input_mod": "audio",
            "model": "2.2.0.0"
        }
    }
}

input_audio_config = {
    "chunk": 3200,
    "format": "pcm",
    "channels": 1,
    "sample_rate": 16000,
    "bit_size": pyaudio.paInt16
}

output_audio_config = {
    "chunk": 3200,
    "format": "pcm",
    "channels": 1,
    "sample_rate": 24000,
    "bit_size": pyaudio.paFloat32
}
