from urllib.parse import unquote, urljoin

from telethon import TelegramClient
from telethon.tl.functions.messages import RequestAppWebViewRequest
from telethon.tl.types import InputBotAppShortName

from Crypto import Random
from Crypto.Cipher import AES
from hashlib import md5
import cloudscraper
import base64

import time
import re

import json
from bs4 import BeautifulSoup

class AutoTonnel:
    def __init__(self, client: TelegramClient):
        self.client = client
        self.init_data = None
        self.scraper = cloudscraper.create_scraper()
        self.headers = {
            "accept": "*/*",
            "accept-encoding": "gzip",
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,pl;q=0.6",
            "content-type": "application/json",
            "origin": "https://marketplace.tonnel.network",
            "referer": "https://marketplace.tonnel.network",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0"
        }
        self.url = "https://gifts2.tonnel.network"

    def update_gifts(self):
        url = "https://marketplace.tonnel.network/"
        res = self.scraper.get(url)
        print(res.status_code)
        if res.status_code != 200:
            return False
        
        soup = BeautifulSoup(res.text, 'html.parser')
        script_tag = next((tag['src'] for tag in soup.find_all('script', src=True) if re.match(r'/assets/index-\w+\.js', tag['src'])), None)
        if not script_tag:
            return False
        
        js_res = self.scraper.get(urljoin(url, script_tag))
        if js_res.status_code != 200:
            return False
        
        match = re.search(r'MODELS=JSON\.parse\(`(.*?)`\)', js_res.text, re.DOTALL)
        if not match:
            return False
        
        data = json.loads(match.group(1))
        formatted_data = {
            item['_id']: {
                "models": {m.rsplit(" (", 1)[0]: f"({m.rsplit(' (', 1)[1]}" if " (" in m else "" for m in item.get('models', []) if m != "All Models"},
                "backgrounds": {b.rsplit(" (", 1)[0]: f"({b.rsplit(' (', 1)[1]}" if " (" in b else "" for b in item.get('backgrounds', []) if b != "All Backgrounds"},
                "symbols": {s.rsplit(" (", 1)[0]: f"({s.rsplit(' (', 1)[1]}" if " (" in s else "" for s in item.get('symbols', []) if s != "All Symbols"}
            }
            for item in data if item['_id'] != "All Names"
        }
        
        with open('gifts.json', 'w', encoding='utf-8') as f:
            json.dump(formatted_data, f, ensure_ascii=False, indent=3)
        
        return True

    def gen_wtf(self, timestamp):
        password = "yowtfisthispieceofshitiiit".encode()
        salt = Random.new().read(8)
        
        password += salt
        key_hash = md5(password).digest()
        key_iv = key_hash
        while len(key_iv) < 48:
            key_hash = md5(key_hash + password).digest()
            key_iv += key_hash
        
        key, iv = key_iv[:32], key_iv[32:]
        
        block_padding = 16 - (len(str(timestamp).encode()) % 16)
        padded_message = str(timestamp).encode() + (chr(block_padding) * block_padding).encode()
        
        aes = AES.new(key, AES.MODE_CBC, iv)
        encrypted_data = base64.b64encode(b"Salted__" + salt + aes.encrypt(padded_message))
        return encrypted_data.decode()

    async def data(self) -> str:
        web = await self.client(RequestAppWebViewRequest(peer='me',
                                app=InputBotAppShortName(bot_id=await self.client.get_input_entity('Tonnel_Network_bot'),
                                                         short_name="gift"), platform='android'))
        url = web.url
        self.init_data = unquote(url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])

    async def get_gifts(self, limit=30, gift_name=["Spiced Wine", "Lunar Snake"], backdrops=["ALL!"], models=["ALL!"], symbols=["ALL!"], asset="TON"):
        if not self.init_data:
            await self.data()
        try:
            with open('gifts.json', 'r', encoding='utf-8') as f:
                gifts = json.load(f)
        except FileNotFoundError:
            self.update_gifts()
            with open('gifts.json', 'r', encoding='utf-8') as f:
                gifts = json.load(f)
        if gift_name:
            filters = {"backgrounds": backdrops, "models": models, "symbols": symbols}
            for key, value in filters.items():
                if value != ["ALL!"]:
                    filters[key] = [f"{item} {gifts[gift_name[0]][key][item]}" for item in value if item in gifts[gift_name[0]][key]]
                else:
                    filters[key] = []
            backdrops, models, symbols = filters["backgrounds"], filters["models"], filters["symbols"]
        if isinstance(gift_name, list):
            filter_payload = {"price": {"$exists": True}, "refunded": {"$ne": True},
                              "buyer": {"$exists": False}, "export_at": {"$exists": True},
                              "gift_name": {"$in": gift_name}, "asset": asset}
        else:
            filter_payload = {"price": {"$exists": True}, "refunded": {"$ne": True},
                              "buyer": {"$exists": False}, "export_at": {"$exists": True},
                              "gift_name": gift_name, "asset": asset}
        filter_payload.update({field[:-1]: {"$in": values} for field, values in filters.items() if values})
        payload = {"page": 1, "limit": limit,
                   "sort": json.dumps({"price": 1, "gift_id": -1}),
                   "filter": json.dumps(filter_payload),
                   "ref": 0, "price_range": None, "user_auth": self.init_data}
        resp = self.scraper.post(f"{self.url}/api/pageGifts", json=payload, headers=self.headers)
        return resp.json()
    
    async def get_info(self):
        if not self.init_data:
            await self.data()

        resp = self.scraper.post(f"{self.url}/api/balance/info", json={"authData": self.init_data, "ref": ""}, headers=self.headers)

        return resp.json()
    
    async def buy_gift(self, gift_id, price, asset):
        if not self.init_data:
            await self.data()

        timestamp = int(time.time())

        payload = {"authData": self.init_data, "asset": asset,
                   "price": price, "timestamp": timestamp,
                   "wtf": self.gen_wtf(timestamp)}

        if premarket:
            type = "buyGiftPreMarket"
        else:
            type = "buyGift"

        resp = self.scraper.post(f"https://gifts.coffin.meme/api/{type}/{gift_id}", json=payload, headers=self.headers)

        return resp.json()
