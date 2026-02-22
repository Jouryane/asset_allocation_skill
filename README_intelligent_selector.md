# 智能选品路由器使用指南

## 概述

智能选品路由器（intelligent_selector_router.py）是一个智能决策系统，能够根据用户画像和市场状态，自动选择使用申万一级行业指数（SW_LV1）还是申万二级行业指数（SW_LV2）进行选品。

## 核心思想

### 为什么需要智能路由？

**申万一级行业指数（SW_LV1）**
- 数量：31个行业
- 特点：行业覆盖广，相对稳定
- 适合：中小资金、保守型、投资经验较少的用户
- 优势：容易理解，集中投资，管理简单

**申万二级行业指数（SW_LV2）**
- 数量：131个行业
- 特点：细分领域，机会更多
- 适合：大资金、激进型、投资经验丰富的用户
- 优势：分散投资，机会更多，需要更强的分析能力

### 智能路由的优势

1. **个性化适配**：根据用户画像自动选择最合适的选品器
2. **动态调整**：根据市场状态调整选择策略
3. **透明决策**：提供详细的决策原因和评分对比
4. **灵活配置**：权重可调，适应不同场景

## 评估维度

智能选品路由器从5个维度评估选品器的适用性：

### 1. 资金规模（权重：30%）

| 资金规模 | SW_LV1得分 | SW_LV2得分 | 说明 |
|---------|------------|------------|------|
| <100万 | 90 | 40 | 小资金适合一级行业集中投资 |
| 100-500万 | 80 | 70 | 中等资金两者皆可 |
| ≥500万 | 60 | 95 | 大资金适合二级行业分散投资 |

### 2. 风险偏好（权重：25%）

| 风险等级 | SW_LV1得分 | SW_LV2得分 | 说明 |
|---------|------------|------------|------|
| 保守（1-2级） | 90 | 50 | 一级行业相对稳定 |
| 稳健（3级） | 85 | 80 | 两者皆可 |
| 激进（4-5级） | 60 | 95 | 二级行业机会更多 |

### 3. 投资经验（权重：20%）

| 投资经验 | SW_LV1得分 | SW_LV2得分 | 说明 |
|---------|------------|------------|------|
| 无/匮乏/较少 | 90 | 40 | 一级行业更容易理解 |
| 一般 | 80 | 75 | 两者皆可 |
| 较多/丰富 | 70 | 95 | 二级行业需要更强的分析能力 |

### 4. 市场状态（权重：15%）

| 市场波动率 | SW_LV1得分 | SW_LV2得分 | 说明 |
|-----------|------------|------------|------|
| 低波动 | 75 | 70 | 两者皆可 |
| 中等波动 | 90 | 80 | 一级行业适合震荡市场 |
| 高波动 | 65 | 85 | 二级行业适合趋势市场 |

### 5. 分散化需求（权重：10%）

| 资金规模 | SW_LV1得分 | SW_LV2得分 | 说明 |
|---------|------------|------------|------|
| <200万 | 90 | 50 | 小资金适合集中投资 |
| 200-500万 | 75 | 80 | 中等资金两者皆可 |
| ≥500万 | 60 | 95 | 大资金适合分散投资 |

## 使用方法

### 方式1：直接使用路由器

```python
from intelligent_selector_router import intelligent_select

# 用户画像
user_profile = {
    'age': 34,
    'annual_income': 30,
    'total_capital': 100,
    'monthly_expense': 1,
    'risk_level': 3,
    'investment_experience': '匮乏',
    'career_stage': '职业生涯起步'
}

# 市场状态（可选）
market_state = {
    'volatility': 'medium',  # low/medium/high
    'trend': 'neutral'        # up/down/neutral
}

# 智能选择选品器
selected_type, detail_info = intelligent_select(user_profile, market_state)

# 查看结果
print(f"选中的选品器：{selected_type}")
print(f"综合得分：{detail_info['selected_score']:.1f}/100")
```

### 方式2：使用集成工作流

```python
from intelligent_allocation_workflow import intelligent_allocation_workflow

# 用户画像
user_profile = {
    'age': 34,
    'annual_income': 30,
    'total_capital': 100,
    'monthly_expense': 1,
    'risk_level': 3,
    'investment_experience': '匮乏',
    'career_stage': '职业生涯起步'
}

# 市场状态（可选）
market_state = {
    'volatility': 'medium',
    'trend': 'neutral'
}

# 运行智能资产配置工作流
selected_type, result, routing_info = intelligent_allocation_workflow(
    user_profile=user_profile,
    market_state=market_state,
    auto_visualize=True  # 自动生成可视化图表
)

# 查看结果
print(f"选中的选品器：{selected_type}")
print(f"选品结果：{result}")
print(f"路由决策信息：{routing_info}")
```

### 方式3：命令行执行

```bash
# 运行智能选品路由器（测试模式）
python intelligent_selector_router.py

# 运行智能资产配置工作流（测试模式）
python intelligent_allocation_workflow.py
```

