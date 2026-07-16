#!/usr/bin/env python3
"""
test_runner.py — 基于Mock LLM的完整测试套件

使用模拟LLM响应验证所有核心模块的功能正确性。
测试覆盖：知识点抽取、图谱构建、问题生成、学习路径推荐。
"""

import json
import sys
from pathlib import Path

# 将项目根目录和 scripts 加入路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "skill" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

# ============================================================
# Mock LLM 响应数据
# ============================================================

MOCK_EXTRACTION_RESPONSE = {
    "concepts": [
        {
            "name": "变量",
            "definition": "变量是存储数据的命名容器，Python中变量不需要声明类型，属于动态类型",
            "category": "编程/Python基础",
            "difficulty": "basic",
            "keywords": ["变量", "动态类型", "赋值", "数据类型"],
        },
        {
            "name": "列表（List）",
            "definition": "列表是Python中最常用的有序、可变的数据结构，用方括号定义，支持索引访问和切片操作",
            "category": "编程/数据结构",
            "difficulty": "basic",
            "keywords": ["列表", "有序", "可变", "索引", "切片"],
        },
        {
            "name": "元组（Tuple）",
            "definition": "元组与列表类似但是不可变的数据结构，用圆括号定义，适用于存储不应被修改的数据",
            "category": "编程/数据结构",
            "difficulty": "basic",
            "keywords": ["元组", "不可变", "哈希", "序列"],
        },
        {
            "name": "字典（Dictionary）",
            "definition": "字典是基于哈希表实现的键值对集合，支持O(1)时间复杂度的查找、插入和删除操作",
            "category": "编程/数据结构",
            "difficulty": "intermediate",
            "keywords": ["字典", "哈希表", "键值对", "O(1)"],
        },
        {
            "name": "集合（Set）",
            "definition": "集合是无序、不重复元素的集合，基于哈希表实现，支持数学集合运算（交并差对称差）",
            "category": "编程/数据结构",
            "difficulty": "basic",
            "keywords": ["集合", "去重", "哈希表", "集合运算"],
        },
        {
            "name": "字符串",
            "definition": "字符串是不可变的字符序列，支持丰富的操作方法（查找、分割、格式化等）",
            "category": "编程/Python基础",
            "difficulty": "basic",
            "keywords": ["字符串", "不可变", "序列", "格式化"],
        },
        {
            "name": "时间复杂度",
            "definition": "时间复杂度用大O表示法描述算法执行时间随输入规模的增长趋势",
            "category": "算法/复杂度分析",
            "difficulty": "intermediate",
            "keywords": ["时间复杂度", "大O", "渐近分析", "性能"],
        },
        {
            "name": "空间复杂度",
            "definition": "空间复杂度描述算法执行所需的额外存储空间随输入规模的增长趋势",
            "category": "算法/复杂度分析",
            "difficulty": "intermediate",
            "keywords": ["空间复杂度", "原地算法", "内存", "递归栈"],
        },
        {
            "name": "哈希表",
            "definition": "哈希表是通过哈希函数将键映射到数组索引的数据结构，核心操作平均O(1)",
            "category": "算法/数据结构",
            "difficulty": "intermediate",
            "keywords": ["哈希表", "哈希函数", "冲突解决", "开放寻址"],
        },
        {
            "name": "排序算法",
            "definition": "排序算法是将一组数据元素按照特定顺序重新排列的算法，常见的有冒泡、选择、插入、归并、快速、堆排序等",
            "category": "算法/排序",
            "difficulty": "intermediate",
            "keywords": ["排序", "比较", "稳定", "分治"],
        },
        {
            "name": "递归",
            "definition": "递归是函数调用自身来解决问题的方法，必须有基准条件防止无限递归",
            "category": "算法/编程范式",
            "difficulty": "intermediate",
            "keywords": ["递归", "基准条件", "栈帧", "分治"],
        },
        {
            "name": "迭代",
            "definition": "迭代是使用循环重复执行代码块的方法，通常比递归效率更高",
            "category": "算法/编程范式",
            "difficulty": "basic",
            "keywords": ["迭代", "循环", "效率", "显式栈"],
        },
    ],
    "summary": "Python数据结构与算法复杂度基础知识的综合讲解",
}

