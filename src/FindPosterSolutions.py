"""
FindPosterSolution module is used to prune some posters' status in preliminary preprocessing phase.
Input: relative files' path.
Output: preliminary character with useful posters.
        Posters are maintained by a DAG which records the dominating relations.
After attribute and filter, the number of states decreased by 96.7% than enum.
After domination DAG, the number of states decreased by 99.961% than enum.
"""
import json
from collections import defaultdict

import copy


class CharacterFilter:
    """
    Filter unnecessary elements for character. Options included:
    "Id", "CharacterBaseMasterId", "Name", "Description", "Rarity", "Attribute", "MinLevelStatus", "StarActMasterId",
    "AwakenStarActMasterId", "AwakenStarActMasterId", "SenseMasterId", "ForbidGenericItemBloom",
    "BloomBonusGroupMasterId", "SenseEnhanceItemGroupMasterId", "FirstEpisodeReleaseItemGroupId",
    "SecondEpisodeReleaseItemGroupId", "CharacterAwakeningItemGroupMasterId", "DisplayStartAt", "DisplayEndAt",
    "UnlockText", "Categories", "LeaderSenseMasterId", "MaxTalentStage", "MaxTalentStageReleaseDate",
    "SecondarySenseMasterId", "SecondaryAttribute"
    Input: Data in userdata.json and CharacterMaster.json
    Output: Data has structure like:
    {'CharacterBaseMasterId': [405, (12w)], 'Rarity': 'Rare4', 'Attribute': ['Cheerful', 'Colorful']}
    """
    def __init__(self, included_parameter=None):
        included_default = {"CharacterBaseMasterId", "Rarity", "Attribute"}
        if included_parameter:
            self.included = included_default.union(set(included_parameter))
        else:
            self.included = included_default

    def apply(self, data):
        data = copy.deepcopy(data)
        # pre-process "SecondaryAttribute"
        if "CharacterBaseMasterId" in data:
            if not isinstance(data["CharacterBaseMasterId"], list):
                data["CharacterBaseMasterId"] = [data["CharacterBaseMasterId"]]
        if "Attribute" in data:
            if not isinstance(data["Attribute"], list):
                data["Attribute"] = [data["Attribute"]]
        if data.get("SecondaryCharacterBaseMasterId", []):
            data["CharacterBaseMasterId"].append(data["SecondaryCharacterBaseMasterId"])
        if data.get("SecondaryAttribute", []):
            data["Attribute"].append(data["SecondaryAttribute"])
        data = {k: v for k, v in data.items() if k in self.included}
        return data


