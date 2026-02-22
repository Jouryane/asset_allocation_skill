---
name: Aggressive Asset Allocation strategy
description: 在本agent技能中执行资产配置进取类资产战术的一环，负责处理"选什么去买"、"买多少"等问题。当用户输入"配置战术"、"帮我选品"、"买什么"或类似需要提供资产配置进取类资产战术的场景时触发。根据用户画像和当前市场估值，采用非线性两步法ETF投资策略，结合加权百分位和分位数压缩法提供仓位配置建议，输出可直接用于交易决策的战术方案。完成后可以将方案配置到钉钉机器人进行播报。
---

## Aggressive Asset Allocation strategy

## 1. 概述
Aggressive Asset Allocation strategy技能核心目标是基于用户画像（年龄、风险偏好、资金规模等）和当前市场估值状况，采用非线性两步法ETF投资策略完成「宏观仓位控制→标的筛选与权重分配→结果推送」全流程，避免AI依赖预训练的资产配置方案，而是根据市场实时估值，完全通过执行自定义脚本逻辑输出符合市场状态的配置建议。

**核心特点：**
- 非线性仓位映射：使用Sigmoid/幂函数/自定义函数处理估值分位到仓位的映射
- 加权百分位计算：使用衰减因子削弱极端行情的干扰
- 分位数压缩：通过缩尾处理削弱极端值的影响
- 适当性原则：根据用户风险等级和职业生涯阶段调整进取系数

## 2. 核心依赖文件说明

| 文件名称 | 核心作用 | 调用方式 |
|---------|---------|---------|
| config.yaml | 定义资产配置核心思想（如进取系数矩阵、ETF映射、钉钉配置等） | 作为基础配置模块被导入 |
| user_profile_parser.py | 解析用户画像，将非结构化输入转换为结构化字段 | 调用parse_user_profile()函数 |
| intelligent_selector_router.py | 智能选择选品器（SW_LV1或SW_LV2） | 调用intelligent_select()函数 |
| etf_selector.py | 申万一级行业指数选品程序 | 调用select_best_sw_lv1_indices_by_valuation()函数 |
| sw_lv2_selector.py | 申万二级行业指数选品程序 | 调用select_best_sw_lv2_indices_by_valuation()函数 |
| strategy.py | 基于非线性两步法ETF投资策略，结合市场估值制定具体仓位配置 | 调用NonlinearTwoStepInvestmentStrategy类 |
| dingding.py | 将最终资产配置建议格式化并推送至指定钉钉群/个人 | 调用DingTalkBot类 |

## 3. 核心执行逻辑

### 3.1 环境与模块导入

```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import akshare as ak
import yaml
import sys
import os
import argparse

from user_profile_parser import UserProfileParser, parse_user_profile
from dingding import DingTalkBot, send_strategy_report_to_dingding
```

### 3.2 非线性两步法ETF投资策略

**策略核心思想：**

估值分位 vs 仓位的关系：
- 0% 估值 → 100% 仓位（极端低估，满仓）
- 50% 估值 → 50% 仓位（正常估值，半仓）
- 100% 估值 → 0% 仓位（极端高估，空仓）

**第一步：宏观仓位控制**
- 使用加权百分位计算全市场估值水平
- 通过非线性函数（Sigmoid/幂函数/自定义）映射到仓位
- 考虑衰减因子削弱极端行情干扰

**第二步：标的筛选与权重分配**
- 选择性价比最高的ETF标的
- 使用非线性权重分配，避免中庸配置
- 结合用户风险偏好调整最终配置

### 3.3 资产配置主函数

