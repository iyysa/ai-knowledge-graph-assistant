#!/usr/bin/env python3
"""
graph_builder.py — 知识图谱构建模块

将已抽取的知识点列表构建为有向知识图谱，利用LLM自动推理节点间的关系类型。

关系类型：
  - 前置依赖（prerequisite）: B的学习需要先理解A
  - 相关延伸（related）: A和B属于同一主题的不同方面
  - 对立对比（contrast）: A和B是不同的方法/观点，需要对比理解
  - 包含关系（contains）: A是B的子概念

AI核心价值：
  传统方案只能基于关键词共现或规则匹配猜关系，准确率低。
  LLM可以理解概念的深层语义，判断真实的逻辑关系。
"""

import json
import logging
from typing import Optional

from utils import get_config, get_llm, load_json, save_json

logger = logging.getLogger("knowledge_graph.builder")

# ============================================================
# 提示词模板
# ============================================================
GRAPH_BUILD_SYSTEM_PROMPT = """你是一个知识图谱构建专家。给定一组知识点，你需要分析它们之间的逻辑关系。

对于每对有关系的知识点，确定以下关系类型：
- prerequisite（前置依赖）: 理解B必须先理解A → 箭头从A指向B
- related（相关延伸）: A和B属于同一主题的不同方面
- contrast（对立对比）: A和B是不同的方法/观点/概念，需要对比学习
- contains（包含关系）: A是B的子概念或组成部分

关系建立原则：
1. 优先建立prerequisite关系，这是学习路径的基础
2. 不要为所有知识点对都建立关系，只建立有意义的关系
3. 每个关系需要简短的解释
4. 如果一个知识点没有与其他知识点的明确关系，就不要强行关联

请严格按照以下JSON格式输出：
{
  "edges": [
    {
      "source": "知识点A的name",
      "target": "知识点B的name",
      "relation": "prerequisite|related|contrast|contains",
      "explanation": "简短解释为什么存在这个关系"
    }
  ],
  "graph_stats": {
    "total_nodes": 节点总数,
    "connected_nodes": 至少有一条边的节点数,
    "isolated_nodes": 没有任何边的节点数
  }
}"""

# ============================================================
# 可视化提示词
# ============================================================
GRAPH_VISUALIZATION_PROMPT = """你是一个图表生成专家。根据给定的知识图谱数据（节点和边），生成一个Mermaid格式的图表代码。

要求：
1. 使用 flowchart TD（自上而下的流程图）
2. 节点用方括号[]包裹名称
3. 不同类型的边用不同标签：前置依赖用 -->|前置|, 相关延伸用 -->|相关|, 对立对比用 -->|对比|, 包含关系用 -->|包含|
4. 为不同分类的节点使用不同的样式类
5. 图表应该清晰展示知识之间的层次关系

请只输出Mermaid代码，放在```mermaid代码块中。"""


