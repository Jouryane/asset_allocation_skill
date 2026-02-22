# 用户画像结构化字段说明

## 概述

本文档定义了用户画像解析模块的结构化字段规范，用于将非结构化/半结构化的用户输入转换为标准化的结构化字段，避免大模型解析偏差。

## 核心维度与结构化字段

### 1. 基础属性

| 核心维度 | 结构化字段 | 数据类型 | 取值示例 | 说明 |
|---------|-----------|---------|---------|------|
| 年龄 | age | float | 34.0 | 用户年龄，单位：岁 |
| 风险承受能力 | risk_level | int | 3 | 风险等级（1-5级），1=非常保守，2=保守，3=稳健，4=激进，5=非常激进 |
| 职业生涯阶段 | career_stage | str | "职业生涯稳健期" | 职业阶段：职业生涯起步、职业生涯稳健期、职业生涯中后期 |
| 投资经验 | investment_experience | str | "匮乏" | 投资经验：丰富、一般、匮乏、较少、较多、无 |
| 婚姻状态 | marital_status | str | "已婚" | 婚姻状态：已婚、单身、离异 |

### 2. 财务属性

| 核心维度 | 结构化字段 | 数据类型 | 取值示例 | 说明 |
|---------|-----------|---------|---------|------|
| 年收入 | annual_income | float | 30.0 | 年收入，单位：万元 |
| 月支出 | monthly_expense | float | 1.0 | 月支出，单位：万元 |
| 可投资金额 | total_capital | float | 100.0 | 可投资金额，单位：万元 |
| 负债状态 | debt_status | dict | {"has_debt": False, "debt_amount": 0} | 包含是否有负债和负债金额（万元） |

### 3. 衍生字段

| 结构化字段 | 数据类型 | 取值示例 | 说明 |
|-----------|---------|---------|------|
| work_years | float | 5.0 | 工作年限，单位：年 |

## 字段解析规则

### 年龄解析
- 支持格式：
  - "34岁"
  - "年龄：34"
  - "我今年34岁"
  - "34周岁"
  - "34 years old"

### 年收入解析
- 支持格式：
  - "年收入：30万"
  - "年薪30万"
  - "收入30万"
  - "收入在年30万人民币"
  - "目前收入在年30万"
- 单位自动转换：
  - "万" → 直接使用
  - "元" → 除以10000转换为万元
  - "k" → 除以10000转换为万元

### 月支出解析
- 支持格式：
  - "月支出：1万"
  - "每月开支1万"
  - "月开支在10000人民币"
  - "月开支在10000元"
- 单位自动转换：
  - "万" → 直接使用
  - "元"（数值≥1000）→ 除以10000转换为万元
  - "元"（数值<1000）→ 直接使用（单位：万元）

### 可投资金额解析
- 支持格式：
  - "资金100万"
  - "总资金100万"
  - "可投资金额100万"
  - "可支配金融资产100万"
  - "大约100万"
  - "资金大约是100万人民币"
  - "目前我的资金大约是100万"
- 单位自动转换：同年收入

### 风险偏好解析
- 支持格式：
  - "风险偏好：稳健"
  - "风险承受能力：3级"
  - "风险等级3"
  - "我是稳健型"
- 文本映射到等级：
  - "非常保守" / "低" → 1级
  - "保守" / "低" → 2级
  - "稳健" / "平衡" / "中性" / "中" → 3级
  - "激进" / "高" → 4级
  - "非常激进" → 5级

### 投资经验解析
- 支持格式：
  - "投资经验：匮乏"
  - "投资经验匮乏"
  - "没有投资经验"
  - "投资经验较少"

### 职业生涯阶段解析
- 支持格式：
  - "职业生涯阶段：稳健"
  - "工作年限5年"
- 自动推断：
  - 工作年限≤5年 → 职业生涯起步
  - 5年<工作年限≤15年 → 职业生涯稳健期
  - 工作年限>15年 → 职业生涯中后期

### 婚姻状态解析
- 支持格式：
  - "已婚"
  - "单身"
  - "离异"

### 负债状态解析
- 支持格式：
  - "有负债"
  - "无负债"
  - "没有任何负债"
  - "负债50万"
- 返回结构：
  ```python
  {
    "has_debt": True/False,
    "debt_amount": 50.0  # 单位：万元，无负债时为0
  }
  ```

## 验证规则

### 必填字段
- age（年龄）
- annual_income（年收入）
- total_capital（可投资金额）

### 合理性检查
- 年龄范围：18-80岁
- 资金与收入关系：总资金不应超过年收入的10倍（否则发出警告）