```python
def main(user_info=None):
    """
    主函数
    
    :param user_info: 用户信息字典，包含age, annual_income, total_capital, monthly_expense等
    """
    # 步骤1：解析用户信息
    # 支持命令行参数或直接传入user_info字典
    parser = argparse.ArgumentParser(description='非线性两步法ETF投资策略')
    parser.add_argument('--age', type=int, help='用户年龄')
    parser.add_argument('--annual_income', type=float, help='年收入')
    parser.add_argument('--total_capital', type=float, help='总资金')
    parser.add_argument('--monthly_expense', type=float, help='月开支')
    parser.add_argument('--risk_level', type=str, help='风险偏好')
    parser.add_argument('--investment_experience', type=str, help='投资经验')
    parser.add_argument('--career_stage', type=str, help='职业生涯阶段')
    
    args = parser.parse_args()
    
    # 合并命令行参数和user_info
    if args.age is not None or args.annual_income is not None or args.total_capital is not None:
        if user_info is None:
            user_info = {}
        if args.age is not None:
            user_info['age'] = args.age
        if args.annual_income is not None:
            user_info['annual_income'] = args.annual_income
        if args.total_capital is not None:
            user_info['total_capital'] = args.total_capital
        if args.monthly_expense is not None:
            user_info['monthly_expense'] = args.monthly_expense
        if args.risk_level is not None:
            user_info['risk_level'] = args.risk_level
        if args.investment_experience is not None:
            user_info['investment_experience'] = args.investment_experience
        if args.career_stage is not None:
            user_info['career_stage'] = args.career_stage
    
    # 步骤2：根据用户画像计算进取系数
    # 加载配置文件
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    appropriateness_matrix = config.get('appropriateness_matrix', {})
    
    # 根据年龄推断职业生涯阶段
    age = user_info.get('age', 40)
    if age < 35:
        career_stage = '职业生涯起步'
    elif age < 50:
        career_stage = '职业生涯稳健期'
    else:
        career_stage = '职业生涯中后期'
    
    # 根据风险偏好映射到配置中的键
    risk_preference = user_info.get('risk_level', '进取')
    risk_mapping = {
        '保守': '低',
        '稳健': '中',
        '进取': '高',
        '激进': '高'
    }
    risk_key = risk_mapping.get(risk_preference, '高')
    
    # 获取进取类投资比例
    stage_config = appropriateness_matrix.get(career_stage, {})
    aggressive_ratio = stage_config.get(risk_key, 0.8)
    
    # 计算进取类投资资金
    total_capital = user_info.get('total_capital', 7000000)
    aggressive_capital = int(total_capital * aggressive_ratio)
    
    # 步骤3：创建策略实例
    strategy = NonlinearTwoStepInvestmentStrategy(
        total_capital=aggressive_capital,  # 使用进取类投资资金
        lookback_years=5,
        rebalance_freq='Q',
        nonlinear_type='sigmoid',  # 可以选择 'sigmoid', 'power', 'custom'
        aggressiveness=1.2,  # 激进程度
        lambda_decay=0.95,  # 衰减因子
        winsorize_pct=0.05  # 缩尾比例5%
    )
    
    # 步骤4：加载ETF数据
    etf_codes = ["510050", "510880", "516950"]  # 配置文件中的ETF
    strategy.load_etf_data(etf_codes)
    
    # 步骤5：运行策略
    result = strategy.run_strategy()
    
    # 步骤6：保存结果
    df_plan = pd.DataFrame(result['investment_plan'])
    df_plan.to_csv('nonlinear_investment_plan.csv', index=False, encoding='utf-8-sig')
    
    # 步骤7：发送到钉钉机器人
    bot = DingTalkBot(MY_ACCESS_TOKEN, MY_SECRET)
    dingding_result = send_strategy_report_to_dingding(result, bot, user_info)
    
    return result
```

### 3.4 执行入口

```python
if __name__ == "__main__":
    # 方式1：使用命令行参数
    # python strategy.py --age 34 --annual_income 300000 --total_capital 1000000 --monthly_expense 10000
    
    # 方式2：直接传入user_info字典
    user_info = {
        'age': 34,
        'annual_income': 300000,
        'total_capital': 1000000,
        'monthly_expense': 10000,
        'risk_level': '稳健',
        'investment_experience': '匮乏',
        'career_stage': '职业生涯起步'
    }
    
    result = main(user_info)
```

## 4. 关键注意事项

### 4.1 数据源适配
- 使用AKshare获取实时市场估值数据
- 确保数据实时性，避免使用静态预训练数据
- ETF到指数的映射需在config.yaml中配置