MOCK_GRAPH_RESPONSE = {
    "edges": [
        {
            "source": "变量",
            "target": "列表（List）",
            "relation": "prerequisite",
            "explanation": "理解列表需要先理解变量的概念",
        },
        {
            "source": "列表（List）",
            "target": "元组（Tuple）",
            "relation": "contrast",
            "explanation": "列表可变，元组不可变，需要对比理解两种序列类型的区别",
        },
        {
            "source": "哈希表",
            "target": "字典（Dictionary）",
            "relation": "prerequisite",
            "explanation": "字典底层基于哈希表实现，理解哈希表原理对使用字典很重要",
        },
        {
            "source": "哈希表",
            "target": "集合（Set）",
            "relation": "prerequisite",
            "explanation": "集合也基于哈希表实现，哈希表是理解集合的基础",
        },
        {
            "source": "字典（Dictionary）",
            "target": "集合（Set）",
            "relation": "related",
            "explanation": "都基于哈希表，都是无序集合，但用途不同",
        },
        {
            "source": "时间复杂度",
            "target": "哈希表",
            "relation": "prerequisite",
            "explanation": "理解哈希表O(1)操作需要先理解时间复杂度的概念",
        },
        {
            "source": "时间复杂度",
            "target": "排序算法",
            "relation": "prerequisite",
            "explanation": "比较排序算法需要以时间复杂度作为衡量标准",
        },
        {
            "source": "排序算法",
            "target": "递归",
            "relation": "related",
            "explanation": "归并排序和快速排序都使用了递归的分治思想",
        },
        {
            "source": "递归",
            "target": "迭代",
            "relation": "contrast",
            "explanation": "递归和迭代是解决问题的两种不同范式，经常需要对比选择",
        },
        {
            "source": "变量",
            "target": "字符串",
            "relation": "prerequisite",
            "explanation": "字符串作为一种数据类型，需要先理解变量的概念",
        },
        {
            "source": "列表（List）",
            "target": "字符串",
            "relation": "related",
            "explanation": "字符串和列表都是序列类型，共享切片等操作",
        },
        {
            "source": "时间复杂度",
            "target": "空间复杂度",
            "relation": "related",
            "explanation": "时间和空间复杂度共同构成算法效率的完整评估",
        },
    ],
    "graph_stats": {
        "total_nodes": 12,
        "connected_nodes": 12,
        "isolated_nodes": 0,
    },
}

