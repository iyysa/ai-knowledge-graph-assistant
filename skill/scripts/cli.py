#!/usr/bin/env python3
"""
cli.py — AI知识图谱学习助手 命令行统一入口

支持子命令:
  extract          从文本抽取知识点
  build-graph      构建知识图谱
  generate-questions  生成复习问题
  recommend-path   推荐学习路径
  full-pipeline    一键全流程执行

用法示例:
  python cli.py extract -i notes.txt -o concepts.json
  python cli.py full-pipeline --input data/notes/ --output data/output/
"""

import argparse
import logging
import sys
from pathlib import Path

# 将 scripts/ 目录加入路径，确保内部模块可导入
sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils import init, save_json, load_json

logger = logging.getLogger("knowledge_graph.cli")


def cmd_extract(args):
    """知识点抽取子命令"""
    from knowledge_extractor import KnowledgeExtractor

    init(args.config)
    extractor = KnowledgeExtractor()

    if Path(args.input).is_dir():
        # 目录模式：处理所有.md和.txt文件
        files = list(Path(args.input).glob("*.md")) + list(Path(args.input).glob("*.txt"))
        logger.info(f"发现 {len(files)} 个文件")
        result = extractor.extract_from_files([str(f) for f in files])
    else:
        result = extractor.extract_from_file(args.input)

    save_json(result, args.output)
    print(f"\n✅ 知识点抽取完成！")
    print(f"   抽取知识点: {result['metadata'].get('after_dedup', len(result['concepts']))} 个")
    print(f"   主题概括: {result.get('summary', 'N/A')[:100]}")
    print(f"   输出文件: {args.output}")


def cmd_build_graph(args):
    """知识图谱构建子命令"""
    from graph_builder import GraphBuilder

    init(args.config)
    builder = GraphBuilder()
    graph = builder.build([], concept_file=args.concepts)

    save_json(graph, args.output)
    print(f"\n✅ 知识图谱构建完成！")
    print(f"   节点: {graph['stats']['total_nodes']}, 边: {graph['stats']['total_edges']}")
    print(f"   关系分布: {graph['stats']['relation_distribution']}")

    if args.visualize:
        vis_path = args.output.replace(".json", ".png")
        builder.visualize(graph, vis_path)
        print(f"   可视化: {vis_path}")

    if args.mermaid:
        mermaid = builder.generate_mermaid(graph)
        print(f"\n--- Mermaid 代码 ---\n{mermaid}\n---")


def cmd_generate_questions(args):
    """问题生成子命令"""
    from question_generator import QuestionGenerator

    init(args.config)
    generator = QuestionGenerator()

    if args.practice_set:
        result = generator.generate_practice_set(
            graph_file=args.graph,
            easy=args.easy or 3,
            medium=args.medium or 5,
            hard=args.hard or 2,
        )
    else:
        result = generator.generate(
            graph_file=args.graph,
            count=args.count,
            difficulty=args.difficulty,
            question_types=args.type,
        )

    save_json(result, args.output)
    print(f"\n✅ 题目生成完成！")
    print(f"   题目总数: {result['metadata']['total']}")
    print(f"   题型分布: {result['metadata']['types']}")
    print(f"   难度分布: {result['metadata']['difficulties']}")


def cmd_recommend_path(args):
    """学习路径推荐子命令"""
    from learning_path import LearningPathRecommender

    init(args.config)
    recommender = LearningPathRecommender()
    result = recommender.recommend(
        graph_file=args.graph,
        mastered=args.mastered or [],
        target=args.target,
        max_steps=args.max_steps,
    )

    save_json(result, args.output)
    print(f"\n✅ 学习路径推荐完成！")
    print(f"   总步数: {result['overall_plan'].get('total_steps', len(result['learning_path']))}")
    print(f"   预计时间: {result['overall_plan'].get('total_estimated_time', 'N/A')}")
    print(f"\n推荐学习顺序:")
    for step in result.get("learning_path", []):
        print(f"   {step['step']:2d}. [{step.get('concept_name', '?')}] — {step.get('reason', '')[:60]}")


