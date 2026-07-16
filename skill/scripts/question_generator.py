#!/usr/bin/env python3
"""
question_generator.py — 关联问题生成模块

基于知识图谱的拓扑结构，生成需要综合运用多个知识点的复合问题。

AI核心价值：
  传统题库是静态的、孤立的——一个知识点一道题。
  AI理解知识图谱后，可以沿图的路径生成「跨节点综合题」，
  比如同时考察"导数→梯度→梯度下降→学习率"这条链上的所有概念。
"""

import logging
from typing import Optional

from utils import get_config, get_llm, load_json, save_json

logger = logging.getLogger("knowledge_graph.questions")

# ============================================================
# 提示词模板
# ============================================================
QUESTION_GEN_SYSTEM_PROMPT = """你是一个专业的教育测评专家。根据给定的知识图谱（包含节点和边），生成高质量的复习题目。

知识图谱中的"边"代表了知识点之间的关系（前置依赖、相关延伸、对立对比、包含关系）。
你需要沿着图谱的"路径"生成题目：

题目类型：
1. single（单一知识点题）：考察单个核心概念的理解
2. chain（知识链题）：考察一条路径上2-3个有前置关系的知识点，测试综合理解
3. compare（对比题）：考察两个有"对立对比"或"相关延伸"关系的知识点
4. apply（应用题）：将多个知识点应用于一个实际场景

对于每道题，请提供：
- type: 题目类型
- question: 题目描述
- concepts_involved: 涉及的知识点（在知识图谱中的节点名）
- path: 题目考察的概念路径（按逻辑顺序排列）
- difficulty: 题目难度（easy/medium/hard）
- answer_hint: 答题要点提示（给学生自检用，不是完整答案）
- explanation: 为什么这道题需要用到这些知识点

请严格按照以下JSON格式输出：
{
  "questions": [
    {
      "id": "q001",
      "type": "chain",
      "question": "题目的完整文字描述",
      "concepts_involved": ["概念A", "概念B"],
      "path": ["概念A → 概念B → 概念C"],
      "difficulty": "medium",
      "answer_hint": "答题要点...",
      "explanation": "这道题考察的知识链解释..."
    }
  ]
}"""