MOCK_QUESTION_RESPONSE = {
    "questions": [
        {
            "id": "q001",
            "type": "single",
            "question": "解释列表（List）的三个核心特性，并分别给出代码示例。",
            "concepts_involved": ["列表（List）"],
            "path": ["列表（List）"],
            "difficulty": "easy",
            "answer_hint": "从有序性、可变性、索引访问三个方面回答",
            "explanation": "考察对列表基本特性的理解",
        },
        {
            "id": "q002",
            "type": "chain",
            "question": "从变量概念出发，解释为什么列表的append()操作是O(1)均摊时间复杂度？在处理大量数据时，这个特性有什么实际意义？",
            "concepts_involved": ["变量", "列表（List）", "时间复杂度"],
            "path": ["变量 → 列表（List）→ 时间复杂度"],
            "difficulty": "medium",
            "answer_hint": "1) append本质上是在数组末尾写入; 2) 扩容时的均摊分析; 3) 对大数据处理的性能影响",
            "explanation": "这道题需要串联变量存储模型、列表的动态数组实现和时间复杂度分析",
        },
        {
            "id": "q003",
            "type": "chain",
            "question": "哈希表的O(1)查找是如何实现的？当字典的键越来越多时，查找性能会如何变化？请结合Python字典的实现来说明。",
            "concepts_involved": ["时间复杂度", "哈希表", "字典（Dictionary）"],
            "path": ["时间复杂度 → 哈希表 → 字典（Dictionary）"],
            "difficulty": "medium",
            "answer_hint": "哈希函数映射 → 开放寻址 → 负载因子 → 扩容rehashing",
            "explanation": "综合考察时间复杂度的实际体现、哈希表原理和Python字典的具体实现",
        },
        {
            "id": "q004",
            "type": "compare",
            "question": "比较列表（List）和元组（Tuple）的异同。在什么场景下应该使用元组而不是列表？给出至少3个实际编程场景。",
            "concepts_involved": ["列表（List）", "元组（Tuple）"],
            "path": ["列表（List）↔ 元组（Tuple）"],
            "difficulty": "easy",
            "answer_hint": "从可变性、性能、语义（是否需要保护数据）、可作为字典键等方面比较",
            "explanation": "通过对比加深对两种序列类型的理解",
        },
        {
            "id": "q005",
            "type": "compare",
            "question": "递归和迭代各有什么优缺点？给定一个求斐波那契数列第n项的问题，分别用递归和无记忆化递归、迭代三种方式实现，分析各自的时间复杂度和空间复杂度。",
            "concepts_involved": ["递归", "迭代", "时间复杂度", "空间复杂度"],
            "path": ["递归 ↔ 迭代"],
            "difficulty": "hard",
            "answer_hint": "无记忆化递归O(2^n) → 记忆化递归O(n) → 迭代O(n)且O(1)空间",
            "explanation": "通过经典问题对比两种范式的性能差异，同时综合运用复杂度分析",
        },
        {
            "id": "q006",
            "type": "apply",
            "question": "你需要实现一个学生成绩管理系统，支持：1)按姓名快速查找成绩; 2)按成绩排名; 3)统计每个分数段的人数。请为每个需求选择合适的数据结构，并解释选择的理由（考虑时间复杂度）。",
            "concepts_involved": ["字典（Dictionary）", "列表（List）", "排序算法", "时间复杂度"],
            "path": ["字典（Dictionary）+ 列表（List）+ 排序算法 → 综合应用"],
            "difficulty": "hard",
            "answer_hint": "查找用字典O(1); 排名用列表+排序O(n log n); 分段统计用字典O(n)",
            "explanation": "实际场景中的数据结构和算法选择，综合运用多个知识点",
        },
        {
            "id": "q007",
            "type": "single",
            "question": "什么是时间复杂度的大O表示法？为什么我们在分析时忽略常数系数和低阶项？",
            "concepts_involved": ["时间复杂度"],
            "path": ["时间复杂度"],
            "difficulty": "easy",
            "answer_hint": "大O表示增长趋势; 当n很大时常数影响可忽略; 高阶项主导增长",
            "explanation": "巩固时间复杂度分析的基本概念",
        },
        {
            "id": "q008",
            "type": "apply",
            "question": "设计一个简易的去重系统：给定一个包含100万条URL的列表，需要快速判断新URL是否已存在。你会选择什么数据结构？如果内存只有100MB怎么办？",
            "concepts_involved": ["集合（Set）", "哈希表", "空间复杂度"],
            "path": ["哈希表 → 集合（Set）→ 空间复杂度 → 实际约束"],
            "difficulty": "hard",
            "answer_hint": "首选集合O(1)查找; 内存不足考虑布隆过滤器（允许少量误判）",
            "explanation": "结合实际约束进行数据结构选型，考察工程思维",
        },
        {
            "id": "q009",
            "type": "chain",
            "question": "解释Python中字符串的不可变性。如果需要在循环中拼接大量字符串，为什么推荐使用join()而不是+操作符？请从时间复杂度的角度分析。",
            "concepts_involved": ["字符串", "列表（List）", "时间复杂度"],
            "path": ["字符串 → 列表（List）→ 时间复杂度"],
            "difficulty": "medium",
            "answer_hint": "每次+创建新字符串O(n²); join()一次性分配O(n); 先收集到列表再join",
            "explanation": "通过性能分析理解不可变对象操作的正确姿势",
        },
        {
            "id": "q010",
            "type": "compare",
            "question": "比较冒泡排序、归并排序和快速排序的适用场景。在数据近乎有序时，哪种算法最好？为什么Python的Timsort被选为默认排序算法？",
            "concepts_involved": ["排序算法", "时间复杂度", "空间复杂度"],
            "path": ["排序算法（冒泡↔归并↔快速）"],
            "difficulty": "medium",
            "answer_hint": "近乎有序时插入排序/Timsort最优; Timsort综合了归并的稳定性和插入排序对有序数据的优势",
            "explanation": "通过对比不同排序算法理解'没有银弹'的工程原则",
        },
    ],
}

