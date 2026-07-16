#!/usr/bin/env python3
"""
learning_path.py — 个性化学习路径推荐模块

基于知识图谱拓扑结构和用户掌握状态，智能推荐最优学习顺序。

工作流程：
1. 根据图中的prerequisite边建立有向依赖关系
2. 用户标记已掌握的知识点
3. 计算可学习的候选节点（所有前置依赖已满足的未掌握节点）
4. LLM根据知识点重要性、难度曲线进一步排序推荐

AI核心价值：
  纯拓扑排序只输出一种顺序，无法考虑"先学重要的"、"难度循序渐进"、
  "相关知识一起学效率高"等人类学习策略。LLM可以综合这些因素给出
  更符合人类学习习惯的路径。
"""

import logging
from typing import Optional

from utils import get_llm, load_json, save_json

logger = logging.getLogger("knowledge_graph.path")

# ============================================================
# 提示词模板
# ============================================================
PATH_RECOMMEND_SYSTEM_PROMPT = """你是一个个性化学习规划专家。根据知识图谱和用户已掌握的知识点，推荐最优学习路径。

推荐原则：
1. 前置依赖必须满足（没学依赖之前不能学后继）
2. 难度循序渐进（不要连续推荐高难度知识点）
3. 相关知识集中学习（有"相关延伸"关系的知识一起学效率高）
4. 优先推荐「枢纽节点」（连接多个知识点的重要概念）
5. 给出每个推荐知识点的学习建议和预计学习时间

请严格按照以下JSON格式输出：
{
  "learning_path": [
    {
      "step": 1,
      "concept_name": "知识点名称",
      "reason": "为什么现在学这个（基于知识图谱的推理）",
      "estimated_time": "预计学习时间（如 30min, 1h）",
      "study_tips": "学习建议",
      "prerequisites_satisfied": ["已满足的前置知识点"],
      "leads_to": ["学完后可以接着学的知识点"]
    }
  ],
  "overall_plan": {
    "total_steps": 总步数,
    "total_estimated_time": "总预计学习时间",
    "strategy": "路径规划策略说明"
  }
}"""


