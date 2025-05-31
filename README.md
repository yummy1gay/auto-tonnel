## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Initialize the Client

```python
from telethon import TelegramClient
from auto_tonnel import AutoTonnel

client = TelegramClient('AutoTonnel', api_id, api_hash)
client.start()

tonnel = AutoTonnel(client)
```

### Fetch Available Gifts

```python
gifts = await tonnel.get_gifts(limit=30, 
                               gift_name="Top Hat", 
                               backdrops=["ALL!"], 
                               models=["Pixel Perfect"], 
                               symbols=["ALL!"], 
                               asset="TON")
print(gifts)
```

### Buy a Gift

```python
buy = await tonnel.buy_gift(gift_id=1488, price=100, asset="TON")  # Gift ID and price are retrieved from get_gifts()
premarket = await tonnel.buy_gift(gift_id=1337, price=69, asset="TON", pemarket=True) # If the gift is from premarket
print(buy, premarket)
```
*Note: API prices do not include fees. The final cost is approximately 10% higher.*

### Get User Info

```python
info = await tonnel.get_info()
print(info)
```