### 可选字段
- monthly_expense（月支出）
- risk_level（风险等级）
- investment_experience（投资经验）
- career_stage（职业生涯阶段）
- marital_status（婚姻状态）
- debt_status（负债状态）

## 转换为strategy.py参数

用户画像解析模块可以将结构化字段转换为strategy.py所需的参数：

```python
# 原始字段（单位：万元）
annual_income: 30.0
total_capital: 100.0
monthly_expense: 1.0

# 转换后参数（单位：元）
annual_income: 300000.0
total_capital: 1000000.0
monthly_expense: 10000.0
```

## 使用示例

### 示例1：完整用户画像
**输入文本：**
```
我是一位34岁的男性、目前收入在年30万人民币，投资经验比较匮乏，主要是进行存款，但现在想要学习一些股票基金投资，已婚，没有任何负债，目前我的资金大约是100万人民币，每月开支在10000人民币左右。
```

**结构化输出：**
```python
{
    "age": 34.0,
    "annual_income": 30.0,
    "monthly_expense": 1.0,
    "total_capital": 100.0,
    "risk_preference": None,
    "risk_level": None,
    "investment_experience": "匮乏",
    "career_stage": None,
    "marital_status": "已婚",
    "debt_status": {"has_debt": False, "debt_amount": 0},
    "work_years": None
}
```

### 示例2：简洁格式
**输入文本：**
```
35岁，年收入50万，月支出8000元，可投资金额100万，风险等级3（稳健型）
```

**结构化输出：**
```python
{
    "age": 35.0,
    "annual_income": 50.0,
    "monthly_expense": 0.8,
    "total_capital": 100.0,
    "risk_preference": "3",
    "risk_level": 3,
    "investment_experience": None,
    "career_stage": None,
    "marital_status": None,
    "debt_status": {"has_debt": False, "debt_amount": 0},
    "work_years": None
}
```

## 进取系数建议表

根据Asset Allocation basic.md中的资产配置思想，结合用户的年龄和风险偏好，提供进取系数建议：

| 职业生涯阶段 | 风险偏好低 | 风险偏好中 | 风险偏好高 |
|-------------|-----------|-----------|-----------|
| 职业生涯起步 | 0.15 | 0.35 | 0.65 |
| 职业生涯稳健期 | 0.25 | 0.50 | 0.80 |
| 职业生涯中后期 | 0.10 | 0.25 | 0.60 |

**说明：**
- 进取系数是指为追求目标配置方案，用户选取进取类资产的投资比例
- 金融知识、投资经验相对匮乏的用户优先关注风险管理项目，选择相对低的进取系数
- 每月盈余状态不佳的用户优先关注流动性管理项目

## 与Asset Allocation basic的衔接

本用户画像解析模块为Asset Allocation basic提供以下支持：

1. **风险管理**：根据age、risk_level、career_stage计算进取系数
2. **流动性管理**：根据monthly_expense计算流动性匹配率
3. **收益率管理**：根据annual_income和历史收益数据计算实际收益率
4. **保障杠杆管理**：根据marital_status、debt_status计算保障杠杆率

## 注意事项

1. **适当性原则**：禁止在用户倾向保守时提出激进的建议
2. **预警机制**：
   - 进取类资产占比 > 用户进取系数 → ⚠️预警
   - 流动性资金 < 三个月月支出 → ⚠️预警
   - 年化收益 < 十年期国债利率 → ⚠️预警
3. **合规性**：Asset Allocation basic仅作为阐述资产配置逻辑的基础，不包含具体的资产配置方案、禁止涉及任何具体产品的推荐

## 代码接口

### 主要类和方法

```python
from user_profile_parser import UserProfileParser, parse_user_profile

# 方式1：使用解析器类
parser = UserProfileParser()
profile = parser.parse_text(user_text)
validation = parser.validate_profile(profile)
strategy_params = parser.export_to_strategy_params(profile)

# 方式2：使用便捷函数
profile, validation = parse_user_profile(user_text)
```

### 返回值说明

**profile（用户画像字典）：**
- 包含所有提取的结构化字段
- 未提取到的字段值为None

**validation（验证结果字典）：**
- `is_valid`: 是否通过验证（bool）
- `missing_fields`: 缺失的必填字段列表
- `warnings`: 警告信息列表
- `suggestions`: 建议信息列表

## 文件结构

```
asset_allocation/
├── user_profile_parser.py          # 用户画像解析模块
├── Asset Allocation basic.md       # 资产配置基础文档
├── strategy.py                     # 策略执行模块
└── user_profile_fields.md          # 本文档
```

## 版本历史

- v1.0 (2025-02-22): 初始版本，支持基础属性和财务属性的结构化解析
