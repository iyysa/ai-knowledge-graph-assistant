# AI知识图谱学习助手 — 最佳实践指南

## 一、输入材料准备

### 1.1 什么样的材料效果好

| 好 | 不好 |
|----|------|
| 结构化的教材/讲义 | 纯聊天记录 |
| 概念密度高的文本 | 大段的代码/公式推导 |
| 有明确分节/标题的文档 | 无结构的碎片笔记 |
| 连续的章节内容 | 跳转太大的摘录 |

### 1.2 推荐的处理方式

```bash
# ✅ 推荐：按章节分别处理
python cli.py extract -i ch1_线性回归.md -o ch1_concepts.json
python cli.py extract -i ch2_逻辑回归.md -o ch2_concepts.json

# ✅ 后将所有章节合并构建整体图谱
python cli.py build-graph -c merged_concepts.json -o full_graph.json

# ❌ 不推荐：一次性喂入整本教材（超长文本分块可能丢失跨章节关系）
```

### 1.3 文本预处理建议

- 删除与学习无关的内容（广告、目录、页眉页脚）
- 确保公式使用 LaTeX 格式或文字描述
- 代码片段保留关键注释即可

## 二、提示词调优

### 2.1 知识点抽取调优

如果抽取结果太泛：
```
修改 knowledge_extractor.py 中的 EXTRACTION_SYSTEM_PROMPT，
添加："每个知识点必须有明确的数学定义或操作定义，不要抽取过于宽泛的概念"
```

如果抽取太多细枝末节：
```
添加："只抽取本学科的核心概念，数量控制在15-30个之间"
```

### 2.2 图谱关系调优

如果关系太少：
```
在 GRAPH_BUILD_SYSTEM_PROMPT 增加："至少为80%的知识点建立关系"
```

如果关系错误较多：
```
降低 temperature 至 0.1，并增加："只建立你100%确定的关系，不确定的不要瞎猜"
```

## 三、API 选择建议

### 3.1 各模型对比

| 模型 | 单次调用成本 | 推理质量 | 推荐场景 |
|------|------------|---------|---------|
| deepseek-chat | 极低（有免费额度） | ⭐⭐⭐⭐ | 日常使用 |
| deepseek-reasoner | 低 | ⭐⭐⭐⭐⭐ | 需要深度推理的关系分析 |
| moonshot-v1-8k | 中 | ⭐⭐⭐ | 中文材料优秀 |
| qwen-turbo | 低 | ⭐⭐⭐ | 通义系生态 |

### 3.2 成本估算

以 deepseek-chat 为例：
- 知识点抽取：约 2000 input tokens + 1500 output tokens = ¥0.003/次
- 图谱构建（20节点）：约 3000 input + 2000 output = ¥0.005/次
- 问题生成（10题）：约 4000 input + 3000 output = ¥0.007/次
- **平均单轮全流程成本 < ¥0.02**

## 四、知识图谱维护

### 4.1 增量更新策略

```bash
# 1. 只抽取新增章节
python cli.py extract -i ch5_神经网络.md -o ch5_concepts.json

# 2. 写脚本合并新老知识点（见下方示例）
python scripts/merge_concepts.py old_concepts.json ch5_concepts.json -o merged.json

# 3. 重新构建图谱（因为新知识点可能改变现有关系）
python cli.py build-graph -c merged.json -o updated_graph.json
```

### 4.2 图谱版本管理

建议使用 Git 管理你的知识图谱：

```bash
git add data/graph.json
git commit -m "feat: 添加第5章神经网络知识点，图谱从42节点增至58节点"
```

## 五、学习路径使用建议

### 5.1 诚实标记掌握状态

路径推荐的质量取决于你标记的准确性：
- ✅ "变量" — 你真的能给别人讲清楚这个概念
- ❌ "好像会" — 如果说不清楚知识点之间的区别和联系，就标记为未掌握

### 5.2 迭代使用

```
第1天：运行全流程 → 按推荐路径学习 → 标记新增掌握的知识点
第3天：只运行 recommend-path → 更新路径（因为掌握状态变了）
第7天：重新运行 full-pipeline → 综合复习
```

## 六、常见问题

### Q: LLM返回的JSON格式不正确怎么办？

```
Answer: 检查 scripts/utils.py 中的 _parse_json 方法。
工具已内置了 ```json 代码块提取逻辑，大部分情况能自动处理。
如果频繁出错，降低 temperature 至 0.1 或更换模型。
```

### Q: 知识图谱可视化中文乱码？

```
Answer: 需要系统安装中文字体。
Windows: 一般自带微软雅黑，不需要额外配置。
Linux: sudo apt install fonts-wqy-microhei
Mac: 一般自带PingFang，不需要额外配置。

如果仍有问题，在 graph_builder.py 的 visualize() 方法中添加：
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'WenQuanYi Micro Hei']
```

### Q: 能否不依赖在线API离线运行？

```
Answer: 可以，但需要本地部署模型。
在 api_config.yaml 中将 base_url 指向本地 Ollama/vLLM 服务：
base_url: "http://localhost:11434/v1"
model: "qwen2.5:7b"
注意：本地小模型在关系推理方面可能不如大模型准确。
```
