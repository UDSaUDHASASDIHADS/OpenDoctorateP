import json
import hashlib
import asyncio
import threading
import traceback
import sys
import os

from msgspec.json import Encoder, Decoder, format
from typing import Optional
from typing import Dict, Any
from datetime import datetime
from hashlib import sha3_512
from random import shuffle
from flask import after_this_request
from datetime import datetime, UTC
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

from constants import USER_JSON_PATH, SERVER_DATA_PATH, SYNC_DATA_TEMPLATE_PATH, CONFIG_PATH

json_encoder = Encoder(order="deterministic")
json_decoder = Decoder(strict=False)


def read_json(path: str) -> Dict[str, Any]:
    with open(path, "rb") as f:
        return json_decoder.decode(f.read())


def write_json(data: Any, path: str, indent: int = 4):
    with open(path, "wb") as f:
        if indent:
            f.write(format(json_encoder.encode(data), indent=indent))
        else:
            f.write(json_encoder.encode(data))


def decrypt_battle_data(data: str, login_time: int = read_json(USER_JSON_PATH)["user"]["pushFlags"]["status"]):
    LOG_TOKEN_KEY = "pM6Umv*^hVQuB6t&"

    battle_data = bytes.fromhex(data[:len(data) - 32])
    src = LOG_TOKEN_KEY + str(login_time)
    key = hashlib.md5(src.encode()).digest()
    iv = bytes.fromhex(data[len(data) - 32:])
    aes_obj = AES.new(key, AES.MODE_CBC, iv)
    try:
        decrypt_data = unpad(aes_obj.decrypt(battle_data), AES.block_size)
        return json.loads(decrypt_data)
    except Exception:
        return {}


def logging(data):
    def rand_name(len: int = 16) -> str:
        dt = datetime.now()
        time = (dt.year, dt.month, dt.day)
        seed = ""
        for t in time:
            seed += str(t)
        seed = str(shuffle(list(seed)))
        return sha3_512(seed.encode()).hexdigest()[:len]

    name = rand_name(8)
    log_message = f"[{datetime.now(UTC).isoformat()}] {data}"
    print(log_message)
    with open(f"logs/{name}.log", "w") as f:
        f.write(log_message)


def run_after_response(func, *args, on_error=None):
    """
    在函数返回后异步执行函数（带线程池、异常捕获）。

    :param func: 要执行的函数。支持带一个参数(data)，亦可以无参数。
    :param *args: 可选，传给函数的参数/数据。
    :param on_error: 可选，异常回调函数。例子: on_error(exception, traceback_str)
    """

    @after_this_request
    def register(response):
        async def task():
            try:
                await asyncio.to_thread(func, *args)
            except Exception as e:
                tb_str = traceback.format_exc()
                if on_error:
                    on_error(e, tb_str)
                else:
                    print(f"[处理异常] {e}", file=sys.stderr)
                    print(tb_str, file=sys.stderr)

        asyncio.run_coroutine_threadsafe(task(), global_loop)
        return response


# 定义一个全局变量，用于存储从 JSON 文件中读取的数据
memory_cache: Dict[str, Any] = {}


# 读取 JSON 文件并存入内存
def preload_json_data():
    # 加载 data/excel 目录下的所有 JSON 文件到内存中
    global memory_cache
    excel_dir = "data/excel"

    # 确保目录存在
    if not os.path.exists(excel_dir):
        raise FileNotFoundError(f"未找到目录: {excel_dir}")

    # 遍历目录下的所有 JSON 文件
    for filename in os.listdir(excel_dir):
        if filename.endswith(".json"):
            # 去除 .json 后缀作为 key
            key = filename[:-5]
            file_path = os.path.join(excel_dir, filename)

            try:
                memory_cache[key] = read_json(file_path)
            except Exception as e:
                print(f"加载 {filename} 时出错: {str(e)}")


global_loop: Optional[asyncio.AbstractEventLoop] = None


def start_global_event_loop() -> asyncio.AbstractEventLoop:
    global global_loop
    if global_loop is not None:
        return global_loop

    loop = asyncio.new_event_loop()

    def _run_loop():
        asyncio.set_event_loop(loop)
        loop.run_forever()

    t = threading.Thread(target=_run_loop, daemon=True)
    t.start()

    global_loop = loop
    return loop


