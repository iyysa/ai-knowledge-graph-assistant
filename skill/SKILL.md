---
name: "AI知识图谱学习助手"
version: "1.0.0"
description: >
  从非结构化学习材料（笔记、教材、文章）中自动抽取知识点，构建跨学科知识图谱，
  生成关联复习问题，推荐个性化学习路径。核心能力依赖AI大模型实现语义理解和关系推理，
  是传统编程手段无法独立完成的功能。
author: "大数据专业学生"
tags: ["学习", "知识图谱", "AI", "NLP", "教育"]
category: "学习学业"
llm_required: true
llm_provider: "openai-compatible"
llm_model: "deepseek-chat"
trigger_keywords:
  - "知识图谱"
  - "知识抽取"
  - "学习路径"
  - "生成考题"
  - "知识点串联"
  - "复习规划"
  - "概念图"
  - "思维导图"
dependencies:
  python: ">=3.10"
  packages:
    - "openai>=1.0"
    - "networkx>=3.0"
    - "pyyaml>=6.0"
    - "matplotlib>=3.7"
    - "rich>=13.0"
---

# AI知识图谱学习助手

## 一、概述

AI知识图谱学习助手是一个基于大语言模型的智能学习工具，核心能力包括：

1. **知识点自动抽取** — 输入任意非结构化文本（笔记、教材、论文），AI自动识别核心概念、定义、定理
2. **知识图谱构建** — 将孤立的零散概念串联成有向知识图谱，标注「前置依赖」「相关延伸」「对立对比」等关系
3. **关联问题生成** — 基于知识图谱结构，自动生成跨章节、跨学科的综合性问题
4. **个性化学习路径** — 根据用户已掌握和未掌握的知识点，动态推荐最优学习顺序

### 为什么必须有AI

| 传统做法 | AI做法 |
|---------|--------|
| 手动整理概念，耗时且容易遗漏 | 大模型秒级理解全文语义，识别关键概念 |
| 概念间关系靠人脑记忆，无法形成结构 | LLM推理概念间的因果/包含/对比关系 |
| 出题需要教师手动设计 | AI理解知识图谱拓扑结构后自动生成问题 |
| 学习路径千人一面 | 基于个人知识缺口动态规划 |

## 二、触发条件

当用户发出以下任一请求时，自动激活本Skill：

- "帮我从这些笔记中提取知识点"
- "建立这节课的知识图谱"
- "根据我学过的内容出几道题"
- "帮我规划一下机器学习的学习路径"
- "我想看看数据结构各章之间有什么联系"
- "把这些概念串联成一张图"

## 三、目录结构

```
skill/
├── SKILL.md                     # 本文件
├── scripts/                     # 核心脚本
│   ├── cli.py                   # 命令行统一入口
│   ├── knowledge_extractor.py   # 知识点抽取模块
│   ├── graph_builder.py         # 知识图谱构建模块
│   ├── question_generator.py    # 问题生成模块
│   ├── learning_path.py         # 学习路径推荐模块
│   └── utils.py                 # 工具函数（API调用、配置加载等）
└── references/                  # 参考配置与使用指南
    ├── api_config.yaml          # API配置模板
    ├── best_practices.md        # 最佳实践
    └── example_usage.md         # 详细使用示例
```

## 四、使用方式

### 4.1 环境准备

```bash
pip install openai networkx pyyaml matplotlib rich
```

### 4.2 配置API

复制 `references/api_config.yaml` 到项目根目录，填写你的API密钥：

```yaml
llm:
  provider: "openai-compatible"
  api_key: "your-api-key-here"
  base_url: "https://api.deepseek.com/v1"
  model: "deepseek-chat"
  temperature: 0.3
```

### 4.3 命令行使用

```bash
# 1. 从文本文件提取知识点
python scripts/cli.py extract --input data/notes/sample.md --output data/concepts.json

# 2. 构建知识图谱（需先完成知识点提取）
python scripts/cli.py build-graph --concepts data/concepts.json --output data/graph.json

# 3. 生成复习问题
python scripts/cli.py generate-questions --graph data/graph.json --count 10 --output data/questions.json

# 4. 推荐学习路径
python scripts/cli.py recommend-path --graph data/graph.json --mastered "变量,循环" --output data/path.json

# 5. 一键全流程
python scripts/cli.py full-pipeline --input data/notes/ --output data/output/
```

## 五、核心模块说明

### 5.1 knowledge_extractor.py — 知识点抽取

输入原始文本 → LLM分析 → 输出结构化知识点的JSON列表。

**AI核心价值**：语义级别的概念识别，理解上下文中的同义词、缩写、隐含定义。

### 5.2 graph_builder.py — 知识图谱构建

输入知识点列表 → LLM推理关系 → 输出有向图的节点和边。

**AI核心价值**：自动判断概念间是"前置依赖"还是"并列相关"还是"对立对比"，这是传统规则匹配做不到的。

### 5.3 question_generator.py — 问题生成

输入知识图谱 → LLM理解拓扑结构 → 生成跨节点、综合性的问题。

**AI核心价值**：不只是孤立地为一个知识点出题，而是理解多条概念路径后生成需要综合运用多个知识点的复合题。

### 5.4 learning_path.py — 学习路径推荐

输入知识图谱 + 用户掌握状态 → 拓扑排序 + LLM调整 → 输出最优学习顺序。

**AI核心价值**：传统拓扑排序只看依赖关系，AI可以考虑知识点的重要程度、学习曲线难度、用户当前状态等因素。

## 六、输出格式

### 知识点JSON格式
```json
{
  "concepts": [
    {
      "id": "concept_1",
      "name": "梯度下降",
      "definition": "一种通过迭代最小化损失函数来优化模型参数的算法",
      "category": "机器学习/优化算法",
      "difficulty": "intermediate",
      "source_text": "..."
    }
  ]
}
```

### 知识图谱JSON格式
```json
{
  "nodes": [
    {"id": "concept_1", "name": "梯度下降", "category": "机器学习"},
    {"id": "concept_2", "name": "导数", "category": "数学"}
  ],
  "edges": [
    {"source": "concept_2", "target": "concept_1", "relation": "前置依赖", "explanation": "梯度下降需要用到导数计算梯度"}
  ]
}
```

## 七、注意事项

1. 需要有效的LLM API密钥（推荐使用DeepSeek，有免费额度）
2. 文本量较大时建议分批处理，单次建议不超过8000字符
3. 知识图谱的可视化需要matplotlib支持中文显示
4. 所有中间结果以JSON格式持久化，支持增量更新
