"""
ActorFormation module is used for building formation automatically.
Input: relative files' path.
Output: N-Top results among all status.
"""
import json
import os
import asyncio

import time

from .FindPosterSolutions import find_poster_solutions, CharacterFilter
from .args import parse_args

from collections import defaultdict


class CheckUnrepeated:
    """
    Accelerate auto formation for actors by pruning illegal characters' status.
    Some important data is stored in this class simultaneously.
    Input: charm(c_base_id), poste(p_base_id), posit(position of leader), c_cache
    Output: A legal list for character on [:posit] axis, eg: [110010, 110020, ...]
    """
    def __init__(self):
        self.chara_master = {  # characters' id
            101, 102, 103, 104, 105, 106,
            201, 202, 203, 204, 205,
            301, 302, 303, 304, 305,
            401, 402, 403, 404, 405
        }
        self.poste_dedupe = [  # deduplication for particular posters
            [230090, 230100, 230110, 230120],  # troupe
            [230510, 230570, 230640, 230720]   # fd series
        ]
        self.poste_map = {}  # memorize the initialization of deduplication
        self._status = set()  # enum bottle for c/p status
        self._result_poste = []
        self.manda_chara = [0] * 5  # record mandatory characters and [index] position
        self.manda_poste = [0] * 5  # record mandatory posters and [index] position
        self.prior_chara = set()  # record mandatory characters with void position
        self.prior_poste = set()  # record mandatory posters with void position
        self.num_master = {1, 2, 3, 4, 5}
        self.state_base = [0, 0, 0, 0, 0]  # be used for initialize bfs status
        self.chara_mid2id = defaultdict(list)

    def urp_filter_c(self, master, filtlist=None, c_cache=None):  # filter characters' filtlist in master
        if not c_cache:
            return {f for f in master if f not in filtlist}
        charm_bot = master.copy()
        for f in filtlist:
            charm_bot.discard(f)
        c_bot = set()
        for c in charm_bot:
            for i in self.chara_mid2id[c]:
                charb = c_cache[i].get("CharacterBaseMasterId", [])
                charb_len = len(charb)
                if charb_len == 1:
                    c_bot.add(i)
                    continue
                elif charb_len == 2:
                    if c == charb[0]:
                        j = charb[1]
                    else:
                        j = charb[0]
                    if j in filtlist or j == charb[0]:
                        continue
                    c_bot.add(i)
                else:
                    print(f"Unknown CharacterBaseMasterId {charb}")
        return c_bot

    def urp_filter_dag(self, filter_c_p, poste_busy):
        # print(f"come in")
        c_p_bot = filter_c_p.supreme_arr.copy()
        boolean = True
        while boolean:  # update current supreme queue by busy posters
            # print(f"check")
            boolean = False  # check if status changed
            for p in poste_busy:  # check busy poster's domination
                if p not in c_p_bot:  # if busy poster in supreme
                    continue
                p_son = filter_c_p.dominate[p]  # check posters it dominates
                for son in p_son:
                    if son in c_p_bot:
                        continue
                    bson = True
                    for f in filter_c_p.dominated[son]:  # check one son's father
                        if f not in c_p_bot:  # father not in supreme
                            bson = False  # no need to push son in supreme
                            break
                    if bson:  # need to push son in supreme
                        c_p_bot.add(son)
                        # print(f"add son {son} in supreme posters")
                        boolean = True  # status changed
        postb_bot = set()
        postb_not = []
        for p in poste_busy:
            if p in self.poste_map:  # collect posters in map
                postb_bot.update(self.poste_map[p])
            else:  # collect posters not in map
                postb_not.append(p)
        postb_bot.update(postb_not)
        c_p_bot.difference_update(postb_bot)
        return c_p_bot

    # def urp_filter_i(self, chara, poste, c_cache):  # initialize mandatory elements
    def urp_filter_i(self, chara, poste):
        for posters in self.poste_dedupe:  # initialization for particular posters deduplication
            shared_set = set(posters)
            for p in posters:
                self.poste_map[p] = shared_set
        for i in range(5):  # Deal with mandatory and prior character.
            i2 = i << 1
            bid = chara[i2]
            pos_c = chara[i2 + 1] - 1
            # bool_either = False
            if not pos_c < 0:  # mandatory character with position
                self.manda_chara[pos_c] = bid
                # print(f"character{bid} at {pos_c}")
                # bool_either = True
            elif bid:  # mandatory character without position
                self.prior_chara.add(bid)
                # bool_either = True
            bid = poste[i2]
            pos_p = poste[i2 + 1]
            if bid and not pos_p:
                self.prior_poste.add(bid)

    def urp_filter_n(self, num_busy=None):  # check {1, 2, 3, 4, 5} which is used and discard
        number_bot = self.num_master.copy()
        if num_busy:
            for n in num_busy:
                number_bot.discard(n)
        return number_bot

    def urp_filter_p(self, chara, poste):  # initialize mandatory posters for current status
        # TODO(Frocean): Add preprocessing persistent domination DAG module at convenience
        self.manda_poste = [0] * 5
        charp = list(chara)
        for i in range(5):  # Deal with mandatory character's poster. Others will process in poster processor.
            i2 = i << 1
            bid = poste[i2]
            pos_p = poste[i2 + 1]
            # bool_either = False
            if not pos_p < 0:
                for n, c in enumerate(charp):
                    if pos_p == c:
                        self.manda_poste[n] = bid
                        break

    def processor_character(self, c_cache):
        stime = time.time()
        queue = []
        self._status = set()
        manda_busy = {i+1 for i in range(5) if self.manda_chara[i]}  # initialize busy position
        leng = len(self.prior_chara)
        if leng:  # check prior characters' status initially
            # not essential to concern duplicated status between mandatory/prior characters
            for n in self.urp_filter_n(manda_busy):
                for c in self.prior_chara:
                    state_bot = list(self.manda_chara)
                    state_bot[n - 1] = c
                    state_bot = tuple(state_bot)
                    self._status.add(state_bot)
                    queue.append(state_bot)
            for i in range(leng - 1):
                queue_next = []
                for state in queue:
                    nums_bot = {i+1 for i, p in enumerate(state) if p}  # | manda_busy
                    busy_bot = {c for c in state if c}
                    for n in self.urp_filter_n(nums_bot):
                        for c in self.urp_filter_c(self.prior_chara, busy_bot):
                            state_bot = list(state)
                            state_bot[n - 1] = c
                            state_bot = tuple(state_bot)
                            if state_bot in self._status:
                                continue
                            self._status.add(state_bot)
                            queue_next.append(state_bot)
                queue = queue_next
        leng = 5 - leng - len(manda_busy)
        if leng == 5:  # A condition which would never be used. So why I code this?
            for n in self.urp_filter_n():
                for c in self.urp_filter_c(self.chara_master, set(), c_cache):
                    state_bot = list(self.state_base)
                    state_bot[n - 1] = c
                    state_bot = tuple(state_bot)
                    self._status.add(state_bot)
                    queue.append(state_bot)
            leng -= 1
        if not queue:
            state_bot = tuple(self.manda_chara)
            self._status.add(state_bot)
            queue.append(state_bot)
        for i in range(leng):  # complete the status for characters
            queue_next = []
            for state in queue:
                nums_bot = {i+1 for i, p in enumerate(state) if p}
                busy_bot = {i for c in state if c for i in c_cache[c].get("CharacterBaseMasterId", [])}
                for n in self.urp_filter_n(nums_bot):
                    for c in self.urp_filter_c(self.chara_master, busy_bot, c_cache):  # now need to concern
                        state_bot = list(state)
                        state_bot[n - 1] = c
                        state_bot = tuple(state_bot)
                        if state_bot in self._status:
                            continue
                        self._status.add(state_bot)
                        queue_next.append(state_bot)
            queue = queue_next
        print(f"cost time {time.time() - stime}s in {len(queue)} solutions")
        return queue

    def processor_poster(self, clist, solutions):
        # print(clist)
        stime = time.time()
        queue = []
        # print(self.manda_poste)
        self._result_poste = []
        self._status = set()
        manda_busy = {i+1 for i in range(5) if self.manda_poste[i]}  # initialize busy position
        length = len(self.prior_poste)
        if length:  # check prior characters' status initially
            for n in self.urp_filter_n(manda_busy):  # also feel free to loop, user will check it
                for p in self.prior_poste:
                    state_bot = list(self.manda_poste)
                    state_bot[n - 1] = p
                    state_bot = tuple(state_bot)
                    self._status.add(state_bot)
                    queue.append(state_bot)
            for i in range(length - 1):
                queue_next = []
                for state in queue:
                    nums_bot = {i+1 for i, p in enumerate(state) if p}
                    busy_bot = {p for p in state if p}
                    for n in self.urp_filter_n(nums_bot):
                        for p in self.urp_filter_c(self.prior_poste, busy_bot):  # feel free, feel free
                            state_bot = list(state)
                            state_bot[n - 1] = p
                            state_bot = tuple(state_bot)
                            if state_bot in self._status:
                                continue
                            self._status.add(state_bot)
                            queue_next.append(state_bot)
                queue = queue_next
        length = 5 - length - len(manda_busy)
        if length == 5:  # Why I code this module again?
            for n in self.urp_filter_n():
                # if clist == (150030, 142420, 150020, 150040, 150010):
                #     print(f"check for first time, now n: {n}, chara: {clist[n-1]}")
                # print(f"clist: {clist}")
                for p in solutions[clist[n-1]].supreme_arr:  # feel free, feel free
                    state_bot = list(self.state_base)
                    state_bot[n - 1] = p
                    state_bot = tuple(state_bot)
                    self._status.add(state_bot)
                    queue.append(state_bot)
            length -= 1
        if not queue:
            state_bot = tuple(self.manda_poste)
            self._status.add(state_bot)
            queue.append(state_bot)
        for i in range(length):
            queue_next = []
            for state in queue:
                nums_bot = {i+1 for i, p in enumerate(state) if p}
                busy_bot = {p for p in state if p}
                for n in self.urp_filter_n(nums_bot):
                    poste_bot = self.urp_filter_dag(solutions[clist[n-1]], busy_bot)
                    for p in poste_bot:
                        state_bot = list(state)
                        state_bot[n - 1] = p
                        state_bot = tuple(state_bot)
                        if state_bot in self._status:
                            continue
                        self._status.add(state_bot)
                        queue_next.append(state_bot)
            queue = queue_next
        for q in queue:
            res_bot = [None] * 10
            res_bot[:5] = clist  # TODO(Frocean): Send c/p status respectively may accelerate a lot.
            res_bot[5:10] = list(q)
            self._result_poste.append(tuple(res_bot))
        print(f"cost time {time.time() - stime}s in {len(queue)} solutions")
        return self._result_poste