def cmd_full_pipeline(args):
    """一键全流程：抽取 → 图谱 → 题目 → 路径"""
    from knowledge_extractor import KnowledgeExtractor
    from graph_builder import GraphBuilder
    from question_generator import QuestionGenerator
    from learning_path import LearningPathRecommender

    init(args.config)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: 知识点抽取
    print("\n" + "=" * 60)
    print("  Step 1/4: 知识点抽取")
    print("=" * 60)

    extractor = KnowledgeExtractor()
    input_path = Path(args.input)

    if input_path.is_dir():
        files = list(input_path.glob("*.md")) + list(input_path.glob("*.txt"))
        concepts_result = extractor.extract_from_files([str(f) for f in files])
    else:
        concepts_result = extractor.extract_from_file(str(input_path))

    concepts_path = output_dir / "concepts.json"
    save_json(concepts_result, str(concepts_path))
    print(f"  ✅ 已抽取 {concepts_result['metadata'].get('after_dedup', len(concepts_result['concepts']))} 个知识点")

    # Step 2: 知识图谱
    print("\n" + "=" * 60)
    print("  Step 2/4: 知识图谱构建")
    print("=" * 60)

    builder = GraphBuilder()
    graph = builder.build(concepts_result["concepts"])
    graph_path = output_dir / "graph.json"
    save_json(graph, str(graph_path))
    print(f"  ✅ {graph['stats']['total_nodes']}节点, {graph['stats']['total_edges']}条边")

    if args.visualize:
        builder.visualize(graph, str(output_dir / "graph.png"))
        print(f"  ✅ 图谱可视化已保存")

    # Step 3: 题目生成
    print("\n" + "=" * 60)
    print("  Step 3/4: 复习题目生成")
    print("=" * 60)

    generator = QuestionGenerator()
    questions = generator.generate(graph, count=args.question_count)
    questions_path = output_dir / "questions.json"
    save_json(questions, str(questions_path))
    print(f"  ✅ 已生成 {questions['metadata']['total']} 道题目")

    # Step 4: 学习路径
    print("\n" + "=" * 60)
    print("  Step 4/4: 学习路径推荐")
    print("=" * 60)

    recommender = LearningPathRecommender()
    path = recommender.recommend(graph, mastered=args.mastered or [], max_steps=args.max_steps)
    path_path = output_dir / "learning_path.json"
    save_json(path, str(path_path))
    print(f"  ✅ 已推荐 {len(path.get('learning_path', []))} 步学习路径")

    # 总结
    print("\n" + "=" * 60)
    print("  🎉 全流程完成！")
    print("=" * 60)
    print(f"  输出目录: {output_dir}")
    print(f"  ├── concepts.json        ({concepts_result['metadata'].get('after_dedup', 0)} 个知识点)")
    print(f"  ├── graph.json           ({graph['stats']['total_nodes']}节点, {graph['stats']['total_edges']}边)")
    print(f"  ├── questions.json       ({questions['metadata']['total']} 道题)")
    print(f"  └── learning_path.json   ({len(path.get('learning_path', []))} 步路径)")


def main():
    parser = argparse.ArgumentParser(
        description="AI知识图谱学习助手 — 命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 抽取知识点
  python cli.py extract -i notes.md -o concepts.json

  # 构建知识图谱
  python cli.py build-graph -c concepts.json -o graph.json -v

  # 生成题目
  python cli.py generate-questions -g graph.json -n 10 -o questions.json

  # 推荐路径
  python cli.py recommend-path -g graph.json -m "变量" "循环" -o path.json

  # 一键全流程
  python cli.py full-pipeline -i data/notes/ -o data/output/ -v
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="可用子命令")

    # extract
    p_extract = subparsers.add_parser("extract", help="从文本中抽取知识点")
    p_extract.add_argument("--input", "-i", required=True, help="输入文件/目录路径")
    p_extract.add_argument("--output", "-o", default="concepts.json", help="输出JSON文件")
    p_extract.add_argument("--config", "-c", help="配置文件路径")

    # build-graph
    p_graph = subparsers.add_parser("build-graph", help="构建知识图谱")
    p_graph.add_argument("--concepts", "-c", required=True, help="知识点JSON文件")
    p_graph.add_argument("--output", "-o", default="graph.json", help="输出JSON文件")
    p_graph.add_argument("--visualize", "-v", action="store_true", help="生成可视化图片")
    p_graph.add_argument("--mermaid", "-m", action="store_true", help="输出Mermaid代码")
    p_graph.add_argument("--config", help="配置文件路径")

    # generate-questions
    p_q = subparsers.add_parser("generate-questions", help="生成复习问题")
    p_q.add_argument("--graph", "-g", required=True, help="知识图谱JSON文件")
    p_q.add_argument("--output", "-o", default="questions.json", help="输出JSON文件")
    p_q.add_argument("--count", "-n", type=int, default=10, help="生成题目数量")
    p_q.add_argument("--difficulty", "-d", choices=["easy", "medium", "hard"])
    p_q.add_argument("--type", "-t", choices=["single", "chain", "compare", "apply"], action="append")
    p_q.add_argument("--practice-set", action="store_true", help="生成完整练习卷")
    p_q.add_argument("--easy", type=int, default=3)
    p_q.add_argument("--medium", type=int, default=5)
    p_q.add_argument("--hard", type=int, default=2)
    p_q.add_argument("--config", help="配置文件路径")

    # recommend-path
    p_path = subparsers.add_parser("recommend-path", help="推荐学习路径")
    p_path.add_argument("--graph", "-g", required=True, help="知识图谱JSON文件")
    p_path.add_argument("--mastered", "-m", nargs="*", default=[], help="已掌握知识点")
    p_path.add_argument("--target", "-t", help="目标知识点")
    p_path.add_argument("--output", "-o", default="learning_path.json", help="输出JSON文件")
    p_path.add_argument("--max-steps", type=int, default=20)
    p_path.add_argument("--config", help="配置文件路径")

    # full-pipeline
    p_full = subparsers.add_parser("full-pipeline", help="一键全流程执行")
    p_full.add_argument("--input", "-i", required=True, help="输入文件/目录")
    p_full.add_argument("--output", "-o", default="data/output/", help="输出目录")
    p_full.add_argument("--visualize", "-v", action="store_true", help="生成可视化")
    p_full.add_argument("--question-count", type=int, default=10, help="生成题目数量")
    p_full.add_argument("--mastered", "-m", nargs="*", default=[], help="已掌握知识点")
    p_full.add_argument("--max-steps", type=int, default=20)
    p_full.add_argument("--config", "-c", help="配置文件路径")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    command_map = {
        "extract": cmd_extract,
        "build-graph": cmd_build_graph,
        "generate-questions": cmd_generate_questions,
        "recommend-path": cmd_recommend_path,
        "full-pipeline": cmd_full_pipeline,
    }

    command_map[args.command](args)


if __name__ == "__main__":
    main()
