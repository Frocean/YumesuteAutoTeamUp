"""
FindAccessorySolution module is used to prune some accessory' status, and combinate with previous C/P status.
Input: status of characters and posters.
Output: status of characters, posters, and accessories.
"""


def processor_accessory(base_state, busy_chara, accessory_user, accessory_list):
    """
    Generate final status through accessory data.
    Input: base status of characters and posters tuple[10], busy character for matching status list[idk],
           user's accessory data, preprocessed accessory list
    Output: all final status tuple[n][15]
    Reminder: If there's new essential accessory appended, plz reach out to me in a timely manner.
              [other solution]: Modify accessory_processed.json and add corresponding ID into "AccessoryId"
    注意事项: 如果出现了类似蝴蝶结的通用上位饰品, 请及时通过 qq 联系本人, 也可以或自行在 accessory_processed.json 中添加对应饰品 ID.
    """
    # ---------- status for check ----------
    # if base_state and base_state[0][:5] == (150010, 150040, 150020, 150030, 142290):
    #     print("Characters' status: base_state with characters (150010, 150040, 150020, 150030, 142290)")
    #     for base in base_state:
    #         print(base)
    # else:
    #     return []
    # ---------------------------------
    a_status = set()
    a_busy = set()
    a_user = {al[0] for al in accessory_user}
    # print(base_state)

    _default = 331670  # 48%
    # _default = 331710  # Time-sensitive parameter. Analysis if birthday/ct accessory doesn't increase score.
    ct_default = 331540
    a_default = {_default}
    if ct_default in a_user:
        a_default.add(ct_default)
    a_list = [a_default.copy() for _ in range(5)]
    # print(a_list)

    for i in range(5):
        for c in busy_chara[i]:
            a_list[i] |= {a for a in accessory_list[c].get("AccessoryId", []) if a in a_user}
            # print(a_list[i])

    for a1 in a_list[0]:
        a_busy.add(a1)
        for a2 in a_list[1]:
            if a2 not in a_default and a2 in a_busy:
                continue
            a_busy.add(a2)
            for a3 in a_list[2]:
                if a3 not in a_default and a3 in a_busy:
                    continue
                a_busy.add(a3)
                for a4 in a_list[3]:
                    if a4 not in a_default and a4 in a_busy:
                        continue
                    a_busy.add(a4)
                    for a5 in a_list[4]:
                        if a5 not in a_default and a5 in a_busy:
                            continue
                        a_busy.add(a5)
                        a_status.add((a1, a2, a3, a4, a5))
                        a_busy.discard(a5)
                    a_busy.discard(a4)
                a_busy.discard(a3)
            a_busy.discard(a2)
        a_busy.discard(a1)

    a_result = []
    for state_c_p in base_state:
        for state_a in a_status:
            a_result.append(state_c_p + state_a)
    return a_result


def processor_accessory_server(base_state, busy_chara, accessory_user, accessory_list, leader=None):
    """
    Generate final status through accessory data.
    Input: base status of characters and posters list[10], busy character for matching status list[idk],
           user's accessory data, preprocessed accessory list
    Output: all final status list[n][15]
    """
    a_status = set()
    a_busy = set()
    a_user = {al[0] for al in accessory_user}

    _default = 331670  # 48%
    # _default = 331710  # Time-sensitive parameter. Analysis if birthday/ct accessory doesn't increase score.
    ct_default = 331540
    a_default = {_default}
    if ct_default in a_user:
        a_default.add(ct_default)
    a_list = [a_default.copy() for _ in range(5)]

    for i in range(5):
        for c in busy_chara[i]:
            a_list[i] |= {a for a in accessory_list[c].get("AccessoryId", []) if a in a_user}

    for a1 in a_list[0]:
        a_busy.add(a1)
        for a2 in a_list[1]:
            if a2 not in a_default and a2 in a_busy:
                continue
            a_busy.add(a2)
            for a3 in a_list[2]:
                if a3 not in a_default and a3 in a_busy:
                    continue
                a_busy.add(a3)
                for a4 in a_list[3]:
                    if a4 not in a_default and a4 in a_busy:
                        continue
                    a_busy.add(a4)
                    for a5 in a_list[4]:
                        if a5 not in a_default and a5 in a_busy:
                            continue
                        a_busy.add(a5)
                        a_status.add((a1, a2, a3, a4, a5))
                        a_busy.discard(a5)
                    a_busy.discard(a4)
                a_busy.discard(a3)
            a_busy.discard(a2)
        a_busy.discard(a1)

    a_result = []
    for state_c_p in base_state:
        for state_a in a_status:
            state_bot = {"characters": state_c_p[:5],
                         "posters": state_c_p[5:10],
                         "accessories": state_a}
            if leader is not None:
                state_bot["leader"] = leader
            a_result.append(state_bot)
    return a_result