class QuestionGenerator:
    """
    关联问题生成器。

    基于知识图谱结构，沿路径生成多类型复习问题。
    支持按数量、难度、类型筛选。

    Attributes:
        llm: LLM客户端
    """

    QUESTION_TYPES = ["single", "chain", "compare", "apply"]

    def __init__(self):
        self.llm = get_llm()

    def generate(
        self,
        graph: dict,
        count: int = 5,
        difficulty: Optional[str] = None,
        question_types: Optional[list[str]] = None,
        graph_file: Optional[str] = None,
    ) -> dict:
        """
        基于知识图谱生成复习问题。

        Args:
            graph: 知识图谱字典（含nodes和edges）
            count: 生成题目数量
            difficulty: 筛选难度 (easy/medium/hard)，None表示不限
            question_types: 筛选题型列表，None表示全部类型
            graph_file: 可选，从JSON文件加载图谱

        Returns:
            包含questions和metadata的字典
        """
        if graph_file:
            graph = load_json(graph_file)

        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        if not nodes:
            raise ValueError("知识图谱中没有节点")

        logger.info(f"开始生成问题: {len(nodes)}个节点, {len(edges)}条边, 目标{count}道题")

        # 构建图谱的文本描述
        graph_description = self._describe_graph(nodes, edges)

        # 构建用户提示词
        user_prompt = f"""知识图谱结构：

{graph_description}

请基于以上知识图谱生成 {count} 道题目。
题目类型分布：single(30%), chain(30%), compare(20%), apply(20%)。
"""

        if difficulty:
            user_prompt += f"\n所有题目的难度应为: {difficulty}"
        if question_types:
            user_prompt += f"\n只生成以下类型的题目: {', '.join(question_types)}"

        # 调用LLM
        result = self.llm.chat_json(QUESTION_GEN_SYSTEM_PROMPT, user_prompt)

        questions = result.get("questions", [])

        # 确保ID唯一
        for i, q in enumerate(questions):
            if "id" not in q:
                q["id"] = f"q{i+1:03d}"

        logger.info(f"已生成 {len(questions)} 道题目")

        return {
            "questions": questions,
            "metadata": {
                "total": len(questions),
                "types": self._count_types(questions),
                "difficulties": self._count_difficulties(questions),
                "graph_nodes": len(nodes),
                "graph_edges": len(edges),
            },
        }

    def generate_practice_set(
        self,
        graph: dict,
        easy: int = 3,
        medium: int = 5,
        hard: int = 2,
    ) -> dict:
        """
        生成一套完整的练习卷（按难度比例混合）。

        Args:
            graph: 知识图谱
            easy: 简单题数量
            medium: 中等题数量
            hard: 困难题数量

        Returns:
            完整练习卷
        """
        all_questions = []
        difficulties = [("easy", easy), ("medium", medium), ("hard", hard)]

        for diff, cnt in difficulties:
            if cnt <= 0:
                continue
            result = self.generate(graph, count=cnt, difficulty=diff)
            all_questions.extend(result["questions"])

        return {
            "title": "综合练习卷",
            "description": f"本题集基于知识图谱自动生成，包含 {easy} 简单题 + {medium} 中等题 + {hard} 困难题",
            "questions": all_questions,
            "metadata": {
                "total": len(all_questions),
                "types": self._count_types(all_questions),
                "difficulties": self._count_difficulties(all_questions),
            },
        }

    def _describe_graph(self, nodes: list, edges: list) -> str:
        """将图谱转为LLM可读的文本描述"""
        lines = ["## 知识点列表"]
        for n in nodes:
            lines.append(f"- {n['id']}: {n['name']}（{n.get('category', '')}）")

        lines.append("\n## 知识点关系")
        for e in edges:
            lines.append(
                f"- {e['source_name']} --[{e['relation']}]--> {e['target_name']}（{e.get('explanation', '')}）"
            )

        return "\n".join(lines)

    def _count_types(self, questions: list) -> dict:
        counts = {}
        for q in questions:
            t = q.get("type", "unknown")
            counts[t] = counts.get(t, 0) + 1
        return counts

    def _count_difficulties(self, questions: list) -> dict:
        counts = {}
        for q in questions:
            d = q.get("difficulty", "unknown")
            counts[d] = counts.get(d, 0) + 1
        return counts


# ============================================================
# 命令行入口
# ============================================================
def main():
    import argparse

    parser = argparse.ArgumentParser(description="关联问题生成工具")
    parser.add_argument("--graph", "-g", required=True, help="知识图谱JSON文件路径")
    parser.add_argument("--output", "-o", default="questions.json", help="输出JSON文件路径")
    parser.add_argument("--count", "-n", type=int, default=10, help="生成题目数量")
    parser.add_argument("--difficulty", "-d", choices=["easy", "medium", "hard"], help="难度筛选")
    parser.add_argument("--type", "-t", choices=["single", "chain", "compare", "apply"], action="append", help="题型筛选")
    parser.add_argument("--config", help="配置文件路径")

    args = parser.parse_args()

    from utils import init

    init(args.config)

    generator = QuestionGenerator()
    result = generator.generate(
        graph_file=args.graph,
        count=args.count,
        difficulty=args.difficulty,
        question_types=args.type,
    )

    save_json(result, args.output)
    print(f"✅ 已生成 {result['metadata']['total']} 道题目，保存至 {args.output}")
    print(f"   题型分布: {result['metadata']['types']}")
    print(f"   难度分布: {result['metadata']['difficulties']}")


if __name__ == "__main__":
    main()