class PosterFilter:
    """
    Filter unnecessary elements for posters. Options included:
    "AddSenseLightAmplification", "AddSenseLightVariable", "AddSenseLightSpecial", "AddSenseLightSupport",
    (check "FireTimingType" to differentiate effects)
    "AddSenseLightSelf", "SenseRecastDown",
    "VocalUp", "ExpressionUp", "ConcentrationUp", "PerformanceUp", "PerformanceLimitUp",
    "PrincipalGaugeGain", "PrincipalGaugeUp", "PrincipalGaugeLimitUp",
    "ScoreGainOnVocal", "ScoreGainOnExpression", "ScoreGainOnConcentration", "ScoreGainOnScore",
    "LifeGuard", "LifeHealing",
    "PlayerRankPointUp", "RewardUp",
    "StarActScoreUp",
    "FinalPerformanceUpCancelSense",
    Raw data seems like:
        {'Id': 230050, 'Name': 'ちびっこチームワーク', ...} <-- leader skill
        {'Id': 230051, 'Name': '演技力アップⅢ', ...}      <-- normal skill
    Effect data seems like:
        {"Id":70052001, "Type":"PerformanceUp", ...,
         "Conditions":[{"Condition":"Attribute", "Value":2}],
         "Triggers":[{"Trigger":"Attribute", "Value":4}], ...}
    Output will filter particular skill items.
    """
    def __init__(self, excluded_parameter=None):
        self.excluded = {excluded_parameter}
        self.n2attr = {
            1: "Cute",
            2: "Cool",
            3: "Colorful",
            4: "Cheerful"
        }
        self.group = {
            3: [402, 403, 404, 405],  # 発動条件：美兎・カミラ・蕾・叶羽が装備
            4: [1, 4],  # 発動条件：シリウス・劇団電姫に所属するアクターが装備
            5: [2, 3]  # 発動条件：Eden・銀河座に所属するアクターが装備
        }

    @staticmethod
    def _merge_effects(effects):
        merged = {}
        for eff in effects:
            key = (eff.get("Type"), eff.get("FireTimingType"))
            if key not in merged:
                merged[key] = eff.copy()  # 保留第一条的结构
            else:
                merged[key]["Value"] += eff["Value"]
        return list(merged.values())

    def apply(self, data, poster, character, effect):  # process raw data
        # print(data)
        data = self.filter_level(data, poster[1])
        if Default_filter:  # decrease 46482
            data = self.filter_leader(data)
        data_bot = []
        for ab in data:
            boolean = True
            effect_id = self.get_effect_id(ab)
            effect_data = effect.get(effect_id, [])
            # print(effect_data)
            if self.filter_effect(effect_data, character):
                boolean = False
            if boolean:
                data_bot.append(self.filter_final(effect_data, poster[1] + poster[2]))
        data_bot = self._merge_effects(data_bot)
        return {"Id": poster[0], "Effects": data_bot}

    # Filter unnecessary effects for posters.
    def filter_effect(self, data, character):  # process effect data
        # global tot  # original: 155956 now: 30501
        # excluded_effect_default = set()
        excluded_effect_default = {"PlayerRankPointUp", "RewardUp"}  # decrease 4572
        # print(data)
        if Default_filter:
            # decrease 32332 finally
            effect_default = {"PerformanceUp", "ScoreGainOnVocal", "ScoreGainOnExpression", "ScoreGainOnConcentration"}
        else:
            effect_default = set()
        if self.excluded:
            effect_default = effect_default.union(set(self.excluded))
        excluded_effect_default = excluded_effect_default.union(set(effect_default))
        if data["Type"] in excluded_effect_default:
            return True
        if self.filter_triggers(data, character):
            return True
        # print(data["Triggers"])
        # tot += 1  # check effects' amount if needed
        return False

    """
    Filter useless elements for posters. Options:
    "Id", "Type", "Range", "CalculationType", "Details", "Conditions", "DurationSecond", "Triggers", "FireTimingType"
    """
    @staticmethod
    def filter_final(data, level):
        # included_effect_default = {"Id"}
        included_final = {}
        detail_list = data.get("Details", [])
        matched = next((d for d in detail_list if d.get("Level") == level), None)
        if matched:
            included_final["Value"] = matched["Value"]
        if "Type" in data:
            included_final["Type"] = data["Type"]
        if "FireTimingType" in data:
            included_final["FireTimingType"] = data["FireTimingType"]
        # print(included_final)
        return included_final

    @staticmethod
    def filter_leader(data):
        return [t for t in data if t.get("Type") != "Leader"]

    @staticmethod
    def filter_level(data, level):
        return [ab for ab in data if ab.get("ReleaseLevelAt", 0) <= level]

    """
    filter_triggers method is used to check Trigger with options:
        "Attribute", "CharacterBase", "CharacterBaseGroup(3/4/5)", "Company"
    """
    def filter_triggers(self, data, character):
        # print(character)
        trig_checker = {"Attribute", "CharacterBase", "Company", "CharacterBaseGroup"}
        triggers = data.get("Triggers", [])
        # print(triggers)
        for trigger in triggers:
            t = trigger["Trigger"]
            v = trigger["Value"]
            if t == "Attribute":  # decrease 6410
                v = self.n2attr.get(v, None)
                if v not in character["Attribute"]:
                    return True
                else:
                    continue
            if t == "CharacterBase":  # decrease 7668
                if v not in character["CharacterBaseMasterId"]:
                    return True
                else:
                    continue
            if t == "Company":  # decrease 31341
                chara_set = {c_v // 100 for c_v in character["CharacterBaseMasterId"]}
                if v not in chara_set:
                    return True
                else:
                    continue
            if t == "CharacterBaseGroup":
                if v == 3:  # decrease 202
                    if all(c_v not in self.group.get(v) for c_v in character["CharacterBaseMasterId"]):
                        return True
                    else:
                        continue
                if v == 4 or v == 5:  # decrease 512
                    if all(c_v // 100 not in self.group.get(v) for c_v in character["CharacterBaseMasterId"]):
                        return True
                    else:
                        continue
                else:
                    print(f"unknown type in poster with CharacterBaseMasterId {v}")
            else:
                print(f"unknown trigger in poster with string {t}")
        return False

    @staticmethod
    def get_effect_id(data):
        branches = data.get("Branches", [])
        branch = next((b for b in branches if b.get("Order") == 1), None)
        if not branch:
            print(f"Poster {data.get('PosterMasterId')}'s sense {data.get('Id')} doesn't have Branches")
            return None
        branch_effect = branch.get("BranchEffects", [])
        effect = next((b for b in branch_effect if b.get("Order") == 1), None)
        if not effect:
            print(f"Poster {data.get('PosterMasterId')}'s sense {data.get('Id')} doesn't have EffectMasterId")
            return None
        return effect.get("EffectMasterId")


class PosterSolution:
    """
    Final solution for posters.
    Store current character in userdata with its useful posters. Posters have additional domination DAG saved.
     Special judge options also included:
    "AddSenseLightAmplification", "AddSenseLightVariable", "AddSenseLightSpecial", "AddSenseLightSupport",
    (check "FireTimingType" to differentiate effects)
    "AddSenseLightSelf", "SenseRecastDown",
    "VocalUp", "ExpressionUp", "ConcentrationUp", "PerformanceUp", "PerformanceLimitUp",
    "PrincipalGaugeGain", "PrincipalGaugeUp", "PrincipalGaugeLimitUp",
    "ScoreGainOnVocal", "ScoreGainOnExpression", "ScoreGainOnConcentration", "ScoreGainOnScore",
    "LifeGuard", "LifeHealing",
    "PlayerRankPointUp", "RewardUp",
    "StarActScoreUp",
    "FinalPerformanceUpCancelSense"
    Output: A dictionary with the key: character base id, value: self's data.
    """
    def __init__(self):
        self.poster = {}
        self.dominate = {}
        self.dominated = {}
        self.supreme_arr = set()
        self.supreme_dic = set()

    @staticmethod
    def _effects_to_dict(effects):
        return {(e["Type"], e["FireTimingType"]): e["Value"] for e in effects}

    def check_if_dominate(self, data1, data2):
        dict1 = self._effects_to_dict(data1)
        dict2 = self._effects_to_dict(data2)
        for k, v in dict2.items():
            if k not in dict1 or dict1[k] < v:
                return False
        return True

    @staticmethod
    def check_if_spj(effect1, effect2):
        spj_1 = [0] * 3
        spj_2 = [0] * 3

        for e in effect1:
            effect_type = e.get("Type")
            if effect_type == "SenseRecastDown":
                spj_1[0] = e.get("Value", 0)
            if effect_type == "AddSenseLightVariable":
                if e.get("FireTimingType") == "Passive":
                    spj_1[1] = e.get("Value", 0)
                else:
                    spj_1[2] = e.get("Value", 0)

        for e in effect2:
            effect_type = e.get("Type")
            if effect_type == "SenseRecastDown":
                spj_2[0] = e.get("Value", 0)
            if effect_type == "AddSenseLightVariable":
                if e.get("FireTimingType") == "Passive":
                    spj_2[1] = e.get("Value", 0)
                else:
                    spj_2[2] = e.get("Value", 0)

        for i in range(3):
            if spj_1[i] and spj_2[i]:
                if spj_1[i] != spj_2[i]:
                    return True
        return False

    def push(self, data):
        # print(data)
        index = data["Id"]
        self.poster[index] = data
        self.dominate[index] = []
        self.dominated[index] = []

    def generate_graph(self):
        index = list(self.poster.keys())
        for i in index:
            data1 = self.poster[i]
            for j in index:
                if i == j:
                    continue
                data2 = self.poster[j]
                if self.check_if_spj(data1["Effects"], data2["Effects"]):
                    continue
                if self.check_if_dominate(data1["Effects"], data2["Effects"]):
                    self.dominate[i].append(j)
                    self.dominated[j].append(i)
        self.supreme_arr = {i for i in self.poster if not self.dominated.get(i)}
        # for i in index:
        #     if not self.dominated[i]:
        #         self.supreme_arr.add(i)

    # superfluous try to combine a with p
    # def multi_accessory(self, character):
    #     if (character == 401) or (character == 102):
    #         poster_bot = []
    #         for p in self.poster:
    #             boolean = False
    #             effects = p.get("Effects")
    #             for e in effects:
    #                 if (e.get("Type") == "AddSenseLightVariable") and (e.get("FireTimingType") == "StartLive"):
    #                     boolean = True
    #                     break
    #             co_p = copy.deepcopy(p)
    #             if boolean:
    #                 for e in co_p.get("Effects"):
    #                     if (e.get("Type") == "AddSenseLightVariable") and (e.get("FireTimingType") == "StartLive"):
    #                         e["Value"] += 3
    #                         break
    #             else:
    #                 co_p["Effects"].append({
    #                     "Type": "AddSenseLightVariable",
    #                     "FireTimingType": "StartLive",
    #                     "Value": 3
    #                 })
    #             poster_bot.append(co_p)
    #             print(poster_bot)
    #         self.poster.extend(poster_bot)


def find_poster_solutions(
        userdata_path=None,
        character_master_path="../data/CharacterMaster.json",
        poster_ability_path="../data/PosterAbilityMaster.json",
        effect_master_path="../data/EffectMaster.json",
        userdata=None
):
    if userdata is not None:
        user_data = userdata
    else:
        with open(userdata_path, "r", encoding="utf-8") as f:
            user_data = json.load(f)
    character_list = user_data["characters"]
    poster_list = user_data["posters"]

    with open(character_master_path, "r", encoding="utf-8") as f:
        characters_data = json.load(f)
    characters_id_master = {item["Id"]: item for item in characters_data}

    # with open("./PosterMaster.json", "r", encoding="utf-8") as f:
    #     posters_data = json.load(f)
    # posters_id_master = {item["Id"]: item for item in posters_data}

    with open(poster_ability_path, "r", encoding="utf-8") as f:
        posters_ability = json.load(f)
    posters_ability_master = defaultdict(list)
    for item in posters_ability:
        posters_ability_master[item["PosterMasterId"]].append(item)

    with open(effect_master_path, "r", encoding="utf-8") as f:
        effects_data = json.load(f)
    effect_id_master = {item["Id"]: item for item in effects_data}

    solutions = {}
    # search matching poster for every id character
    for chara in character_list:  # characters total: 254
        c_id = chara[0]
        c_data = characters_id_master.get(c_id)
        filter_c_c = CharacterFilter()
        c_data_filtered = filter_c_c.apply(c_data)
        # print(c_data_filtered)
        filter_c_p = PosterSolution()
        # check if new elements are appended
        # poster id: poste[0]  poster level: poste[1]
        for poste in poster_list:  # original: 183 sense filtered: 89
            p_data = posters_ability_master.get(poste[0], [])
            filter_p_p = PosterFilter()
            p_sense_filtered = filter_p_p.apply(p_data, poste, c_data_filtered, effect_id_master)
            if p_sense_filtered.get("Effects", []):
                # print(p_sense_filtered)
                filter_c_p.push(p_sense_filtered)
        # filter_c_p.multi_accessory(c_data_filtered["CharacterBaseMasterId"])
        filter_c_p.generate_graph()
        # print(filter_c_p.poster)
        # print(poster_list)
        # a = 0
        # b = 0
        # for poste in poster_list:
        #     if poste[0] in filter_c_p.poster:
        #         if filter_c_p.dominated[poste[0]]:
        #             a += 1
        #         else:
        #             b += 1
        # print(f"posters: {a + b}, be dominated: {a}, supreme: {b}")
        # print(tot)
        # print(filter_c_p.poster)
        solutions[c_id] = filter_c_p
        # print(filter_c_p.poster)
    # print(solutions)
    return solutions
    # print(f"total tot number: {tot}")


Default_filter = True
tot = 0

if __name__ == "__main__":
    solution = find_poster_solutions(userdata_path="../test.json")
