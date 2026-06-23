import asyncio
import queue
import aiohttp

from src.FindAccessorySolutions import processor_accessory_server


async def _send_one_request(session, formation: dict, api_url: str, data_file: str,
                            sensenotation: int, score_only: bool):
    """
    Server的请求体为:
    {
        "data_file": "example.json",
        "team": {
            "actors": [46, 1, 5, 29, 12],
            "posters": [141, 189, 107, 184, 183],
            "accessories": [340, 493, 492, 356, 350],
            "leader": 1
        },
        "photo": [2, 3, 4, 5, 6],
        "sensenotation": 1146,
        "score_only": false
    }
    本模块将提供 data_file, team, sensenotation 和 score_only 部分. 其余部分按服务器默认.
    # TODO(Frocean): 服务器仍未适配好, 与本模块及项目无关, 详细请联系 @Ohnkyta
    """
    payload = {
        "data_file": data_file,
        "team": formation,
        "sensenotation": sensenotation,
        "score_only": score_only
    }
    try:
        async with session.post(api_url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            data = await resp.json()
            if "error" in data:
                print(f"[ERROR] Server error: {data['error']} | team={formation}")
            return {"team": formation, "result": data}
    except Exception as e:
        print(f"[ERROR] Request failed: {e} | team={formation}")
        return {"team": formation, "error": str(e)}


async def _accessory_and_request_loop(
    async_queue: asyncio.Queue,
    result_queue: asyncio.Queue,
    accessory_user: list,
    accessory_list: dict,
    api_url: str,
    data_file: str,
    sensenotation: int,
    leader: int,
    score_only: bool = False,
    concurrency: int = 10
):
    """
    Get ActorFormation from queue, expand status from Accessory and send request.
    Computed result will be stored in result_queue.
    """
    semaphore = asyncio.Semaphore(concurrency)
    loop = asyncio.get_running_loop()

    async def _bounded_send(session, team):
        async with semaphore:
            for attempt in range(557):
                result = await _send_one_request(session, team, api_url, data_file,
                                               sensenotation, score_only)
                if "error" not in result:
                    return result
            print(f"time out for team={team}")

    async with aiohttp.ClientSession() as session:
        while True:  # get actor formations
            s_q = await async_queue.get()
            if s_q is None:  # EOT
                async_queue.task_done()
                break

            base_state = s_q["Result"]
            busy_chara = s_q["CharacterBaseMasterId"]

            # process accessories
            expanded_teams = await loop.run_in_executor(
                None, processor_accessory_server, base_state, busy_chara, accessory_user, accessory_list, leader
            )

            # send request
            tasks = [asyncio.create_task(_bounded_send(session, t)) for t in expanded_teams]
            for coro in asyncio.as_completed(tasks):
                res = await coro
                await result_queue.put(res)

            async_queue.task_done()

    await result_queue.put(None)


async def _result_saver_loop(result_queue: asyncio.Queue, save_func):
    result_count = 0
    while True:
        item = await result_queue.get()
        result_count += 1
        if item is None:
            result_queue.task_done()
            print(f"EOT for result. Total results: {result_count-1}")
            break
        # save_func(item)
        print(item)
        result_queue.task_done()


def start_pipeline(
    async_queue: asyncio.Queue,
    accessory_user: list,
    accessory_list: dict,
    api_url: str = "http://127.0.0.1:3456/calc",
    data_file: str = "example.json",
    sensenotation: int = 1146,
    leader: int = 0,
    score_only: bool = False,
    concurrency: int = 10,
    save_func=print
):
    sync_queue = queue.Queue(maxsize=10)
    result_queue = asyncio.Queue()

    accessory_task = asyncio.create_task(
        _accessory_and_request_loop(
            sync_queue, result_queue, accessory_user, accessory_list, api_url,
            data_file, sensenotation, leader, score_only, concurrency
        )
    )
    saver_task = asyncio.create_task(_result_saver_loop(result_queue, save_func))

    return accessory_task, saver_task