class GraphBuilder:
    """
    知识图谱构建器。

    接收知识点列表，调用LLM分析关系，生成有向图的节点和边。
    支持导出为标准JSON格式和图可视化（Mermaid/NetworkX+Matplotlib）。

    Attributes:
        max_nodes: 单次LLM调用处理的最大节点数
    """

    RELATION_TYPES = {
        "prerequisite": "前置依赖",
        "related": "相关延伸",
        "contrast": "对立对比",
        "contains": "包含关系",
    }

    def __init__(self):
        config = get_config()
        self.max_nodes = config.get("graph", "max_nodes_per_graph", default=200)
        self.llm = get_llm()

    def build(self, concepts: list, concept_file: Optional[str] = None) -> dict:
        """
        构建知识图谱。

        Args:
            concepts: 知识点列表（dict列表，每个包含name等字段）
            concept_file: 可选，从JSON文件加载知识点

        Returns:
            包含nodes, edges, stats的图谱字典
        """
        if concept_file:
            data = load_json(concept_file)
            concepts = data.get("concepts", data if isinstance(data, list) else [])

        if not concepts:
            raise ValueError("没有可用的知识点")

        logger.info(f"开始构建知识图谱，共 {len(concepts)} 个知识点")

        # 构建节点列表
        nodes = []
        for i, c in enumerate(concepts):
            node_id = f"c{i:03d}"
            nodes.append({
                "id": node_id,
                "name": c.get("name", f"概念{i}"),
                "category": c.get("category", "未分类"),
                "difficulty": c.get("difficulty", "basic"),
                "definition": c.get("definition", ""),
            })

        # 创建名称到ID的映射
        name_to_id = {n["name"]: n["id"] for n in nodes}

        # 调用LLM分析关系
        concept_names = [n["name"] for n in nodes]
        concepts_text = "\n".join(
            f"{i+1}. {n['name']}（{n.get('definition', '')[:80]}...）"
            for i, n in enumerate(nodes)
        )

        logger.info("正在调用LLM分析知识点关系...")
        result = self.llm.chat_json(
            GRAPH_BUILD_SYSTEM_PROMPT,
            f"以下是要建立关系的知识点列表（共{len(nodes)}个）：\n\n{concepts_text}\n\n请分析这些知识点之间的关系。",
        )

        # 将名称映射回ID
        raw_edges = result.get("edges", [])
        edges = []
        for edge in raw_edges:
            source_id = name_to_id.get(edge["source"])
            target_id = name_to_id.get(edge["target"])
            if source_id and target_id and source_id != target_id:
                edges.append({
                    "source": source_id,
                    "target": target_id,
                    "source_name": edge["source"],
                    "target_name": edge["target"],
                    "relation": edge.get("relation", "related"),
                    "explanation": edge.get("explanation", ""),
                })

        # 统计
        connected = set()
        for e in edges:
            connected.add(e["source"])
            connected.add(e["target"])
        isolated = [n for n in nodes if n["id"] not in connected]

        graph_stats = {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "connected_nodes": len(connected),
            "isolated_nodes": len(isolated),
            "relation_distribution": self._count_relations(edges),
        }

        logger.info(f"图谱构建完成: {len(nodes)}节点, {len(edges)}条边, {len(isolated)}个孤立节点")

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": graph_stats,
        }

    def generate_mermaid(self, graph: dict) -> str:
        """
        将知识图谱转换为Mermaid格式。

        Args:
            graph: build()返回的图谱字典

        Returns:
            Mermaid flowchart代码
        """
        lines = ["flowchart TD"]

        # 节点定义
        for node in graph["nodes"]:
            node_id = node["id"]
            node_name = node["name"].replace('"', "'")
            lines.append(f'    {node_id}["{node_name}"]')

        # 边定义
        relation_labels = {
            "prerequisite": "前置",
            "related": "相关",
            "contrast": "对比",
            "contains": "包含",
        }

        for edge in graph["edges"]:
            src = edge["source"]
            tgt = edge["target"]
            rel = relation_labels.get(edge["relation"], "关联")
            lines.append(f"    {src} -->|{rel}| {tgt}")

        return "\n".join(lines)

    def visualize(self, graph: dict, output_path: str = "knowledge_graph.png"):
        """
        使用matplotlib和networkx可视化知识图谱。

        Args:
            graph: build()返回的图谱字典
            output_path: 输出图片路径
        """
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import networkx as nx

            G = nx.DiGraph()

            # 添加节点
            for node in graph["nodes"]:
                G.add_node(node["id"], label=node["name"], category=node.get("category", ""))

            # 添加边
            color_map = {
                "prerequisite": "#FF6B6B",
                "related": "#4ECDC4",
                "contrast": "#45B7D1",
                "contains": "#96CEB4",
            }

            for edge in graph["edges"]:
                color = color_map.get(edge["relation"], "#888888")
                G.add_edge(edge["source"], edge["target"], relation=edge["relation"], color=color)

            if len(G.nodes) == 0:
                logger.warning("图谱为空，无法可视化")
                return

            # 布局
            plt.figure(figsize=(16, 12))

            # 使用分层布局
            try:
                pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
            except Exception:
                pos = nx.circular_layout(G)

            # 绘制边
            edge_colors = [G[u][v].get("color", "#888") for u, v in G.edges()]
            nx.draw_networkx_edges(G, pos, edge_color=edge_colors, arrows=True, arrowsize=20, alpha=0.6)

            # 绘制节点
            node_colors = []
            categories = set(nx.get_node_attributes(G, "category").values())
            cat_colors = plt.cm.Set3([i / max(len(categories), 1) for i in range(len(categories))])
            cat_to_color = dict(zip(categories, cat_colors))

            for node in G.nodes():
                cat = G.nodes[node].get("category", "")
                node_colors.append(cat_to_color.get(cat, "#CCCCCC"))

            nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=800, alpha=0.9)

            # 标签
            labels = {n: G.nodes[n].get("label", n)[:12] for n in G.nodes()}
            nx.draw_networkx_labels(G, pos, labels, font_size=7, font_family="sans-serif")

            # 图例
            legend_elements = [
                plt.Line2D([0], [0], color=color_map["prerequisite"], lw=2, label="前置依赖"),
                plt.Line2D([0], [0], color=color_map["related"], lw=2, label="相关延伸"),
                plt.Line2D([0], [0], color=color_map["contrast"], lw=2, label="对立对比"),
                plt.Line2D([0], [0], color=color_map["contains"], lw=2, label="包含关系"),
            ]
            plt.legend(handles=legend_elements, loc="upper right")

            plt.title(f"知识图谱可视化 ({graph['stats']['total_nodes']}节点, {graph['stats']['total_edges']}边)")
            plt.axis("off")
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches="tight")
            plt.close()

            logger.info(f"知识图谱已保存至: {output_path}")
        except ImportError as e:
            logger.warning(f"可视化需要 matplotlib 和 networkx: {e}")

    def _count_relations(self, edges: list) -> dict:
        counts = {}
        for e in edges:
            rel = e.get("relation", "unknown")
            counts[rel] = counts.get(rel, 0) + 1
        return counts


# ============================================================
# 命令行入口
# ============================================================
def main():
    import argparse

    parser = argparse.ArgumentParser(description="知识图谱构建工具")
    parser.add_argument("--concepts", "-c", required=True, help="知识点JSON文件路径")
    parser.add_argument("--output", "-o", default="knowledge_graph.json", help="输出JSON文件路径")
    parser.add_argument("--visualize", "-v", action="store_true", help="生成可视化图片")
    parser.add_argument("--mermaid", "-m", action="store_true", help="输出Mermaid代码")
    parser.add_argument("--config", help="配置文件路径")

    args = parser.parse_args()

    from utils import init

    init(args.config)

    builder = GraphBuilder()
    graph = builder.build([], concept_file=args.concepts)

    save_json(graph, args.output)
    print(f"✅ 知识图谱已保存至 {args.output}")
    print(f"   节点: {graph['stats']['total_nodes']}, 边: {graph['stats']['total_edges']}")
    print(f"   关系分布: {graph['stats']['relation_distribution']}")

    if args.visualize:
        builder.visualize(graph, args.output.replace(".json", ".png"))

    if args.mermaid:
        mermaid_code = builder.generate_mermaid(graph)
        print("\n=== Mermaid 代码 ===\n")
        print(mermaid_code)


if __name__ == "__main__":
    main()
