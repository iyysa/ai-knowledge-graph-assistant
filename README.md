# AI知识图谱学习助手 (AI Knowledge Graph Learning Assistant)

> AI个人系统实践 — 结课项目  
> 选题类型：自主拟定 | 所属分类：学习学业 | 落地难度：★★轻依赖

## 一、选题理由

**为什么选择"AI知识图谱学习助手"？**

大学生在学习过程中面临一个普遍困境：**知识碎片化**。每门课、每本书、每篇论文都包含大量概念，但这些概念之间是什么关系？应该先学哪个后学哪个？哪些概念在跨学科场景下有关联？

传统做法是手动整理思维导图，但效率极低——12个概念之间就有66种可能的关系需要判断。当概念数量达到100个时，可能的关系数高达4950种，人工整理完全不现实。

这正是**AI大语言模型的核心优势所在**：它可以一次性理解全部概念，推理它们之间的逻辑关系（前置依赖/相关延伸/对立对比/包含关系），构建结构化的知识图谱。这种语义级别的理解和推理是传统编程手段无法实现的。

### AI核心价值论证

| 功能 | 传统做法 | AI做法 | AI的不可替代性 |
|------|---------|--------|---------------|
| 概念抽取 | 人工阅读+手动摘录（1小时/章） | LLM秒级理解全文语义 | 需要语义级别的文本理解 |
| 关系推理 | 人脑联想（容易遗漏） | LLM系统性分析所有概念对 | 需要广博的知识储备+逻辑推理 |
| 题目生成 | 教师手动出题（1小时/份） | 沿知识图谱路径自动生成综合题 | 需要理解知识拓扑结构 |
| 路径规划 | 照教材目录学（一刀切） | 结合个人掌握状态+图谱结构的个性化推荐 | 需要综合多维度信息做决策 |

## 二、功能简介

本Skill封装了四个核心AI驱动模块：

1. **知识点抽取** (`knowledge_extractor.py`) — 从Markdown/文本学习材料中自动识别核心概念
2. **知识图谱构建** (`graph_builder.py`) — 分析概念间关系，生成有向知识图谱
3. **关联问题生成** (`question_generator.py`) — 基于图谱拓扑结构生成跨章节综合题
4. **学习路径推荐** (`learning_path.py`) — 结合个人掌握状态推荐最优学习顺序

## 三、快速开始

### 环境要求

- Python >= 3.10
- LLM API密钥（推荐DeepSeek，有免费额度）

### 安装

```bash
# 克隆仓库
git clone <你的仓库地址>
cd ai-knowledge-graph-assistant

# 安装依赖
pip install openai networkx pyyaml matplotlib rich

# 配置API
cp skill/references/api_config.yaml api_config.yaml
# 编辑 api_config.yaml，填写你的API密钥
```

### 使用

```bash
# 一键全流程
python skill/scripts/cli.py full-pipeline \
    --input data/notes/ \
    --output data/output/ \
    --visualize

# 或分步执行
python skill/scripts/cli.py extract -i data/notes/python_data_structures.md -o concepts.json
python skill/scripts/cli.py build-graph -c concepts.json -o graph.json -v
python skill/scripts/cli.py generate-questions -g graph.json -n 10 -o questions.json
python skill/scripts/cli.py recommend-path -g graph.json -o path.json
```

### 运行测试

```bash
python tests/test_runner.py
```

## 四、项目结构

```
ai-knowledge-graph-assistant/
├── README.md                          # 本文件
├── skill/                             # Skill 技能文件
│   ├── SKILL.md                       # 技能定义（含YAML前端配置）
│   ├── scripts/                       # 核心脚本
│   │   ├── cli.py                     # 命令行统一入口
│   │   ├── utils.py                   # 工具模块（配置/LLM/文件操作）
│   │   ├── knowledge_extractor.py     # 知识点抽取
│   │   ├── graph_builder.py           # 知识图谱构建
│   │   ├── question_generator.py      # 关联问题生成
│   │   └── learning_path.py           # 学习路径推荐
│   └── references/                    # 参考文件
│       ├── api_config.yaml            # API配置模板
│       ├── best_practices.md          # 最佳实践指南
│       └── example_usage.md           # 详细使用示例
├── data/                              # 测试数据
│   └── notes/
│       ├── python_data_structures.md  # Python数据结构笔记
│       └── algorithm_complexity.md    # 算法复杂度笔记
├── tests/                             # 测试记录
│   ├── test_runner.py                 # 自动化测试脚本
│   ├── test_record.md                 # 测试记录文档
│   ├── test_output.log                # 测试执行日志
│   └── test_graph.png                 # 知识图谱可视化截图
└── iteration/                         # 迭代升级
    └── iteration_log.md               # 4个后续迭代方向
```

## 五、技术亮点

- **模块化设计**：四个核心模块独立封装，可单独使用或组合成完整流水线
- **单例LLM客户端**：全局共享一个LLM连接，避免重复初始化
- **多级配置管理**：默认配置 → 用户配置 → 环境变量，优先级清晰
- **Mock测试模式**：完整的测试套件使用模拟LLM，不依赖外部API即可验证所有逻辑
- **大文本分块**：自动处理超长文本，保持段落完整性
- **图谱可视化**：支持静态PNG导出和Mermaid代码生成

## 六、测试验证

全部 **54项测试用例** 通过，覆盖6个测试模块：

| 模块 | 测试项数 | 通过率 |
|------|---------|--------|
| 知识点抽取 | 10 | 100% |
| 知识图谱构建 | 6 | 100% |
| 关联问题生成 | 11 | 100% |
| 学习路径推荐 | 11 | 100% |
| CLI命令行功能 | 11 | 100% |
| 边界情况与健壮性 | 5 | 100% |

详见 `tests/test_record.md`。

## 七、迭代规划

详见 `iteration/iteration_log.md`，包含4个后续迭代方向：

1. **增量知识更新与图谱版本管理** — P0优先级
2. **交互式知识图谱可视化** — P1优先级  
3. **基于用户行为的自适应难度调整** — P1优先级
4. **多模态学习材料支持** — P2优先级

## 八、许可

本项目为课程作业项目，仅供学习交流使用。
