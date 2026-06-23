import os
import asyncio
import json

from src.ActorFormation import automatic_formation
from src.pipeline import start_pipeline
from src.args import parse_args_ob


async def main():
    args = parse_args_ob()
    userdata_path = os.path.join(args.user)
    character_master_path = os.path.join(args.data, 'CharacterMaster.json')
    poster_ability_path = os.path.join(args.data, 'PosterAbilityMaster.json')
    accessory_path = os.path.join(args.data, 'accessory_processed.json')
    effect_master_path = os.path.join(args.data, 'EffectMaster.json')

    with open(userdata_path, "r", encoding="utf-8") as f:
        user_data = json.load(f)
    accessory_user = user_data["accessories"]

    with open(accessory_path, "r", encoding="utf-8") as f:
        accessory_data = json.load(f)
    accessory_list = {item["CharacterBaseMasterId"]: item for item in accessory_data}

    async_queue = asyncio.Queue(maxsize=10)

    accessory_task, saver_task = start_pipeline(
        async_queue=async_queue,
        accessory_user=accessory_user,
        accessory_list=accessory_list,
        api_url="http://127.0.0.1:3456/calc",
        data_file=userdata_path,
        sensenotation=1146,
        leader=args.mandatory_leader,
        score_only=True,
        concurrency=10,
        # save_func=save_result
    )

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(  # ActorFormation.py
        None,
        automatic_formation,
        userdata_path, character_master_path, poster_ability_path, effect_master_path,
        tuple(args.mandatory_characters), tuple(args.mandatory_posters),
        async_queue, loop
    )

    await accessory_task
    await saver_task
    print("Finished")


if __name__ == "__main__":
    asyncio.run(main())
