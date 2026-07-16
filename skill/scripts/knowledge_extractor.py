#!/usr/bin/env python3
"""
knowledge_extractor.py — 知识点自动抽取模块

从非结构化文本中利用LLM识别核心概念、定义、定理、公式等知识点，
输出结构化的JSON格式数据。

AI核心价值：
  传统NLP方法需要大量标注数据训练实体识别模型，且只能识别预定义类别。
  大语言模型可以零样本理解任意领域的文本，识别概念并生成准确的定义。
"""

import json
import logging
from typing import Optional

from utils import chunk_text, get_config, get_llm, load_text, save_json

logger = logging.getLogger("knowledge_graph.extractor")

# ============================================================
# 提示词模板
# ============================================================
EXTRACTION_SYSTEM_PROMPT = """你是一个专业的知识点抽取专家。你的任务是从给定的学习材料中识别和提取所有核心知识点。

对于每个知识点，请提取以下信息：
1. name: 知识点的标准名称（简洁、准确）
2. definition: 知识点的清晰定义（1-3句话）
3. category: 所属分类（如：数学/微积分, 编程/Python, 机器学习/监督学习 等，使用层级结构）
4. difficulty: 难度等级（basic/intermediate/advanced）
5. keywords: 关联关键词列表（2-5个，用于后续关系推理）

要求：
- 不要遗漏任何一个重要概念
- 定义要准确且自包含
- 分类要统一且层级分明
- 只输出知识点，不要包含示例或练习题中的具体数值

请严格按照以下JSON格式输出，不要包含任何其他文字：
{
  "concepts": [
    {
      "name": "...",
      "definition": "...",
      "category": "...",
      "difficulty": "...",
      "keywords": ["...", "..."]
    }
  ],
  "summary": "本材料的整体主题概括"
}"""


# ============================================================
# 核心提取逻辑
# ============================================================
class KnowledgeExtractor:
    """
    知识点抽取器。

    支持单文件/多文件/文本字符串输入，自动处理大文本分块，
    对每块调用LLM抽取知识点，最后合并去重。

    Attributes:
        max_chunk_size: 每次LLM调用的最大文本量
        overlap_size: 分块之间的重叠大小
    """

    def __init__(self):
        config = get_config()
        self.max_chunk_size = config.get("extraction", "max_chunk_size", default=8000)
        self.overlap_size = config.get("extraction", "overlap_size", default=500)
        self.llm = get_llm()

    def extract_from_text(self, text: str, source_label: str = "unknown") -> dict:
        """
        从纯文本中抽取知识点。

        Args:
            text: 输入文本
            source_label: 来源标识

        Returns:
            包含concepts和summary的字典
        """
        logger.info(f"开始抽取知识点，文本长度: {len(text)} 字符，来源: {source_label}")

        all_concepts = []
        summaries = []

        chunks = chunk_text(text, self.max_chunk_size, self.overlap_size)
        logger.info(f"文本分为 {len(chunks)} 个块")

        for i, chunk in enumerate(chunks):
            logger.info(f"处理第 {i+1}/{len(chunks)} 块 ({len(chunk)} 字符)")
            user_prompt = f"来源: {source_label}\n\n学习材料内容：\n\n{chunk}\n\n请提取以上材料中的所有知识点。"

            result = self.llm.chat_json(EXTRACTION_SYSTEM_PROMPT, user_prompt)

            concepts = result.get("concepts", [])
            summary = result.get("summary", "")

            # 标记来源
            for c in concepts:
                c["source"] = source_label
                c["chunk_index"] = i

            all_concepts.extend(concepts)
            if summary:
                summaries.append(summary)

            logger.info(f"第 {i+1} 块抽取到 {len(concepts)} 个知识点")

        # 去重合并
        merged = self._deduplicate_concepts(all_concepts)
        logger.info(f"去重前: {len(all_concepts)} 个知识点, 去重后: {len(merged)} 个")

        result = {
            "concepts": merged,
            "summary": "；".join(summaries) if summaries else "",
            "metadata": {
                "total_chunks": len(chunks),
                "total_extracted": len(all_concepts),
                "after_dedup": len(merged),
                "source": source_label,
            },
        }
        return result

    def extract_from_file(self, file_path: str) -> dict:
        """从文件中抽取知识点"""
        text = load_text(file_path)
        source_label = file_path.split("/")[-1].split("\\")[-1]
        return self.extract_from_text(text, source_label)

    def extract_from_files(self, file_paths: list[str]) -> dict:
        """从多个文件中批量抽取，合并结果"""
        all_concepts = []
        all_summaries = []
        total_chunks = 0
        total_extracted = 0

        for fp in file_paths:
            result = self.extract_from_file(fp)
            all_concepts.extend(result["concepts"])
            all_summaries.append(result["summary"])
            total_chunks += result["metadata"]["total_chunks"]
            total_extracted += result["metadata"]["total_extracted"]

        merged = self._deduplicate_concepts(all_concepts)

        return {
            "concepts": merged,
            "summary": "；".join(filter(None, all_summaries)),
            "metadata": {
                "total_files": len(file_paths),
                "total_chunks": total_chunks,
                "total_extracted": total_extracted,
                "after_dedup": len(merged),
            },
        }

    def _deduplicate_concepts(self, concepts: list) -> list:
        """
        基于名称相似度去重。
        简单策略：完全相同的name视为重复，保留第一次出现。
        更复杂的语义去重在实际迭代中可通过LLM实现。
        """
        seen = set()
        result = []
        for c in concepts:
            name_lower = c.get("name", "").strip().lower()
            if name_lower and name_lower not in seen:
                seen.add(name_lower)
                result.append(c)
        return result


# ============================================================
# 命令行入口
# ============================================================
def main():
    """独立运行入口（用于测试）"""
    import argparse

    parser = argparse.ArgumentParser(description="知识点抽取工具")
    parser.add_argument("--input", "-i", required=True, help="输入文件路径")
    parser.add_argument("--output", "-o", default="concepts.json", help="输出JSON文件路径")
    parser.add_argument("--config", "-c", help="配置文件路径")

    args = parser.parse_args()

    from utils import init

    init(args.config)

    extractor = KnowledgeExtractor()
    result = extractor.extract_from_file(args.input)

    save_json(result, args.output)
    print(f"✅ 已抽取 {result['metadata']['after_dedup']} 个知识点，保存至 {args.output}")
    print(f"   主题概括: {result['summary']}")


if __name__ == "__main__":
    main()
