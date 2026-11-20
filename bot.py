import nonebot
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter

nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(OneBotV11Adapter)

# 載入同目錄下的 qq_plugin.py
nonebot.load_plugin("qq_plugin")

if __name__ == "__main__":
    nonebot.run()