MOCK_PATH_RESPONSE = {
    "learning_path": [
        {
            "step": 1,
            "concept_name": "变量",
            "reason": "所有编程概念的入口，必须先理解数据的存储模型",
            "estimated_time": "20min",
            "study_tips": "重点理解Python动态类型的含义和基本数据类型",
            "prerequisites_satisfied": [],
            "leads_to": ["列表（List）", "字符串", "字典（Dictionary）"],
        },
        {
            "step": 2,
            "concept_name": "时间复杂度",
            "reason": "算法分析的基石，后面学数据结构和排序都需要",
            "estimated_time": "40min",
            "study_tips": "从大O的直观理解开始，用具体代码示例感受不同复杂度的差异",
            "prerequisites_satisfied": [],
            "leads_to": ["哈希表", "排序算法"],
        },
        {
            "step": 3,
            "concept_name": "列表（List）",
            "reason": "最常用的数据结构，是学习其他序列类型的基础",
            "estimated_time": "30min",
            "study_tips": "动手实现列表的CRUD操作，理解动态数组的扩容机制",
            "prerequisites_satisfied": ["变量"],
            "leads_to": ["元组（Tuple）", "字符串"],
        },
        {
            "step": 4,
            "concept_name": "哈希表",
            "reason": "核心数据结构，理解后字典和集合的原理一目了然",
            "estimated_time": "45min",
            "study_tips": "手动画一个简单哈希表，模拟insert和search过程",
            "prerequisites_satisfied": ["时间复杂度"],
            "leads_to": ["字典（Dictionary）", "集合（Set）"],
        },
        {
            "step": 5,
            "concept_name": "字典（Dictionary）",
            "reason": "Python中最强大的内置数据结构之一",
            "estimated_time": "30min",
            "study_tips": "结合哈希表原理理解为什么键必须可哈希",
            "prerequisites_satisfied": ["哈希表"],
            "leads_to": ["集合（Set）"],
        },
        {
            "step": 6,
            "concept_name": "集合（Set）",
            "reason": "和字典共享哈希表底层，学习成本低",
            "estimated_time": "20min",
            "study_tips": "对比字典，理解集合只存键不存值的设计选择",
            "prerequisites_satisfied": ["哈希表", "字典（Dictionary）"],
            "leads_to": [],
        },
        {
            "step": 7,
            "concept_name": "元组（Tuple）",
            "reason": "和列表对比学习，理解不可变性的价值",
            "estimated_time": "15min",
            "study_tips": "重点理解元组的应用场景：作为字典键、函数多返回值",
            "prerequisites_satisfied": ["列表（List）"],
            "leads_to": [],
        },
        {
            "step": 8,
            "concept_name": "字符串",
            "reason": "序列类型的综合应用，连接之前学到的切片等概念",
            "estimated_time": "25min",
            "study_tips": "重点练习f-string格式化和join的性能优化",
            "prerequisites_satisfied": ["变量", "列表（List）"],
            "leads_to": [],
        },
        {
            "step": 9,
            "concept_name": "排序算法",
            "reason": "算法分析的集大成者，综合运用时间/空间复杂度",
            "estimated_time": "60min",
            "study_tips": "从冒泡排序开始逐步优化到快速排序，感受算法设计思路",
            "prerequisites_satisfied": ["时间复杂度"],
            "leads_to": ["递归"],
        },
        {
            "step": 10,
            "concept_name": "空间复杂度",
            "reason": "在了解多种数据结构后，学习空间换时间的思想",
            "estimated_time": "30min",
            "study_tips": "结合哈希表和排序算法的空间消耗来理解",
            "prerequisites_satisfied": ["时间复杂度"],
            "leads_to": [],
        },
        {
            "step": 11,
            "concept_name": "递归",
            "reason": "排序算法（归并/快速）都用到递归，衔接自然",
            "estimated_time": "40min",
            "study_tips": "先画递归树理解调用过程，再动手写代码",
            "prerequisites_satisfied": ["排序算法"],
            "leads_to": ["迭代"],
        },
        {
            "step": 12,
            "concept_name": "迭代",
            "reason": "和递归对比学习，掌握两种范式的选择和转换",
            "estimated_time": "25min",
            "study_tips": "尝试将之前的递归排序算法改写为迭代版本",
            "prerequisites_satisfied": ["递归"],
            "leads_to": [],
        },
    ],
    "overall_plan": {
        "total_steps": 12,
        "total_estimated_time": "约6.5小时",
        "strategy": "先建立时序复杂度的理论基础，再按'基础类型→序列类型→哈希类型→排序算法→编程范式'的顺序递进学习",
    },
}


