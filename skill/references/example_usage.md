# 使用示例详解

## 示例一：从零开始构建机器学习知识图谱

### 场景
你正在学习吴恩达的机器学习课程，想建立自己的知识体系。

### 步骤

#### 1. 准备笔记
将你的课程笔记保存为 Markdown 文件 `data/notes/ml_week1.md`：

```markdown
# 机器学习 Week 1: 线性回归

## 监督学习
监督学习是一种机器学习方法，通过带标签的训练数据学习从输入到输出的映射关系。
主要分为回归问题和分类问题。

## 线性回归
线性回归是最基础的回归算法，目标是找到一条直线（或超平面）使得预测值与真实值的
均方误差最小。模型形式为 y = wx + b。

## 代价函数
代价函数（Cost Function）用于衡量模型预测值与真实值之间的差距。
在线性回归中最常用的是均方误差（MSE）：J(w,b) = (1/2m) * Σ(h(x)-y)²。

## 梯度下降
梯度下降是一种迭代优化算法，通过沿着代价函数梯度的反方向更新参数来最小化代价函数。
参数更新公式：w := w - α * ∂J/∂w，其中α是学习率。

## 学习率
学习率（Learning Rate）控制梯度下降每次迭代的步长。学习率过大可能导致不收敛或震荡，
过小则收敛速度太慢。
```

#### 2. 抽取知识点
```bash
$ python skill/scripts/cli.py extract -i data/notes/ml_week1.md -o data/output/ml_concepts.json

✅ 知识点抽取完成！
   抽取知识点: 6 个
   主题概括: 机器学习基础概念，包括监督学习、线性回归、梯度下降及学习率调整
   输出文件: data/output/ml_concepts.json
```

#### 3. 构建知识图谱
```bash
$ python skill/scripts/cli.py build-graph -c data/output/ml_concepts.json -o data/output/ml_graph.json -v

✅ 知识图谱构建完成！
   节点: 6, 边: 8
   关系分布: {'prerequisite': 4, 'related': 2, 'contains': 1, 'contrast': 1}
   可视化: data/output/ml_graph.png
```

#### 4. 生成复习题目
```bash
$ python skill/scripts/cli.py generate-questions -g data/output/ml_graph.json -n 5 -o data/output/ml_questions.json

✅ 题目生成完成！
   题目总数: 5
   题型分布: {'single': 2, 'chain': 2, 'compare': 1}
   难度分布: {'easy': 2, 'medium': 2, 'hard': 1}
```

#### 5. 推荐学习路径
```bash
$ python skill/scripts/cli.py recommend-path -g data/output/ml_graph.json -o data/output/ml_path.json

✅ 学习路径推荐完成！
   总步数: 6
   预计时间: 约3小时

推荐学习顺序:
    1. [监督学习] — 这是整个主题的入口概念...
    2. [线性回归] — 监督学习中最重要的回归算法...
    3. [代价函数] — 理解线性回归需要先懂代价函数...
    4. [梯度下降] — 需要代价函数的知识作为基础...
    5. [学习率] — 梯度下降的关键参数...
```

---

## 示例二：多章节合并与增量更新

### 场景
你已经学完了机器学习 Week 1-3，现在要加入 Week 4 的内容。

```bash
# Step 1: 抽取新章节
python cli.py extract -i data/notes/ml_week4.md -o data/output/w4_concepts.json

# Step 2: 合并知识点
python -c "
import json
from skill.scripts.utils import load_json, save_json

old = load_json('data/output/ml_concepts.json')
new = load_json('data/output/w4_concepts.json')
merged = {
    'concepts': old['concepts'] + new['concepts'],
    'summary': old['summary'] + '; ' + new['summary']
}
save_json(merged, 'data/output/ml_merged.json')
"

# Step 3: 重新构建图谱（因为新知识可能改变关系）
python cli.py build-graph -c data/output/ml_merged.json -o data/output/ml_graph_v2.json -v

# Step 4: 更新后的学习路径
python cli.py recommend-path -g data/output/ml_graph_v2.json \
    -m "监督学习" "线性回归" "代价函数" "梯度下降" \
    -o data/output/ml_path_v2.json
```

---

## 示例三：面向考试的精准备考

### 场景
考试范围是数据结构第3-5章，你已经掌握了第3章。

```bash
# 1. 一次性处理所有相关章节
python cli.py full-pipeline \
    --input data/notes/ds_ch3-5/ \
    --output data/output/ds_exam/ \
    --visualize \
    --question-count 20

# 2. 生成练习卷
python cli.py generate-questions \
    -g data/output/ds_exam/graph.json \
    --practice-set \
    --easy 5 --medium 10 --hard 5 \
    -o data/output/ds_exam/practice_exam.json

# 3. 标记已掌握知识点后，获取个性化路径
python cli.py recommend-path \
    -g data/output/ds_exam/graph.json \
    -m "链表" "栈" "队列" "递归" "时间复杂度" \
    -t "红黑树" \
    -o data/output/ds_exam/path_to_rbtree.json
```

---

## 示例四：跨学科知识串联

### 场景
想理解机器学习中的"梯度下降"和你数学课学的"导数/偏导数"之间的联系。

```bash
# 分别抽取
python cli.py extract -i data/notes/math_calculus.md -o data/output/math_concepts.json
python cli.py extract -i data/notes/ml_optimization.md -o data/output/ml_concepts.json

# 合并后构建图谱（AI会自动发现跨学科联系）
python -c "
import json
m = json.load(open('data/output/math_concepts.json'))
l = json.load(open('data/output/ml_concepts.json'))
json.dump({'concepts': m['concepts']+l['concepts']}, open('data/output/cross_concepts.json','w'))
"

python cli.py build-graph -c data/output/cross_concepts.json -o data/output/cross_graph.json -v

# 生成的图谱中，AI会自动发现：
# 导数(数学) --[前置依赖]--> 偏导数(数学) --[前置依赖]--> 梯度(数学) --[前置依赖]--> 梯度下降(ML)
```