def get_memory(key: str) -> dict:
    '''
    从内存缓存中获取数据

    :param key: 要获取的数据的名，如"activity_table"，返回"data/excel/activity_table.json"中的数据
    '''
    useMemoryCache = read_json(CONFIG_PATH)["server"]["useMemoryCache"]
    if useMemoryCache:
        # 从内存缓存中获取数据，如果不存在则尝试读取文件
        try:
            return memory_cache[key]
        except KeyError:
            print(f"警告: {key} 未在缓存中找到，正在尝试从文件中加载")
            file_path = f"data/excel/{key}.json"
            try:
                # 将加载的数据存入缓存以备后续使用
                data = read_json(file_path)
                memory_cache[key] = data
                return data
            except FileNotFoundError:
                raise KeyError(f"未找到文件: {file_path}")
            except Exception as e:
                raise ValueError(f"加载 {file_path} 时出错: {str(e)}")
    # 如果不使用内存缓存，则直接从文件中读取数据
    else:
        file_path = f"data/excel/{key}.json"
        try:
            return read_json(file_path)
        except FileNotFoundError:
            raise KeyError(f"未找到文件: {file_path}")
        except Exception as e:
            raise ValueError(f"加载 {file_path} 时出错: {str(e)}")


def update_check_in_status():
    default_data = {
        "lastCheckInTs": 0,
        "lastResetDate": "2000-01-01"
    }

    server_data = read_json(SERVER_DATA_PATH)
    sync_data = read_json(SYNC_DATA_TEMPLATE_PATH)

    check_in_data = server_data.get("checkInData", None)
    if check_in_data is None:
        not_default = False
        check_in_data = default_data
    else:
        not_default = True

    # 获取当前时间（设备本地时区）
    now_local = datetime.now().astimezone()
    today_date = now_local.date()
    current_month = now_local.month
    current_year = now_local.year

    # 处理lastResetDate
    last_reset_date = datetime.strptime(
        check_in_data["lastResetDate"], "%Y-%m-%d"
    ).date()
    last_reset_month = last_reset_date.month  # 最后一次签到的月份
    last_reset_year = last_reset_date.year  # 最后一次签到的年份

    # 计算今天的4AM（本地时区）
    today_4am = datetime.combine(today_date, datetime.min.time()).replace(
        hour=4, minute=0, second=0, microsecond=0
    ).astimezone(now_local.tzinfo)

    # 条件1: 当前时间已经过了今天4AM
    condition1 = now_local >= today_4am

    # 条件2: 上次重置日期不是今天
    condition2 = last_reset_date != today_date

    # 条件3: 最后一次重置的月份与当前月份不同
    condition3 = current_month != last_reset_month

    # 条件4：最后一次重置的年份与当前年份不同
    condition4 = current_year != last_reset_year

    # 只有当条件1、2都满足时才重置可签到状态
    if condition1 and condition2:
        check_in_data["lastResetDate"] = today_date.isoformat()
        check_in_data["canCheckIn"] = True
        sync_data["user"]["checkIn"]["canCheckIn"] = 1
        for vs in sync_data["user"]["activity"]["CHECKIN_VS"].values():
            if isinstance(vs, dict) and "canVote" in vs:
                vs["canVote"] = 1

        write_json(server_data, SERVER_DATA_PATH)
        write_json(sync_data, SYNC_DATA_TEMPLATE_PATH)

    # 当条件3满足且非默认数据时，重置签到进度到当前月份
    if condition3 and not_default:
        sync_data["user"]["checkIn"]["checkInHistory"] = []
        sync_data["user"]["checkIn"]["checkInRewardIndex"] = 0

        check_in_cnt = int(sync_data["user"]["checkIn"]["checkInGroupId"][-2:])

        # 当条件4满足时，进行额外修正处理
        if condition4:
            year_cnt = current_year - last_reset_year
            month_offset = (12 * year_cnt) - last_reset_month

        # 当条件4不满足时，正常进行月份更迭处理
        else:
            month_offset = current_month - last_reset_month
            check_in_cnt = check_in_cnt + month_offset

        sync_data["user"]["checkIn"]["checkInGroupId"] = "signin" + str(check_in_cnt)

    # 如果今天已经签到过，则跳过
    else:
        pass