class LearningPathRecommender:
    """
    学习路径推荐器。

    结合图谱拓扑排序和LLM的语义理解，生成个性化学习路径。

    Attributes:
        llm: LLM客户端
    """

    def __init__(self):
        self.llm = get_llm()

    def recommend(
        self,
        graph: dict,
        mastered: list[str],
        target: Optional[str] = None,
        max_steps: int = 20,
        graph_file: Optional[str] = None,
    ) -> dict:
        """
        推荐个性化学习路径。

        Args:
            graph: 知识图谱字典
            mastered: 用户已掌握的知识点名称列表
            target: 可选，目标知识点（只推荐到达target的路径）
            max_steps: 最大推荐步数
            graph_file: 可选，从JSON文件加载图谱

        Returns:
            包含learning_path和overall_plan的字典
        """
        if graph_file:
            graph = load_json(graph_file)

        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        if not nodes:
            raise ValueError("知识图谱中没有节点")

        # 规范化已掌握列表
        mastered_set = set(m.lower().strip() for m in mastered)

        # 1. 拓扑筛选：找出所有前置依赖已满足的候选节点
        candidates = self._get_candidates(nodes, edges, mastered_set, target)

        logger.info(
            f"已掌握: {len(mastered_set)}个, 候选学习节点: {len(candidates)}个"
        )

        if not candidates:
            return {
                "learning_path": [],
                "overall_plan": {
                    "total_steps": 0,
                    "total_estimated_time": "0",
                    "strategy": "所有知识点已掌握，或无可达目标节点的路径",
                },
            }

        # 2. 构建LLM上下文
        graph_text = self._build_context(nodes, edges, mastered_set, candidates, target)

        # 3. LLM推荐
        user_prompt = f"""知识图谱上下文：

{graph_text}

已掌握的知识点: {', '.join(mastered) if mastered else '无'}

{'目标知识点: ' + target if target else '请推荐完整的学习路径'}

请推荐最优学习顺序（最多{max_steps}步）。"""

        result = self.llm.chat_json(PATH_RECOMMEND_SYSTEM_PROMPT, user_prompt)

        learning_path = result.get("learning_path", [])[:max_steps]
        overall = result.get("overall_plan", {})

        # 确保step正确编号
        for i, step in enumerate(learning_path):
            step["step"] = i + 1

        logger.info(f"学习路径已生成: {len(learning_path)}步")

        return {
            "learning_path": learning_path,
            "overall_plan": overall,
        }

    def _get_candidates(
        self,
        nodes: list,
        edges: list,
        mastered: set,
        target: Optional[str] = None,
    ) -> list:
        """筛选可学习的候选节点（所有前置依赖已满足的未掌握节点）"""
        # 构建依赖图
        prerequisites = {}  # node_id -> [前置node_ids]
        node_names = {}  # node_id -> name
        name_to_id = {}  # name -> node_id

        for n in nodes:
            prerequisites.setdefault(n["id"], [])
            node_names[n["id"]] = n["name"]
            name_to_id[n["name"].lower().strip()] = n["id"]

        for e in edges:
            if e.get("relation") == "prerequisite":
                prerequisites.setdefault(e["target"], []).append(e["source"])

        # 找到所有前置依赖已满足的未掌握节点
        candidates = []
        for node in nodes:
            node_name = node["name"].lower().strip()
            if node_name in mastered:
                continue
            prereqs = prerequisites.get(node["id"], [])
            all_satisfied = all(
                node_names.get(p, "").lower().strip() in mastered for p in prereqs
            )
            if all_satisfied:
                candidates.append(node)

        # 如果指定了目标，做BFS过滤（只保留能到达target路径上的节点）
        if target and candidates:
            target_id = name_to_id.get(target.lower().strip())
            if target_id:
                # 构建正向图
                forward = {n["id"]: [] for n in nodes}
                for e in edges:
                    forward.setdefault(e["source"], []).append(e["target"])

                reachable = self._bfs_reachable(forward, target_id)
                candidates = [c for c in candidates if c["id"] in reachable]

        return candidates

    def _bfs_reachable(self, graph: dict, target: str) -> set:
        """BFS找出所有能到达target的节点"""
        # 反转图
        reverse = {}
        for src, tgts in graph.items():
            for t in tgts:
                reverse.setdefault(t, []).append(src)

        visited = set()
        queue = [target]
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            for pred in reverse.get(node, []):
                if pred not in visited:
                    queue.append(pred)
        return visited

    def _build_context(
        self,
        nodes: list,
        edges: list,
        mastered: set,
        candidates: list,
        target: Optional[str] = None,
    ) -> str:
        """构建给LLM的上下文文本"""
        candidate_ids = {c["id"] for c in candidates}

        lines = ["## 知识点列表"]
        for n in nodes:
            status = "✅已掌握" if n["name"].lower().strip() in mastered else "🟢可学" if n["id"] in candidate_ids else "🔒未解锁"
            lines.append(f"- [{status}] {n['id']}: {n['name']}（{n.get('difficulty', '?')}, {n.get('category', '')}）")

        lines.append("\n## 前置依赖关系")
        for e in edges:
            if e.get("relation") == "prerequisite":
                lines.append(f"- {e['source_name']} → {e['target_name']}")

        lines.append("\n## 其他关系")
        for e in edges:
            if e.get("relation") != "prerequisite":
                lines.append(f"- {e['source_name']} --[{e['relation']}]--> {e['target_name']}")

        if target:
            lines.append(f"\n## 目标\n用户想要学习: {target}")

        return "\n".join(lines)


# ============================================================
# 命令行入口
# ============================================================
def main():
    import argparse

    parser = argparse.ArgumentParser(description="学习路径推荐工具")
    parser.add_argument("--graph", "-g", required=True, help="知识图谱JSON文件路径")
    parser.add_argument("--mastered", "-m", nargs="*", default=[], help="已掌握的知识点名称列表")
    parser.add_argument("--target", "-t", help="目标知识点")
    parser.add_argument("--output", "-o", default="learning_path.json", help="输出JSON文件路径")
    parser.add_argument("--max-steps", type=int, default=20, help="最大推荐步数")
    parser.add_argument("--config", help="配置文件路径")

    args = parser.parse_args()

    from utils import init

    init(args.config)

    recommender = LearningPathRecommender()
    result = recommender.recommend(
        graph_file=args.graph,
        mastered=args.mastered,
        target=args.target,
        max_steps=args.max_steps,
    )

    save_json(result, args.output)
    print(f"✅ 学习路径已生成，共 {result['overall_plan'].get('total_steps', 0)} 步")
    for step in result.get("learning_path", []):
        print(f"   {step['step']}. {step.get('concept_name', '?')} — {step.get('reason', '')[:50]}...")


if __name__ == "__main__":
    main()