### 4.2 风险偏好映射
- config.yaml中的appropriateness_matrix需根据用户风险等级（保守/稳健/激进）精准调整标的权重
- 避免固定化配置，根据用户画像动态调整

### 4.3 适当性原则
- 禁止在用户倾向保守时提出激进的建议
- 进取系数不应超过用户风险等级对应的建议值
- 金融知识、投资经验相对匮乏的用户优先关注风险管理项目

### 4.4 异常处理
- 实际部署需补充更多异常捕获逻辑（如数据源失效、标的代码错误、推送失败等）
- 保证脚本鲁棒性

### 4.5 禁止预训练逻辑替代
- 本技能所有配置建议均通过执行上述代码片段生成
- 禁止AI基于预训练知识直接输出资产配置方案
- 需严格调用脚本并返回执行结果

## 5. 输出格式规范

### 5.1 控制台输出格式

```
================================================================================
非线性两步法ETF投资策略报告
================================================================================
报告时间: 2025-02-22 10:30:00
总资金: ¥1,000,000
非线性类型: sigmoid
激进系数: 1.2
衰减因子(λ): 0.95
缩尾比例: 5.0%
--------------------------------------------------------------------------------

【第一步】宏观仓位分析（使用加权百分位）
全市场估值分位: 35.5%
市场信号: 低估💎
建议仓位: 70.0%
可用资金: ¥700,000
闲置资金: ¥300,000 (可放入货币基金)

【第二步】标的筛选与权重分配
性价比最高的3个ETF:
  1. 红利ETF
     - 估值分位: 25.3%
     - 当前PE: 6.85
     - 综合得分: 74.7

【投资计划】
----------------------------------------------------------------------------------------------------
ETF名称         估值分位   风险等级      权重      投资金额        预估份额
----------------------------------------------------------------------------------------------------
红利ETF         25.3%     较低风险💎   60.0%     ¥420,000       61314
上证50ETF       45.2%     中等风险⚖️   30.0%     ¥210,000       4194
碳中和ETF       55.8%     较高风险⚠️   10.0%     ¥70,000        1234
----------------------------------------------------------------------------------------------------
```

### 5.2 钉钉推送格式

```
【非线性两步法ETF投资策略报告】

📊 宏观仓位分析
- 全市场估值分位: 35.5%
- 市场信号: 低估💎
- 建议仓位: 70.0%
- 可用资金: ¥700,000
- 闲置资金: ¥300,000 (可放入货币基金)

💎 标的筛选与权重分配
1. 红利ETF (510880)
   - 估值分位: 25.3%
   - 风险等级: 较低风险💎
   - 配置权重: 60.0%
   - 投资金额: ¥420,000
   - 预估份额: 61,314

2. 上证50ETF (510050)
   - 估值分位: 45.2%
   - 风险等级: 中等风险⚖️
   - 配置权重: 30.0%
   - 投资金额: ¥210,000
   - 预估份额: 4,194

3. 碳中和ETF (516950)
   - 估值分位: 55.8%
   - 风险等级: 较高风险⚠️
   - 配置权重: 10.0%
   - 投资金额: ¥70,000
   - 预估份额: 1,234

📈 资金效率分析
- 实际投资金额: ¥700,000
- 资金使用率: 70.0%
- 建议货币基金配置: ¥300,000

⏰ 报告时间: 2025-02-22 10:30:00
```

## 6. 与用户画像的集成

### 6.1 使用user_profile_parser解析用户输入

```python
from user_profile_parser import parse_user_profile

# 用户输入文本
user_text = "我是一位34岁的男性、目前收入在年30万人民币，投资经验比较匮乏，主要是进行存款，但现在想要学习一些股票基金投资，已婚，没有任何负债，目前我的资金大约是100万人民币，每月开支在10000人民币左右。"

# 解析用户画像
profile, validation = parse_user_profile(user_text)

# 验证画像
if not validation['is_valid']:
    print("缺失字段：", validation['missing_fields'])
    return

# 转换为strategy.py参数
parser = UserProfileParser()
strategy_params = parser.export_to_strategy_params(profile)

# 执行策略
result = main(strategy_params)
```