# ============================================================
# Mock LLM Client
# ============================================================
class MockLLMClient:
    """模拟LLM客户端，返回预定义的测试数据。支持参数感知。"""

    def __init__(self):
        self.call_count = 0
        self.call_history = []

    def chat(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        self.call_count += 1
        self.call_history.append({
            "call": self.call_count,
            "system_prompt_preview": system_prompt[:100],
            "user_prompt_preview": user_prompt[:100],
        })
        response = self._get_mock_response(system_prompt, user_prompt)
        return json.dumps(response, ensure_ascii=False)

    def chat_json(self, system_prompt: str, user_prompt: str, **kwargs) -> dict:
        return self._get_mock_response(system_prompt, user_prompt)

    def _get_mock_response(self, system_prompt: str, user_prompt: str) -> dict:
        # 知识图谱构建（必须在"提取"之前检查，因为图谱提示词也包含"提取"二字）
        if "知识图谱构建" in system_prompt:
            return MOCK_GRAPH_RESPONSE
        # 知识点抽取
        elif "知识点抽取" in system_prompt or "提取所有" in system_prompt:
            return MOCK_EXTRACTION_RESPONSE
        # 问题生成
        elif "教育测评" in system_prompt:
            return self._filter_questions(user_prompt)
        # 学习路径
        elif "学习规划" in system_prompt:
            return self._filter_path(user_prompt)
        else:
            return {"result": "unknown prompt type"}

    def _filter_questions(self, user_prompt: str) -> dict:
        """根据用户参数筛选题目数量和难度"""
        questions = MOCK_QUESTION_RESPONSE["questions"][:]

        # 解析数量
        import re
        count_match = re.search(r'生成\s*(\d+)\s*道', user_prompt)
        if not count_match:
            count_match = re.search(r'生成\s+(\d+)', user_prompt)
        count = int(count_match.group(1)) if count_match else 10

        # 解析难度
        diff_match = re.search(r'难度应为[：:]\s*(\w+)', user_prompt)
        if diff_match:
            diff = diff_match.group(1)
            questions = [q for q in questions if q.get("difficulty") == diff]

        # 如果不够count，循环填充
        while len(questions) < count and questions:
            questions.extend(questions[:count - len(questions)])

        return {"questions": questions[:count]}

    def _filter_path(self, user_prompt: str) -> dict:
        """根据用户已掌握知识点过滤学习路径"""
        full_path = MOCK_PATH_RESPONSE["learning_path"][:]

        # 解析已掌握的知识点
        import re
        mastered_match = re.search(r'已掌握的知识点[：:]\s*(.+)', user_prompt)
        mastered = []
        if mastered_match:
            mastered_str = mastered_match.group(1).strip()
            if mastered_str and mastered_str != '无':
                # 简单按逗号分割
                mastered = [m.strip() for m in mastered_str.split(',')]

        if not mastered:
            return MOCK_PATH_RESPONSE

        # 过滤已掌握的
        filtered_path = [
            step for step in full_path
            if step["concept_name"] not in mastered
        ]

        # 重新编号
        for i, step in enumerate(filtered_path):
            step["step"] = i + 1

        return {
            "learning_path": filtered_path,
            "overall_plan": {
                "total_steps": len(filtered_path),
                "total_estimated_time": f"约{len(filtered_path) * 30}分钟",
                "strategy": MOCK_PATH_RESPONSE["overall_plan"]["strategy"],
            },
        }


def mock_init():
    """初始化Mock模式"""
    import utils
    utils._CONFIG = utils.ConfigManager()
    utils._LLM = MockLLMClient()
    return utils._CONFIG, utils._LLM


# ============================================================
# 测试用例
# ============================================================
class TestRunner:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0

    def run_all(self):
        print("=" * 70)
        print("  AI知识图谱学习助手 — 自动化测试套件")
        print("  模式: Mock LLM (模拟大模型响应)")
        print("=" * 70)

        self._test_extraction()
        self._test_graph_building()
        self._test_question_generation()
        self._test_learning_path()
        self._test_cli_commands()
        self._test_edge_cases()

        print("\n" + "=" * 70)
        print(f"  测试结果: {self.passed} 通过, {self.failed} 失败, 共 {self.passed + self.failed} 项")
        print("=" * 70)

        return self.passed == self.passed + self.failed  # all passed

    def _assert(self, condition, test_name: str, detail: str = ""):
        if condition:
            self.passed += 1
            print(f"  ✅ PASS: {test_name}")
        else:
            self.failed += 1
            print(f"  ❌ FAIL: {test_name}")
            if detail:
                print(f"     详情: {detail}")
        self.results.append({
            "test": test_name,
            "passed": condition,
            "detail": detail,
        })

    def _test_extraction(self):
        print("\n📋 [测试模块1] 知识点抽取")
        print("-" * 50)
        mock_init()

        from knowledge_extractor import KnowledgeExtractor

        extractor = KnowledgeExtractor()

        # 测试1: 从文件抽取
        test_file = str(PROJECT_ROOT / "data" / "notes" / "python_data_structures.md")
        result = extractor.extract_from_file(test_file)
        self._assert(
            len(result["concepts"]) > 0,
            "从文件抽取知识点",
            f"抽取到 {len(result['concepts'])} 个知识点",
        )
        self._assert(
            "summary" in result,
            "抽取结果包含主题概括",
            result.get("summary", "")[:80],
        )
        self._assert(
            "metadata" in result and "total_chunks" in result["metadata"],
            "元数据包含分块信息",
        )

        # 测试2: 知识点字段完整性
        if result["concepts"]:
            c = result["concepts"][0]
            required_fields = ["name", "definition", "category", "difficulty", "keywords"]
            for field in required_fields:
                self._assert(
                    field in c,
                    f"知识点包含{field}字段",
                    str(c.get(field, "MISSING"))[:50],
                )

        # 测试3: 多文件批量抽取
        files = [
            str(PROJECT_ROOT / "data" / "notes" / "python_data_structures.md"),
            str(PROJECT_ROOT / "data" / "notes" / "algorithm_complexity.md"),
        ]
        multi_result = extractor.extract_from_files(files)
        self._assert(
            len(multi_result["concepts"]) > 0,
            "多文件批量抽取",
            f"共抽取 {len(multi_result['concepts'])} 个知识点",
        )
        self._assert(
            multi_result["metadata"]["total_files"] == 2,
            "批量抽取文件计数正确",
        )

    def _test_graph_building(self):
        print("\n📋 [测试模块2] 知识图谱构建")
        print("-" * 50)
        mock_init()

        from graph_builder import GraphBuilder

        builder = GraphBuilder()

        # 使用mock抽取结果构建图谱
        concepts = MOCK_EXTRACTION_RESPONSE["concepts"]
        graph = builder.build(concepts)

        # 测试4: 图谱节点数
        self._assert(
            len(graph["nodes"]) == len(concepts),
            "图谱节点数等于知识点数",
            f"节点: {len(graph['nodes'])}",
        )

        # 测试5: 图谱有边
        self._assert(
            len(graph["edges"]) > 0,
            "知识图谱包含关系边",
            f"边数: {len(graph['edges'])}",
        )

        # 测试6: 关系类型分布
        self._assert(
            "relation_distribution" in graph["stats"],
            "统计信息包含关系分布",
            str(graph["stats"]["relation_distribution"]),
        )

        # 测试7: Mermaid生成
        mermaid_code = builder.generate_mermaid(graph)
        self._assert(
            "flowchart TD" in mermaid_code,
            "Mermaid代码包含正确的图表类型声明",
        )
        self._assert(
            len(mermaid_code) > 100,
            "Mermaid代码长度合理",
            f"长度: {len(mermaid_code)} 字符",
        )

        # 测试8: 可视化生成
        vis_path = str(PROJECT_ROOT / "tests" / "test_graph.png")
        builder.visualize(graph, vis_path)
        self._assert(
            Path(vis_path).exists(),
            "知识图谱可视化图片已生成",
            f"路径: {vis_path}",
        )

    def _test_question_generation(self):
        print("\n📋 [测试模块3] 关联问题生成")
        print("-" * 50)
        mock_init()

        from graph_builder import GraphBuilder
        from question_generator import QuestionGenerator

        # 先构建图谱
        builder = GraphBuilder()
        graph = builder.build(MOCK_EXTRACTION_RESPONSE["concepts"])

        generator = QuestionGenerator()

        # 测试9: 基本问题生成
        result = generator.generate(graph, count=10)
        self._assert(
            len(result["questions"]) > 0,
            "问题生成成功",
            f"生成 {len(result['questions'])} 道题",
        )
        self._assert(
            result["metadata"]["total"] > 0,
            "元数据包含题目总数",
        )

        # 测试10: 题型分布
        types = result["metadata"]["types"]
        self._assert(
            len(types) >= 2,
            "包含多种题型",
            str(types),
        )

        # 测试11: 题目字段完整性
        if result["questions"]:
            q = result["questions"][0]
            required_fields = ["id", "type", "question", "concepts_involved", "difficulty", "answer_hint"]
            for field in required_fields:
                self._assert(
                    field in q,
                    f"题目包含{field}字段",
                    str(q.get(field, "MISSING"))[:50],
                )

        # 测试12: 练习卷生成
        practice = generator.generate_practice_set(graph, easy=3, medium=5, hard=2)
        self._assert(
            len(practice["questions"]) == 10,
            "练习卷题目数正确",
            f"题目: {len(practice['questions'])}, 期望: 10",
        )

        # 测试13: 难度筛选
        easy_only = generator.generate(graph, count=5, difficulty="easy")
        all_easy = all(q.get("difficulty") == "easy" for q in easy_only["questions"])
        self._assert(
            all_easy,
            "难度筛选功能正常",
            f"全部为easy: {all_easy}",
        )

    def _test_learning_path(self):
        print("\n📋 [测试模块4] 学习路径推荐")
        print("-" * 50)
        mock_init()

        from graph_builder import GraphBuilder
        from learning_path import LearningPathRecommender

        builder = GraphBuilder()
        graph = builder.build(MOCK_EXTRACTION_RESPONSE["concepts"])

        recommender = LearningPathRecommender()

        # 测试14: 零基础学习路径
        result = recommender.recommend(graph, mastered=[])
        self._assert(
            len(result["learning_path"]) > 0,
            "零基础推荐学习路径",
            f"共 {len(result['learning_path'])} 步",
        )
        self._assert(
            "overall_plan" in result,
            "包含总体计划",
            str(result.get("overall_plan", {}).get("strategy", ""))[:80],
        )

        # 测试15: 部分掌握的学习路径
        partial = recommender.recommend(graph, mastered=["变量", "时间复杂度"])
        self._assert(
            len(partial["learning_path"]) > 0,
            "部分掌握推荐学习路径",
            f"共 {len(partial['learning_path'])} 步",
        )
        # 已掌握的不能出现在推荐路径中
        path_names = [s.get("concept_name", "") for s in partial["learning_path"]]
        self._assert(
            "变量" not in path_names,
            "已掌握的'变量'不在推荐路径中",
        )

        # 测试16: 目标导向学习路径
        targeted = recommender.recommend(graph, mastered=[], target="字典（Dictionary）")
        self._assert(
            len(targeted["learning_path"]) > 0,
            "目标导向推荐路径",
            f"到达'字典'需要 {len(targeted['learning_path'])} 步",
        )
        # 路径中应包含目标概念
        if targeted["learning_path"]:
            path_names_all = [s.get("concept_name", "") for s in targeted["learning_path"]]
            has_target = any("字典" in name for name in path_names_all)
            self._assert(
                has_target,
                "路径中包含目标概念'字典'",
                f"路径包含的概念: {path_names_all}",
            )

        # 测试17: 步骤属性完整性
        if result["learning_path"]:
            step = result["learning_path"][0]
            required_fields = ["step", "concept_name", "reason", "estimated_time", "study_tips"]
            for field in required_fields:
                self._assert(
                    field in step,
                    f"学习步骤包含{field}字段",
                    str(step.get(field, "MISSING"))[:50],
                )

    def _test_cli_commands(self):
        print("\n📋 [测试模块5] CLI命令行功能")
        print("-" * 50)

        # CLI命令需要在真实LLM环境下运行，此处验证CLI代码路径正确性
        import importlib.util, sys

        cli_path = str(SCRIPTS_DIR / "cli.py")

        # 测试18: CLI模块可导入
        spec = importlib.util.spec_from_file_location("cli_module", cli_path)
        cli_module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(cli_module)
            self._assert(True, "CLI模块可正常导入")
        except Exception as e:
            self._assert(False, "CLI模块可正常导入", str(e))

        # 测试19: CLI模块包含main函数
        self._assert(
            hasattr(cli_module, "main"),
            "CLI模块包含main入口函数",
        )

        # 测试20: 所有子命令处理函数存在
        for cmd in ["cmd_extract", "cmd_build_graph", "cmd_generate_questions", "cmd_recommend_path", "cmd_full_pipeline"]:
            self._assert(
                hasattr(cli_module, cmd),
                f"CLI包含{cmd}处理函数",
            )

        # 测试21: 使用mock_init通过Python API验证完整流水线
        mock_init()
        from knowledge_extractor import KnowledgeExtractor
        from graph_builder import GraphBuilder
        from question_generator import QuestionGenerator
        from learning_path import LearningPathRecommender

        # 模拟完整流水线
        extractor = KnowledgeExtractor()
        test_file = str(PROJECT_ROOT / "data" / "notes" / "python_data_structures.md")
        concepts = extractor.extract_from_file(test_file)
        self._assert(len(concepts["concepts"]) > 0, "API流水线-知识点抽取成功")

        builder = GraphBuilder()
        graph = builder.build(concepts["concepts"])
        self._assert(len(graph["nodes"]) > 0, "API流水线-图谱构建成功")

        generator = QuestionGenerator()
        questions = generator.generate(graph, count=5)
        self._assert(len(questions["questions"]) > 0, "API流水线-问题生成成功")

        recommender = LearningPathRecommender()
        path = recommender.recommend(graph, mastered=[])
        self._assert(len(path["learning_path"]) > 0, "API流水线-路径推荐成功")

    def _test_edge_cases(self):
        print("\n📋 [测试模块6] 边界情况与健壮性")
        print("-" * 50)
        mock_init()

        from knowledge_extractor import KnowledgeExtractor
        from graph_builder import GraphBuilder
        from learning_path import LearningPathRecommender
        from utils import chunk_text

        # 测试23: 空文本处理
        extractor = KnowledgeExtractor()
        result = extractor.extract_from_text("")
        self._assert(
            "concepts" in result,
            "空文本抽取不崩溃",
        )

        # 测试24: 文本分块
        long_paragraph = "这是一个很长的测试段落，包含大量中文内容用于验证文本分块逻辑的正确性。" * 50
        long_text = (long_paragraph + "\n\n") * 20
        chunks = chunk_text(long_text, max_size=1000, overlap=100)
        self._assert(
            len(chunks) > 1,
            f"长文本正确分块: {len(chunks)}个块",
        )
        max_chunk = max(len(c) for c in chunks)
        self._assert(
            max_chunk <= 2000,
            f"每个分块大小合理（最大{max_chunk}字符）",
        )

        # 测试25: 空概念列表
        builder = GraphBuilder()
        try:
            builder.build([])
            self._assert(False, "空概念列表应抛出异常")
        except ValueError:
            self._assert(True, "空概念列表正确抛出ValueError")

        # 测试26: 全部已掌握的情况
        recommender = LearningPathRecommender()
        graph = builder.build(MOCK_EXTRACTION_RESPONSE["concepts"])
        all_names = [c["name"] for c in MOCK_EXTRACTION_RESPONSE["concepts"]]
        all_mastered = recommender.recommend(graph, mastered=all_names)
        self._assert(
            len(all_mastered["learning_path"]) == 0,
            "全部掌握时路径为空",
        )


# ============================================================
# 主入口
# ============================================================
if __name__ == "__main__":
    runner = TestRunner()
    all_passed = runner.run_all()

    # 保存测试结果
    test_log_path = PROJECT_ROOT / "tests" / "test_output.log"
    with open(test_log_path, "w", encoding="utf-8") as f:
        f.write(f"测试时间: {__import__('datetime').datetime.now()}\n")
        f.write(f"测试结果: {runner.passed}通过, {runner.failed}失败\n\n")
        for r in runner.results:
            status = "PASS" if r["passed"] else "FAIL"
            f.write(f"[{status}] {r['test']}\n")
            if r["detail"]:
                f.write(f"  详情: {r['detail']}\n")

    print(f"\n详细日志已保存至: {test_log_path}")
    sys.exit(0 if all_passed else 1)
