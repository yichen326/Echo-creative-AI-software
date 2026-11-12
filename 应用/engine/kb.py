# -*- coding: utf-8 -*-
"""知识库加载与索引。"""
import json
import os

from .graph import Graph

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


class KnowledgeBase:
    def __init__(self, path=None):
        path = path or os.path.join(DATA_DIR, "curriculum.json")
        raw = json.load(open(path, encoding="utf-8"))
        self.meta = raw.get("meta", {})
        self.raw_nodes = raw["nodes"]
        self.nodes = {n["id"]: n for n in raw["nodes"]}
        self.edges = raw["edges"]
        self.graph = Graph(raw["nodes"], raw["edges"])
        self.assertions = raw["assertions"]
        self.assertions_by_id = {}
        for nid, arr in self.assertions.items():
            for a in arr:
                a["node"] = nid
                self.assertions_by_id[a["id"]] = a
        self.misconceptions = raw["misconceptions"]
        self.mis_by_id = {m["id"]: m for m in self.misconceptions}
        self.mis_by_node = {}
        for m in self.misconceptions:
            self.mis_by_node.setdefault(m["node"], []).append(m)
        self.probes = raw["probes"]
        self.glossary = raw.get("glossary", [])
        self.probes_by_node = {}
        for p in self.probes:
            self.probes_by_node.setdefault(p["node"], []).append(p)
        self.probes_by_assertion = {}
        for p in self.probes:
            for a in p["binds"]:
                self.probes_by_assertion.setdefault(a, []).append(p)

    def node_name(self, nid):
        return self.nodes.get(nid, {}).get("name", nid)

    def node_order(self):
        """按拓扑序返回节点 id，供界面呈现。"""
        return self.graph.topo_order()

    def assertions_of(self, nid):
        return self.assertions.get(nid, [])

    def total_weight(self, nid):
        return sum(a["w"] for a in self.assertions_of(nid)) or 1.0