### 6.2 进取系数计算

根据Asset Allocation basic中的进取系数建议表：

| 职业生涯阶段 | 风险偏好低 | 风险偏好中 | 风险偏好高 |
|-------------|-----------|-----------|-----------|
| 职业生涯起步 | 0.15 | 0.35 | 0.65 |
| 职业生涯稳健期 | 0.25 | 0.50 | 0.80 |
| 职业生涯中后期 | 0.10 | 0.25 | 0.60 |

**计算示例：**
- 用户年龄：34岁 → 职业生涯起步
- 风险偏好：稳健 → 中等风险
- 进取系数：0.35
- 总资金：100万 → 进取类投资资金：35万

## 7. 配置文件说明

### 7.1 config.yaml结构

```yaml
# 进取系数矩阵
appropriateness_matrix:
  职业生涯起步: {低: 0.15, 中: 0.35, 高: 0.65}
  职业生涯稳健期: {低: 0.25, 中: 0.5, 高: 0.8}
  职业生涯中后期: {低: 0.1, 中: 0.25, 高: 0.6}

# 钉钉机器人配置
MY_ACCESS_TOKEN: "your_access_token"
MY_SECRET: "your_secret"

# ETF映射（在strategy.py中定义）
etf_to_index:
  "510050": "000016"  # 上证50ETF → 上证50指数
  "510880": "000015"  # 红利ETF → 红利指数
  "516950": "930608"   # 碳中和ETF → 中证芯片
```

## 7. 智能选品路由器

### 7.1 概述

智能选品路由器（intelligent_selector_router.py）是一个智能决策系统，能够根据用户画像和市场状态，自动选择使用申万一级行业指数（SW_LV1）还是申万二级行业指数（SW_LV2）进行选品。

**核心优势：**
- 个性化适配：根据用户画像自动选择最合适的选品器
- 动态调整：根据市场状态调整选择策略
- 透明决策：提供详细的决策原因和评分对比
- 灵活配置：权重可调，适应不同场景

### 7.2 评估维度

智能选品路由器从5个维度评估选品器的适用性：

| 维度 | 权重 | 说明 |
|------|------|------|
| 资金规模 | 30% | 小资金适合一级行业，大资金适合二级行业 |
| 风险偏好 | 25% | 保守型适合一级行业，激进型适合二级行业 |
| 投资经验 | 20% | 经验少适合一级行业，经验多适合二级行业 |
| 市场状态 | 15% | 震荡市场适合一级行业，趋势市场适合二级行业 |
| 分散化需求 | 10% | 小资金适合集中投资，大资金适合分散投资 |

### 7.3 使用方法

#### 方式1：直接使用路由器

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

#### 方式2：使用集成工作流

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

#### 方式3：与strategy.py集成

```python
from user_profile_parser import parse_user_profile
from intelligent_selector_router import intelligent_select
from strategy import main

# 步骤1：解析用户画像
user_text = "我是一位34岁的男性、目前收入在年30万人民币，投资经验比较匮乏，主要是进行存款，但现在想要学习一些股票基金投资，已婚，没有任何负债，目前我的资金大约是100万人民币，每月开支在10000人民币左右。"

profile, validation = parse_user_profile(user_text)

if not validation['is_valid']:
    print("用户画像不完整，请补充信息")
    return

# 步骤2：智能选择选品器
market_state = {
    'volatility': 'medium',
    'trend': 'neutral'
}

selected_type, routing_info = intelligent_select(profile, market_state)

# 步骤3：根据选品器类型调整策略参数
if selected_type == 'sw_lv1':
    # 一级行业：更保守的参数
    aggressiveness = 1.0
    lookback_years = 5
else:  # sw_lv2
    # 二级行业：更激进的参数
    aggressiveness = 1.2
    lookback_years = 3

# 步骤4：运行策略
result = main(profile)

# 步骤5：输出结果
print(f"使用的选品器：{selected_type}")
print(f"路由决策得分：{routing_info['selected_score']:.1f}/100")
print(f"策略结果：{result}")
```

