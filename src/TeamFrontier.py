"""
FindAccessorySolution module is used to store initial results from calculator.
Every team will save t-top scores in heap which sizes k.
Input: {"team": array[15], "score": int}, An array[15] indicates Characters[5], Posters[5] and Accessories[5].
Output: Top-k results. Tuple(array[15]) per line.
"""
import heapq
from collections import defaultdict


class FrontierHeap:
    def __init__(self, k: int, t: int):
        if k < 1 or t < 1 or t >= k:
            raise ValueError("k and t must satisfy k >= 1, t >= 1, t < k")
        self.k = k
        self.t = t
        # 全局最小堆，元素: (score, tid, full_team, canonical_key)
        self.global_heap = []
        # tid -> 在 global_heap 中的索引
        self.pos = {}
        # 每个队伍的内部最小堆，key -> list of (score, tid, full_team)
        self.teams = defaultdict(list)
        self._counter = 0

    # ---------- 辅助：tid 生成 ----------
    def _next_id(self):
        self._counter += 1
        return self._counter

    # ---------- 全局索引堆操作 ----------
    def _swap(self, i: int, j: int):
        """交换 global_heap 中 i, j 两个元素，并更新 pos 映射"""
        if i == j:
            return
        heap = self.global_heap
        heap[i], heap[j] = heap[j], heap[i]
        self.pos[heap[i][1]] = i
        self.pos[heap[j][1]] = j

    def _sift_up(self, idx: int):
        """将索引 idx 的元素向上浮动到正确位置（最小堆）"""
        heap = self.global_heap
        while idx > 0:
            parent = (idx - 1) >> 1
            if heap[idx][0] < heap[parent][0]:
                self._swap(idx, parent)
                idx = parent
            else:
                break

    def _sift_down(self, idx: int):
        """将索引 idx 的元素向下沉到正确位置（最小堆）"""
        heap = self.global_heap
        n = len(heap)
        while True:
            smallest = idx
            left = (idx << 1) + 1
            right = left + 1
            if left < n and heap[left][0] < heap[smallest][0]:
                smallest = left
            if right < n and heap[right][0] < heap[smallest][0]:
                smallest = right
            if smallest != idx:
                self._swap(idx, smallest)
                idx = smallest
            else:
                break

    def _push_global(self, score, tid, team, key):
        """向全局堆插入一条新记录"""
        self.global_heap.append((score, tid, team, key))
        idx = len(self.global_heap) - 1
        self.pos[tid] = idx
        self._sift_up(idx)

    def _pop_global(self):
        """弹出全局堆顶（分数最小），返回 (score, tid, team, key) 或 None"""
        if not self.global_heap:
            return None
        self._swap(0, len(self.global_heap) - 1)
        item = self.global_heap.pop()
        del self.pos[item[1]]
        if self.global_heap:
            self._sift_down(0)
        return item

    def _update_global(self, tid: int, new_score, new_team, key):
        """
        根据 tid 原地更新全局堆中某条记录的分数和队伍，并调整堆。
        假设 key 不变（队伍内部更新），tid 仍有效。
        """
        idx = self.pos[tid]
        old_score = self.global_heap[idx][0]
        # 更新元素（tid, key 不变）
        self.global_heap[idx] = (new_score, tid, new_team, key)
        # 根据新旧分数大小决定调整方向
        if new_score < old_score:
            self._sift_up(idx)
        elif new_score > old_score:
            self._sift_down(idx)
        # 分数相等无需调整

    # ---------- 队伍内部堆操作 ----------
    def _team_remove_by_tid(self, key, tid):
        """在队伍堆中移除指定 tid 的记录（O(t)，t 很小）"""
        heap = self.teams[key]
        for i, (_, cur_tid, _) in enumerate(heap):
            if cur_tid == tid:
                heap[i] = heap[-1]
                heap.pop()
                if i < len(heap):
                    heapq.heapify(heap)  # 重建局部堆，O(t)
                return

    def add(self, team, score):
        team = tuple(team)
        key = frozenset(team[:10])
        team_heap = self.teams[key]

        if len(team_heap) == self.t:
            min_score, old_tid, old_team = team_heap[0]
            if score <= min_score:
                return
            self._update_global(old_tid, score, team, key)
            heapq.heappop(team_heap)
            heapq.heappush(team_heap, (score, old_tid, team))
            return

        # --- 情况2：队伍未满，需要检查全局容量 ---
        # 生成新 tid（全局插入时需要）
        tid = self._next_id()

        if len(self.global_heap) < self.k:
            # 全局未满，直接插入
            self._push_global(score, tid, team, key)
            heapq.heappush(team_heap, (score, tid, team))
        else:
            # 全局已满，只有高于全局最低分才插入
            if score <= self.global_heap[0][0]:
                return
            # 弹出全局最低分，并从其所属队伍中删除
            popped = self._pop_global()
            if popped is not None:
                _, old_tid, _, old_key = popped
                self._team_remove_by_tid(old_key, old_tid)
            # 插入新记录
            self._push_global(score, tid, team, key)
            heapq.heappush(team_heap, (score, tid, team))

    def get_top_k(self):
        """返回按 score 降序的 [(完整team, score), ...] 列表"""
        entries = list(self.global_heap)
        entries.sort(key=lambda x: x[0], reverse=True)
        return [(entry[2], entry[0]) for entry in entries]  # (full_team, score)