## 决策流程

```
用户画像 + 市场状态
        ↓
智能选品路由器
        ↓
┌───────────────┬───────────────┐
│               │               │
评估SW_LV1     评估SW_LV2     对比得分
│               │               │
└───────────────┴───────────────┘
        ↓
    选择得分更高的选品器
        ↓
┌───────────────┬───────────────┐
│               │               │
SW_LV1得分    SW_LV2得分    决策原因
│               │               │
└───────────────┴───────────────┘
        ↓
    运行相应的选品程序
        ↓
    生成可视化图表
        ↓
    输出最终结果
```

## 输出示例

### 决策结果

```
================================================================================
智能选品路由器决策结果
================================================================================

【决策结果】
  选中选品器：SW_LV1
  综合得分：82.5/100

【决策原因】
选择申万一级行业指数（SW_LV1）
主要考虑因素：资金规模、投资经验
- 资金规模100万元，适合一级行业集中投资
- 风险等级3级，一级行业相对稳定
- 投资经验匮乏，一级行业更容易理解

【详细评分对比】
维度              SW_LV1得分  SW_LV2得分  权重
------------------------------------------------------------
资金规模            80.0       70.0       30.0%
风险偏好            85.0       80.0       25.0%
投资经验            90.0       40.0       20.0%
市场状态            90.0       80.0       15.0%
分散化需求          90.0       50.0       10.0%

【市场状态】
  波动率：medium
  趋势：neutral

【下一步操作】
  1. 运行 etf_selector.py 进行申万一级行业指数筛选
  2. 查看筛选结果和可视化图表
================================================================================
```

## 智能体自发选择条件

### 条件1：用户画像触发

当用户提供完整的用户画像时，智能体自动触发选品路由：

```python
# 用户画像触发条件
user_profile_complete = all([
    user_profile.get('age') is not None,
    user_profile.get('total_capital') is not None,
    user_profile.get('risk_level') is not None
])

if user_profile_complete:
    # 自动触发智能选品路由
    selected_type, detail_info = intelligent_select(user_profile, market_state)
```

### 条件2：市场状态变化

当市场状态发生显著变化时，智能体重新评估选品器选择：

```python
# 市场状态变化触发条件
market_state_changed = (
    abs(current_volatility - previous_volatility) > 0.2 or  # 波动率变化>20%
    current_trend != previous_trend  # 趋势反转
)

if market_state_changed:
    # 重新评估选品器选择
    selected_type, detail_info = intelligent_select(user_profile, market_state)
```

### 条件3：用户画像更新

当用户画像发生显著变化时，智能体重新评估选品器选择：

```python
# 用户画像更新触发条件
profile_changed = (
    abs(current_capital - previous_capital) / previous_capital > 0.2 or  # 资金变化>20%
    current_risk_level != previous_risk_level  # 风险等级变化
)

if profile_changed:
    # 重新评估选品器选择
    selected_type, detail_info = intelligent_select(user_profile, market_state)
```

### 条件4：定期重新评估

智能体定期（如每月）重新评估选品器选择，确保配置的合理性：

```python
# 定期重新评估触发条件
from datetime import datetime, timedelta

last_evaluation_date = get_last_evaluation_date()
current_date = datetime.now()

if current_date - last_evaluation_date >= timedelta(days=30):  # 30天
    # 重新评估选品器选择
    selected_type, detail_info = intelligent_select(user_profile, market_state)
    # 更新评估日期
    update_last_evaluation_date(current_date)
```

## 与其他模块的集成

### 与user_profile_parser集成

```python
from user_profile_parser import parse_user_profile
from intelligent_selector_router import intelligent_select

# 解析用户画像
user_text = "我是一位34岁的男性、目前收入在年30万人民币，投资经验比较匮乏，主要是进行存款，但现在想要学习一些股票基金投资，已婚，没有任何负债，目前我的资金大约是100万人民币，每月开支在10000人民币左右。"

profile, validation = parse_user_profile(user_text)

# 验证画像
if validation['is_valid']:
    # 智能选择选品器
    selected_type, detail_info = intelligent_select(profile, market_state)
else:
    print("用户画像不完整，请补充信息")
```

### 与strategy.py集成

```python
from intelligent_selector_router import intelligent_select
from strategy import main

# 智能选择选品器
selected_type, detail_info = intelligent_select(user_profile, market_state)

# 根据选品器类型调整策略参数
if selected_type == 'sw_lv1':
    # 一级行业：更保守的参数
    aggressiveness = 1.0
    lookback_years = 5
else:  # sw_lv2
    # 二级行业：更激进的参数
    aggressiveness = 1.2
    lookback_years = 3

# 运行策略
result = main(user_profile)
```

### 与Aggressive Asset Allocation strategy集成