### 7.4 智能体自发选择条件

#### 条件1：用户画像触发
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

#### 条件2：市场状态变化
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

#### 条件3：用户画像更新
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

#### 条件4：定期重新评估
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

### 7.5 决策输出示例

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

### 7.6 自定义配置

#### 调整权重

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

#### 自定义评分规则

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

### 7.7 与其他模块的集成

#### 与user_profile_parser集成

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

#### 与dingding集成

```python
from intelligent_selector_router import intelligent_select
from intelligent_allocation_workflow import intelligent_allocation_workflow
from dingding import DingTalkBot, send_strategy_report_to_dingding

# 智能选择选品器并运行完整工作流
selected_type, result, routing_info = intelligent_allocation_workflow(
    user_profile=user_profile,
    market_state=market_state,
    auto_visualize=True
)

# 将结果发送到钉钉
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

### 7.8 常见问题

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

## 8. 使用示例

### 8.1 命令行执行

```bash
# 基本用法
python strategy.py --age 34 --annual_income 300000 --total_capital 1000000 --monthly_expense 10000

# 指定风险偏好
python strategy.py --age 34 --annual_income 300000 --total_capital 1000000 --monthly_expense 10000 --risk_level 稳健

# 指定所有参数
python strategy.py --age 34 --annual_income 300000 --total_capital 1000000 --monthly_expense 10000 --risk_level 稳健 --investment_experience 匮乏 --career_stage 职业生涯起步
```

### 8.2 Python脚本调用

```python
from strategy import main

# 方式1：直接传入user_info
user_info = {
    'age': 34,
    'annual_income': 300000,
    'total_capital': 1000000,
    'monthly_expense': 10000,
    'risk_level': '稳健'
}
result = main(user_info)

# 方式2：先解析用户画像，再执行策略
from user_profile_parser import parse_user_profile
user_text = "34岁，年收入30万，资金100万，月支出1万"
profile, validation = parse_user_profile(user_text)
result = main(profile)
```

## 9. 技术细节

### 9.1 加权百分位计算

公式：p_final = Σ(λ^(T-t) * I(winsorize(x_t) < winsorize(x_current))) / Σ(λ^(T-t))

其中：
- λ：衰减因子（lambda_decay），通常取0.9-0.99
- T：历史数据总期数
- t：时间索引（t=1表示最早，t=T表示当前）
- I(·)：指示函数，条件为真时为1，否则为0
- winsorize(·)：缩尾处理函数

### 9.2 非线性仓位映射

**Sigmoid函数：**
position = 1 / (1 + exp(k * (x - 0.5)))

**幂函数：**
position = (1 - x) ^ power

**自定义函数：**
通过关键点线性插值：
- 估值分位: 0%, 20%, 50%, 80%, 100%
- 对应仓位: 100%, 90%, 50%, 20%, 0%

### 9.3 非线性权重分配

使用指数函数放大估值差异：
factor = ((100 - p) / 50) ^ 2

例如：
- p=20 → factor=4
- p=50 → factor=1
- p=80 → factor=0.25

## 10. 常见问题

**Q1: 如何修改ETF标的池？**

A: 在strategy.py的main()函数中修改etf_codes列表，并在etf_to_index字典中添加对应的指数映射。

**Q2: 如何调整激进程度？**

A: 修改NonlinearTwoStepInvestmentStrategy的aggressiveness参数：
- >1: 更激进
- <1: 更保守

**Q3: 如何更换非线性函数类型？**

A: 修改nonlinear_type参数，可选值：'sigmoid', 'power', 'custom'

**Q4: 如何不发送到钉钉？**

A: 注释掉main()函数中的钉钉发送部分代码。

## 11. 版本历史

- v2.0 (2025-02-22): 更新文档以匹配实际实现
  - 修正依赖文件说明
  - 更新核心执行逻辑
  - 添加用户画像集成说明
  - 完善配置文件说明

- v1.0: 初始版本
