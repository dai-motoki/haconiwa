#!/usr/bin/env python3
"""
Gemini Live API - フル版（元のコードをベース）
テキスト入力対応版に改造
"""

import os
import asyncio
import base64
import io
import traceback
import sys

import cv2
import pyaudio
import PIL.Image
import mss

import argparse

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

MODEL = "models/gemini-2.5-flash-exp-native-audio-thinking-dialog"

DEFAULT_MODE = "none"  # デフォルトでカメラなし

client = genai.Client(
    http_options={"api_version": "v1beta"},
    api_key=os.environ.get("GEMINI_API_KEY"),
)

# CONFIG設定を修正
CONFIG = types.LiveConnectConfig(
    response_modalities=[
        "AUDIO",
    ],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Zephyr")
        )
    ),
)

pya = pyaudio.PyAudio()


class AudioLoop:
    def __init__(self, video_mode=DEFAULT_MODE, single_message=None):
        self.video_mode = video_mode
        self.single_message = single_message
        
        self.audio_in_queue = None
        self.out_queue = None
        self.session = None
        self.send_text_task = None
        self.receive_audio_task = None
        self.play_audio_task = None
        
        self.audio_stream = None

    async def send_single_message(self):
        """単一メッセージ送信モード"""
        if self.single_message:
            print(f"💬 送信: {self.single_message}")
            await self.session.send(input=self.single_message, end_of_turn=True)
            # 5秒待機後終了
            await asyncio.sleep(5)
        raise asyncio.CancelledError("Single message sent")

    async def send_text(self):
        """対話モード（Claude Codeでは使用不可）"""
        while True:
            text = await asyncio.to_thread(
                input,
                "message > ",
            )
            if text.lower() == "q":
                break
            await self.session.send(input=text or ".", end_of_turn=True)

    def _get_frame(self, cap):
        # Read the frame
        ret, frame = cap.read()
        # Check if the frame was read successfully
        if not ret:
            return None
        # Fix: Convert BGR to RGB color space
        # OpenCV captures in BGR but PIL expects RGB format
        # This prevents the blue tint in the video feed
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = PIL.Image.fromarray(frame_rgb)  # Now using RGB frame
        img.thumbnail([1024, 1024])

        image_io = io.BytesIO()
        img.save(image_io, format="jpeg")
        image_io.seek(0)

        mime_type = "image/jpeg"
        image_bytes = image_io.read()
        return {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode()}

    async def get_frames(self):
        # This takes about a second, and will block the whole program
        # causing the audio pipeline to overflow if you don't to_thread it.
        cap = await asyncio.to_thread(
            cv2.VideoCapture, 0
        )  # 0 represents the default camera

        while True:
            frame = await asyncio.to_thread(self._get_frame, cap)
            if frame is None:
                break

            await asyncio.sleep(1.0)

            await self.out_queue.put(frame)

        # Release the VideoCapture object
        cap.release()

    def _get_screen(self):
        sct = mss.mss()
        monitor = sct.monitors[0]

        i = sct.grab(monitor)

        mime_type = "image/jpeg"
        image_bytes = mss.tools.to_png(i.rgb, i.size)
        img = PIL.Image.open(io.BytesIO(image_bytes))

        image_io = io.BytesIO()
        img.save(image_io, format="jpeg")
        image_io.seek(0)

        image_bytes = image_io.read()
        return {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode()}

    async def get_screen(self):
        while True:
            frame = await asyncio.to_thread(self._get_screen)
            if frame is None:
                break

            await asyncio.sleep(1.0)

            await self.out_queue.put(frame)

    async def send_realtime(self):
        while True:
            msg = await self.out_queue.get()
            await self.session.send(input=msg)

    async def listen_audio(self):
        """マイク音声入力（単一メッセージモードでは無効）"""
        if self.single_message:
            return  # 単一メッセージモードではマイク入力しない
            
        mic_info = pya.get_default_input_device_info()
        self.audio_stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=SEND_SAMPLE_RATE,
            input=True,
            input_device_index=mic_info["index"],
            frames_per_buffer=CHUNK_SIZE,
        )
        if __debug__:
            kwargs = {"exception_on_overflow": False}
        else:
            kwargs = {}
        while True:
            data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, **kwargs)
            await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})

    async def receive_audio(self):
        """Background task to reads from the websocket and write pcm chunks to the output queue"""
        while True:
            turn = self.session.receive()
            async for response in turn:
                if data := response.data:
                    print(f"\n📨 受信データ: タイプ={type(data)}, サイズ={len(data) if hasattr(data, '__len__') else 'N/A'}")
                    self.audio_in_queue.put_nowait(data)
                    print("🎵", end="", flush=True)  # 音声チャンク受信表示
                    continue
                if text := response.text:
                    print(text, end="")

            # If you interrupt the model, it sends a turn_complete.
            # For interruptions to work, we need to stop playback.
            # So empty out the audio queue because it may have loaded
            # much more audio than has played yet.
            while not self.audio_in_queue.empty():
                self.audio_in_queue.get_nowait()

    async def play_audio(self):
        stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
        )
        print("🔊 音声出力開始...")
        chunk_count = 0
        while True:
            bytestream = await self.audio_in_queue.get()
            chunk_count += 1
            print(f"\n🎧 音声再生中 チャンク#{chunk_count} サイズ:{len(bytestream)}bytes")
            await asyncio.to_thread(stream.write, bytestream)
            print(f"✅ チャンク#{chunk_count} 再生完了")

    async def run(self):
        try:
            async with (
                client.aio.live.connect(model=MODEL, config=CONFIG) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session

                self.audio_in_queue = asyncio.Queue()
                self.out_queue = asyncio.Queue(maxsize=5)

                # 単一メッセージモードか対話モードかを選択
                if self.single_message:
                    send_text_task = tg.create_task(self.send_single_message())
                else:
                    send_text_task = tg.create_task(self.send_text())
                
                tg.create_task(self.send_realtime())
                tg.create_task(self.listen_audio())
                
                if self.video_mode == "camera":
                    tg.create_task(self.get_frames())
                elif self.video_mode == "screen":
                    tg.create_task(self.get_screen())

                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())

                await send_text_task
                raise asyncio.CancelledError("User requested exit")

        except asyncio.CancelledError:
            print("\n✅ セッション終了")
        except ExceptionGroup as EG:
            if self.audio_stream:
                self.audio_stream.close()
            traceback.print_exception(EG)
        except Exception as e:
            print(f"\n❌ エラー: {e}")
        finally:
            if self.audio_stream:
                self.audio_stream.close()


if __name__ == "__main__":
    # シンプルな引数処理
    if len(sys.argv) < 2:
        print("使用方法: python gemini_live_full.py <メッセージ>")
        print("例: python gemini_live_full.py 'テストメッセージです'")
        sys.exit(1)
    
    # 全ての引数をメッセージとして結合
    single_message = " ".join(sys.argv[1:])
    
    print("🚀 Gemini Live API - フル版")
    print(f"📝 単一メッセージモード: {single_message}")
    
    main = AudioLoop(video_mode=DEFAULT_MODE, single_message=single_message)
    asyncio.run(main.run())