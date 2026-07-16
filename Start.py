"""
python Start.py < test.json
"""
import os
import asyncio
import json
import sys

from src.ActorFormation import automatic_formation
from src.FindAccessorySolutions import processor_accessory
# from src.TeamFrontier import FrontierHeap
from src.args import parse_args


# async def stdin_reader(fin: asyncio.Event, stp: asyncio.Event, topk: FrontierHeap):
async def stdin_reader(fin: asyncio.Event, stp: asyncio.Event):
    loop = asyncio.get_running_loop()
    while True:
        line = await loop.run_in_executor(None, sys.stdin.readline)
        if not line:
            fin.set()
            break
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        ctrl = msg.get("Control")
        if ctrl is not None:
            if ctrl == "stop":
                stp.clear()
            elif ctrl == "continue":
                stp.set()
            continue

        if msg.get("FIN"):
            # final_results = topk.get_top_k()
            # result_json = [{"team": team, "score": score} for team, score in final_results]
            # print(json.dumps(result_json, ensure_ascii=False), flush=True)
            fin.set()
            break

        team_status = msg.get("team")
        team_score = msg.get("score")
        if team_status is not None and team_score is not None:
            pass
            # topk.add(team_status, team_score)  # TODO(Frocean): Push the result in the heap.


async def stdout_writer(que: asyncio.Queue, stp: asyncio.Event):
    while True:
        team = await que.get()
        if team is None:
            print(json.dumps({"FIN": True}), flush=True)
            break

        await stp.wait()

        # if team == (142150, 140530, 141550, 142360, 142160,
        #             230570, 230120, 330330, 230980, 330380,
        #             430220, 330170, 330180, 331670, 330190):
        #     print(f"team {team} has been put")
        print(json.dumps(team, ensure_ascii=False), flush=True)


async def state_expander(
        async_queue: asyncio.Queue,
        out_queue: asyncio.Queue,
        accessory_user: list,
        accessory_list: dict,
        chara_count: int
):
    loop = asyncio.get_running_loop()
    while True:  # get actor formations
        s_q = await async_queue.get()
        if s_q is None:  # EOT
            async_queue.task_done()
            break

        base_state = s_q["Result"]
        busy_chara = s_q["CharacterBaseMasterId"]

        # process accessories
        expanded_teams = await loop.run_in_executor(
            None, processor_accessory, base_state, busy_chara, accessory_user, accessory_list
        )

        for team in expanded_teams:
            await out_queue.put(team)

        chara_count += 1
        print(json.dumps({"type": "character_now", "num": chara_count+1}), flush=True)
        async_queue.task_done()
    await out_queue.put(None)


async def main():
    args = parse_args()
    # userdata_path = os.path.join(args.user)
    character_master_path = os.path.join(args.data, 'CharacterMaster.json')
    poster_ability_path = os.path.join(args.data, 'PosterAbilityMaster.json')
    accessory_path = os.path.join(args.data, 'accessory_processed.json')
    effect_master_path = os.path.join(args.data, 'EffectMaster.json')

    line = await asyncio.get_running_loop().run_in_executor(None, sys.stdin.readline)  # read a line as userdata
    if not line:
        print(json.dumps({"error": "No user data received"}))
        return

    # line = line.lstrip('\ufeff').strip()
    # if not line:
    #     print(json.dumps({"error": "No user data received"}))
    #     return

    try:
        user_data = json.loads(line.strip())
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid user JSON: {e}"}))
        return

    required_fields = ["characters", "posters", "accessories"]
    missing = [f for f in required_fields if f not in user_data]
    if missing:
        print(json.dumps({"error": f"Missing required fields: {missing}"}))
        return

    # with open(userdata_path, "r", encoding="utf-8") as f:
    #     user_data = json.load(f)
    accessory_user = user_data["accessories"]

    with open(accessory_path, "r", encoding="utf-8") as f:
        accessory_data = json.load(f)
    accessory_list = {item["CharacterBaseMasterId"]: item for item in accessory_data}

    # frontier_teams = FrontierHeap(k=1000, t=15)
    c_now = 0

    pause_event = asyncio.Event()
    pause_event.set()

    async_queue = asyncio.Queue(maxsize=10)
    out_queue = asyncio.Queue(maxsize=1023)

    fin_event = asyncio.Event()
    # reader_task = asyncio.create_task(stdin_reader(fin_event, pause_event, frontier_teams))
    reader_task = asyncio.create_task(stdin_reader(fin_event, pause_event))
    writer_task = asyncio.create_task(stdout_writer(out_queue, pause_event))
    expander_task = asyncio.create_task(state_expander(async_queue, out_queue, accessory_user, accessory_list, c_now))

    loop = asyncio.get_running_loop()
    auto_task = loop.run_in_executor(  # ActorFormation.py
        None,
        automatic_formation,
        None, character_master_path, poster_ability_path, effect_master_path,
        tuple(args.mandatory_characters), tuple(args.mandatory_posters),
        async_queue, loop, user_data
    )

    try:
        await auto_task
        await expander_task
        await writer_task
        await reader_task
        print("Finished")
    except KeyboardInterrupt:
        print("task interrupt", flush=True)

        for t in (reader_task, writer_task, expander_task):
            t.cancel()

        try:
            out_queue.put_nowait(None)
        except asyncio.QueueFull:
            pass

        fin_event.set()

        await asyncio.gather(
            reader_task, writer_task, expander_task,
            return_exceptions=True
        )

        print("cleanup done", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
