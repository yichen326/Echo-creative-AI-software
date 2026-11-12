# -*- coding: utf-8 -*-
"""知识图谱：前驱闭包、路径枚举、拓扑序。

图很小（12 节点），全部用纯 Python 实现，不依赖 networkx。
"""


class Graph:
    def __init__(self, nodes, edges):
        self.nodes = {n["id"]: n for n in nodes}
        self.edges = edges
        self.out = {nid: [] for nid in self.nodes}
        self.inn = {nid: [] for nid in self.nodes}
        for e in edges:
            self.out[e["from"]].append((e["to"], e["w"]))
            self.inn[e["to"]].append((e["from"], e["w"]))

    def name(self, nid):
        return self.nodes.get(nid, {}).get("name", nid)

    def prereqs(self, nid):
        """直接前驱。"""
        return [u for u, _ in self.inn[nid]]

    def successors(self, nid):
        return [v for v, _ in self.out[nid]]

    def ancestors(self, nid, max_depth=4):
        """前驱闭包（不含自身），广度优先，带深度。"""
        seen, frontier = {}, [(u, 1) for u, _ in self.inn[nid]]
        for u, d in frontier:
            seen[u] = min(seen.get(u, 99), d)
        depth = 1
        while frontier and depth < max_depth:
            nxt = []
            for u, d in frontier:
                if d != depth:
                    continue
                for p, _ in self.inn[u]:
                    nd = d + 1
                    if nd <= max_depth and seen.get(p, 99) > nd:
                        seen[p] = nd
                        nxt.append((p, nd))
            frontier = nxt
            depth += 1
        return seen

    def paths(self, src, dst, max_len=5):
        """枚举 src 到 dst 的全部简单路径，返回 [(节点序列, 权重连乘)]。"""
        if src == dst:
            return []
        results = []

        def dfs(u, path, wprod):
            if len(path) > max_len:
                return
            if u == dst:
                results.append((list(path), wprod))
                return
            for v, w in self.out[u]:
                if v in path:
                    continue
                path.append(v)
                dfs(v, path, wprod * w)
                path.pop()

        dfs(src, [src], 1.0)
        return results

    def topo_order(self):
        indeg = {n: len(self.inn[n]) for n in self.nodes}
        queue = [n for n, d in indeg.items() if d == 0]
        order = []
        while queue:
            u = queue.pop(0)
            order.append(u)
            for v, _ in self.out[u]:
                indeg[v] -= 1
                if indeg[v] == 0:
                    queue.append(v)
        return order

    def is_ancestor(self, u, v):
        """u 是否为 v 的祖先（含直接前驱）。"""
        return u in self.ancestors(v, max_depth=99)