```python
from intelligent_selector_router import intelligent_select
from intelligent_allocation_workflow import intelligent_allocation_workflow

# 智能选择选品器并运行完整工作流
selected_type, result, routing_info = intelligent_allocation_workflow(
    user_profile=user_profile,
    market_state=market_state,
    auto_visualize=True
)

# 将结果发送到钉钉
from dingding import DingTalkBot, send_strategy_report_to_dingding

bot = DingTalkBot(MY_ACCESS_TOKEN, MY_SECRET)
dingding_result = send_strategy_report_to_dingding(
    {
        'selector_type': selected_type,
        'selection_result': result,
        'routing_info': routing_info
    },
    bot,
    user_profile
)
```

## 自定义配置

### 调整权重

```python
from intelligent_selector_router import IntelligentSelectorRouter

# 创建路由器实例
router = IntelligentSelectorRouter()

# 自定义权重
router.weights = {
    'capital': 0.4,          # 增加资金规模权重
    'risk_level': 0.2,       # 降低风险偏好权重
    'experience': 0.15,       # 降低投资经验权重
    'market_state': 0.15,      # 保持市场状态权重
    'diversification': 0.1,    # 保持分散化需求权重
}

# 使用自定义权重进行选择
selected_type, detail_info = router.select_best_selector(user_profile, market_state)
```

### 自定义评分规则

```python
from intelligent_selector_router import IntelligentSelectorRouter

# 创建路由器实例
router = IntelligentSelectorRouter()

# 自定义资金规模评分规则
def custom_capital_score(selector_type, user_profile):
    capital = user_profile.get('total_capital', 0)
    
    if selector_type == SelectorType.SW_LV1:
        # 自定义评分逻辑
        if capital < 50:
            return 95
        elif capital < 200:
            return 85
        else:
            return 70
    else:
        # 自定义评分逻辑
        if capital < 100:
            return 30
        elif capital < 300:
            return 80
        else:
            return 100

# 替换默认评分规则
router._evaluate_capital = custom_capital_score

# 使用自定义评分规则进行选择
selected_type, detail_info = router.select_best_selector(user_profile, market_state)
```

## 常见问题

**Q1: 如何强制使用某个选品器？**

A: 可以直接调用相应的选品程序，跳过智能路由：
```python
# 强制使用SW_LV1
from etf_selector import select_best_sw_lv1_indices_by_valuation
result = select_best_sw_lv1_indices_by_valuation()

# 强制使用SW_LV2
from sw_lv2_selector import select_best_sw_lv2_indices_by_valuation
result = select_best_sw_lv2_indices_by_valuation()
```

**Q2: 如何查看详细的评分过程？**

A: 查看detail_info中的sw_lv1_scores和sw_lv2_scores字段：
```python
selected_type, detail_info = intelligent_select(user_profile, market_state)

# 查看SW_LV1的详细评分
print("SW_LV1详细评分：")
for dimension, score in detail_info['sw_lv1_scores'].items():
    print(f"  {dimension}: {score}")

# 查看SW_LV2的详细评分
print("SW_LV2详细评分：")
for dimension, score in detail_info['sw_lv2_scores'].items():
    print(f"  {dimension}: {score}")
```

**Q3: 如何调整市场状态的判断逻辑？**

A: 可以在market_state中提供更详细的信息，或者自定义市场状态评分规则：
```python
# 提供更详细的市场状态
market_state = {
    'volatility': 'medium',
    'trend': 'neutral',
    'valuation_level': 'medium',  # 新增：估值水平
    'sentiment': 'neutral'         # 新增：市场情绪
}

# 自定义市场状态评分规则
def custom_market_state_score(selector_type, market_state):
    # 自定义评分逻辑
    pass

router._evaluate_market_state = custom_market_state_score
```

**Q4: 如何在智能体中集成？**

A: 在智能体的主流程中添加智能选品路由：
```python
# 智能体主流程
def agent_main(user_input):
    # 步骤1：解析用户画像
    profile, validation = parse_user_profile(user_input)
    
    # 步骤2：智能选择选品器
    selected_type, detail_info = intelligent_select(profile, market_state)
    
    # 步骤3：运行选品程序
    if selected_type == 'sw_lv1':
        result = run_sw_lv1_selector(profile)
    else:
        result = run_sw_lv2_selector(profile)
    
    # 步骤4：生成可视化
    run_visualization(selected_type, result)
    
    # 步骤5：发送结果
    send_result_to_dingding(result)
    
    return result
```

## 文件结构

```
asset_allocation/
├── intelligent_selector_router.py      # 智能选品路由器核心模块
├── intelligent_allocation_workflow.py  # 智能资产配置工作流
├── README_intelligent_selector.md     # 本文档
├── etf_selector.py                # 申万一级行业指数选品程序
├── sw_lv2_selector.py             # 申万二级行业指数选品程序
├── draw.py                        # SW_LV1可视化程序
└── draw_lv2.py                    # SW_LV2可视化程序
```

## 版本历史

- v1.0 (2025-02-22): 初始版本
  - 实现智能选品路由器
  - 支持5个评估维度
  - 提供详细的决策原因和评分对比
  - 集成工作流和可视化
