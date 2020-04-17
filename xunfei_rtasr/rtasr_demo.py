# -*- encoding:utf-8 -*-

import base64
import hashlib
import hmac
import json
import logging
import sys
import threading
import time
from hashlib import sha1
from socket import *
from urllib.parse import quote

import websocket
from websocket import create_connection

from xunfei_rtasr.key_config import app_id, api_key
import importlib

importlib.reload(sys)
# sys.setdefaultencoding("utf8")
logging.basicConfig()

base_url = "wss://rtasr.xfyun.cn/v1/ws"

file_path = "test_1.pcm"

end_tag = "{\"end\": true}"


class Client():
    def __init__(self):
        # 生成鉴权参数
        ts = str(int(time.time()))
        tmp = app_id + ts
        hl = hashlib.md5()
        hl.update(tmp.encode(encoding='utf-8'))
        my_sign = hmac.new(api_key.encode(), hl.hexdigest().encode(), sha1).digest()
        signa = base64.b64encode(my_sign)

        url = base_url + "?appid=" + app_id + "&ts=" + ts + "&signa=" + quote(signa) + "&pd=edu"
        print(('url: {}'.format(url)))
        self.ws = create_connection(url)
        self.trecv = threading.Thread(target=self.recv)
        self.trecv.start()

    def send(self, file_path):
        file_object = open(file_path, 'rb')
        try:
            index = 1
            while True:
                chunk = file_object.read(1280)
                if not chunk:
                    break
                self.ws.send(chunk)

                index += 1
                time.sleep(0.04)
        finally:
            # print str(index) + ", read len:" + str(len(chunk)) + ", file tell:" + str(file_object.tell())
            file_object.close()

        self.ws.send(bytes(end_tag, encoding='utf-8'))
        print("send end tag success")

    def recv(self):
        try:
            while self.ws.connected:
                result = str(self.ws.recv())
                if len(result) == 0:
                    print("receive result end")
                    break
                result_dict = json.loads(result, encoding='utf-8')

                # 解析结果
                if result_dict["action"] == "started":
                    print("handshake success, result: " + result)

                if result_dict["action"] == "result":
                    # print "rtasr result: " + result
                    data = json.loads(result_dict['data'])['cn']['st']
                    data_type = data['type']
                    # only print each complete sentence.
                    if data_type == '0':
                        data_rt = data['rt']
                        st = []
                        for x in data_rt[0]['ws']:
                            st.append(x['cw'][0]['w'])
                        print(''.join(st))

                if result_dict["action"] == "error":
                    print("rtasr error: " + result)
                    self.ws.close()
                    return
        except websocket.WebSocketConnectionClosedException:
            print("receive result end")

    def close(self):
        self.ws.close()
        print("connection closed")


if __name__ == '__main__':
    client = Client()
    client.send(file_path)