def automatic_formation(
        userdata_path="../Yumetest.json",
        character_master_path="../data/CharacterMaster.json",
        poster_ability_path="../data/PosterAbilityMaster.json",
        effect_master_path="../data/EffectMaster.json",
        mandatory_characters=(150010, 0, 150020, 0, 150030, 0, 150040, 0, 0, 0),
        mandatory_posters=(330380, 150030, 230120, 150040, 0, 0, 0, 0, 0, 0),
        pipeline_queue=None,
        loop=None,
        userdata=None
):
    # start_time = time.time()

    if userdata is not None:
        user_data = userdata
    else:
        with open(userdata_path, "r", encoding="utf-8") as f:
            user_data = json.load(f)
    character_list = user_data["characters"]
    # poster_list = user_data["posters"]

    with open(character_master_path, "r", encoding="utf-8") as f:
        characters_data = json.load(f)
    characters_id_master = {item["Id"]: item for item in characters_data}

    # current_time = time.time() - start_time
    # print(f"check data in {current_time}s")

    c_cache = {}
    checker = CheckUnrepeated()
    for chara in character_list:
        c_id = chara[0]
        c_data = characters_id_master.get(c_id)
        filter_c_c = CharacterFilter()
        c_data_filtered = filter_c_c.apply(c_data)
        for c in c_data_filtered["CharacterBaseMasterId"]:
            checker.chara_mid2id[c].append(c_id)
        c_cache[c_id] = c_data_filtered
    # print(c_cache)
    checker.urp_filter_i(mandatory_characters, mandatory_posters)
    poster_solutions = find_poster_solutions(userdata_path,
                                             character_master_path,
                                             poster_ability_path,
                                             effect_master_path,
                                             userdata)
    print(f"check characters...")
    result_c = checker.processor_character(c_cache)
    # put_count = 0
    for r in result_c:
        print(f"check posters...")
        # print(r)
        checker.urp_filter_p(r, mandatory_posters)
        charb_id = [None] * 5
        for n, c in enumerate(r):
            charb_id[n-1] = c_cache[c].get("CharacterBaseMasterId", [])
        # print(charb_id)
        result = checker.processor_poster(r, poster_solutions)
        if pipeline_queue is not None:
            asyncio.run_coroutine_threadsafe(
                pipeline_queue.put({"Result": result, "CharacterBaseMasterId": charb_id}),
                loop
            )
        #     put_count += 1
        #     if put_count % 100 == 0:
        #         print(f"put {put_count} items into queue, queue size {pipeline_queue.qsize()}")
    if pipeline_queue is not None:
        asyncio.run_coroutine_threadsafe(pipeline_queue.put(None), loop)


if __name__ == "__main__":
    args = parse_args()
    userdata_path = args.user
    character_master_path = os.path.join(args.data, 'CharacterMaster.json')
    poster_ability_path = os.path.join(args.data, 'PosterAbilityMaster.json')
    accessory_path = os.path.join(args.data, 'accessory_processed.json')
    effect_master_path = os.path.join(args.data, 'EffectMaster.json')

    automatic_formation(userdata_path,
                        character_master_path,
                        poster_ability_path,
                        effect_master_path,
                        tuple(args.mandatory_characters),
                        tuple(args.mandatory_posters))
