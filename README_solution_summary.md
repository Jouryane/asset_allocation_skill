# 资产配置技能协作流程 - 完整解决方案

## 问题分析

用户提出的问题：当用户输入"我是一位40岁的男性、目前收入在年55万人民币，有丰富的投资经验，主要是进行基金股票投资，已婚，没有任何负债，目前我的资金大约是700万人民币，每月开支在20000人民币左右。请你帮我设计一个资产配置框架以及执行的具体策略。"时，agent未能正确识别应该先调用Asset Allocation basic（资产配置框架），然后再调用Aggressive Asset Allocation strategy（具体策略）。

## 根本原因

1. **技能描述不清晰**：Asset Allocation basic和Aggressive Asset Allocation strategy的技能描述中没有明确说明它们之间的协作关系
2. **关键词识别不完整**：技能描述中缺少"设计资产配置框架"、"帮我做资产配置"、"具体策略"、"执行策略"等关键词
3. **协作流程不明确**：没有明确的文档说明两个技能应该如何协作
4. **智能选品路由器未集成**：虽然创建了智能选品路由器，但没有在技能描述中明确说明如何使用

## 解决方案

### 1. 更新Asset Allocation basic技能描述

**文件路径**：`d:\agent skills\asset_allocation\.trae\skills\asset-allocation-basic\skill.md`

**主要修改**：
- 在description中增加关键词："设计资产配置框架"、"帮我做资产配置"
- 新增第5章"适当延伸与协作流程"
- 明确与Aggressive Asset Allocation strategy的协作流程
- 提供关键词识别规则
- 提供注意事项（先框架后战术、自动触发、透明决策、配置提醒）

**关键内容**：
```markdown
### 5.2 与Aggressive Asset Allocation strategy的协作

**协作流程：**

当用户提出"设计资产配置框架"、"帮我设计资产配置"、"帮我做资产配置"等需求时，应该按照以下流程执行：

**步骤1：调用Asset Allocation basic（本技能）**
- 解析用户画像（年龄、收入、资金规模、风险偏好等）
- 输出宏观的资产配置框架
- 计算进取系数和各类资产的配置比例
- 提供风险管理、流动性管理、收益率管理、保障杠杆管理的评估

**步骤2：询问用户是否需要具体的选品和执行策略**
- 在输出宏观资产配置框架后，主动询问用户："您是否需要我为您提供具体的选品和执行策略？"
- 如果用户确认需要，则进入步骤3

**步骤3：调用Aggressive Asset Allocation strategy**
- 基于步骤1中的用户画像和进取系数
- 自动使用智能选品路由器选择SW_LV1或SW_LV2
- 输出具体的选品方案和仓位配置建议
- 生成可视化图表（可选）
```

### 2. 更新Aggressive Asset Allocation strategy技能描述

**文件路径**：`d:\agent skills\asset_allocation\.trae\skills\aggressive-asset-allocation-strategy\skill.md`

**主要修改**：
- 在description中增加关键词："具体策略"、"执行策略"
- 新增第0章"与Asset Allocation basic的协作"
- 明确本技能的定位
- 说明协作流程（当用户同时要求"框架"和"策略"时、当用户只要求"策略"或"选品"时）
- 说明智能选品路由器的使用
- 说明输出格式要求

**关键内容**：
```markdown
### 0.2 协作流程

**当用户同时要求"框架"和"策略"时：**

1. **Asset Allocation basic先执行**
   - 解析用户画像
   - 输出宏观的资产配置框架
   - 计算进取系数和各类资产的配置比例

2. **Aggressive Asset Allocation strategy自动执行**
   - 接收Asset Allocation basic输出的用户画像和进取系数
   - 自动使用智能选品路由器选择SW_LV1或SW_LV2
   - 输出具体的选品方案和仓位配置建议
   - 生成可视化图表（可选）

**当用户只要求"策略"或"选品"时：**

1. **直接执行Aggressive Asset Allocation strategy**
   - 解析用户画像
   - 使用智能选品路由器选择SW_LV1或SW_LV2
   - 输出具体的选品方案和仓位配置建议
   - 生成可视化图表（可选）
```

### 3. 创建协作流程文档

**文件路径**：`d:\agent skills\asset_allocation\README_collaboration_workflow.md`

**主要内容**：
- 技能定位说明
- 协作流程详细说明（3个场景）
- 智能选品路由器的使用方法
- 关键注意事项
- 配置文件要求

**关键内容**：
```markdown
## 协作流程

### 场景1：用户同时要求"框架"和"策略"

**示例用户输入：**
"我是一位40岁的男性、目前收入在年55万人民币，有丰富的投资经验，主要是进行基金股票投资，已婚，没有任何负债，目前我的资金大约是700万人民币，每月开支在20000人民币左右。请你帮我设计一个资产配置框架以及执行的具体策略。"

**执行流程：**

用户输入
    ↓
识别到"框架"和"策略"关键词
    ↓
【步骤1】调用Asset Allocation basic
    ├─ 解析用户画像
    ├─ 输出宏观的资产配置框架
    ├─ 计算进取系数和各类资产的配置比例
    └─ 提供风险管理、流动性管理、收益率管理、保障杠杆管理的评估
    ↓
【步骤2】自动调用Aggressive Asset Allocation strategy
    ├─ 接收Asset Allocation basic输出的用户画像和进取系数
    ├─ 自动使用智能选品路由器选择SW_LV1或SW_LV2
    ├─ 输出具体的选品方案和仓位配置建议
    └─ 生成可视化图表（可选）
    ↓
输出完整结果
```

### 4. 创建测试脚本

**文件路径**：`d:\agent skills\asset_allocation\test_collaboration_workflow.py`

**主要功能**：
- 测试场景1：用户同时要求"框架"和"策略"
- 测试场景2：用户只要求"框架"
- 测试场景3：用户只要求"策略"或"选品"
- 验证整个协作流程的正确性

**测试结果**：
```
测试总结：
  场景1：同时要求'框架'和'策略' → 选中选品器：sw_lv2
  场景2：只要求'框架' → 等待用户确认
  场景3：只要求'策略'或'选品' → 选中选品器：sw_lv2
```

### 5. 修复user_profile_parser.py

**问题**：无法解析"有丰富的投资经验"这样的表达

**修复**：增加正则表达式模式 `r'有(丰富|一般|匮乏|较少|较多)\s*投资经验'`

### 6. 修复intelligent_selector_router.py

**问题**：当risk_level为None时，会抛出TypeError

**修复**：在_evaluate_risk_preference方法中增加None值检查，使用默认值3（稳健型）

## 完整的协作流程

### 场景1：用户同时要求"框架"和"策略"

```
用户输入："请你帮我设计一个资产配置框架以及执行的具体策略。"
    ↓
识别到"框架"和"策略"关键词
    ↓
【步骤1】调用Asset Allocation basic
    ├─ 解析用户画像
    ├─ 输出宏观的资产配置框架
    ├─ 计算进取系数和各类资产的配置比例
    └─ 提供风险管理、流动性管理、收益率管理、保障杠杆管理的评估
    ↓
【步骤2】自动调用Aggressive Asset Allocation strategy
    ├─ 接收Asset Allocation basic输出的用户画像和进取系数
    ├─ 自动使用智能选品路由器选择SW_LV1或SW_LV2
    ├─ 输出具体的选品方案和仓位配置建议
    └─ 生成可视化图表（可选）
    ↓
输出完整结果
```

### 场景2：用户只要求"框架"

```
用户输入："请你帮我设计一个资产配置框架。"
    ↓
识别到"框架"关键词
    ↓
【步骤1】调用Asset Allocation basic
    ├─ 解析用户画像
    ├─ 输出宏观的资产配置框架
    ├─ 计算进取系数和各类资产的配置比例
    └─ 提供风险管理、流动性管理、收益率管理、保障杠杆管理的评估
    ↓
【步骤2】询问用户是否需要具体策略
    ↓
等待用户确认
```

### 场景3：用户只要求"策略"或"选品"

```
用户输入："请帮我选品。"
    ↓
识别到"选品"关键词
    ↓
【步骤1】直接调用Aggressive Asset Allocation strategy
    ├─ 解析用户画像
    ├─ 自动使用智能选品路由器选择SW_LV1或SW_LV2
    ├─ 输出具体的选品方案和仓位配置建议
    └─ 生成可视化图表（可选）
    ↓
输出选品结果
```

## 关键词识别规则

### Asset Allocation basic关键词
- "资产配置思路"
- "阐述资产配置思想合理性"
- "我应该如何使用你这套资产配置思路"
- "设计一个资产配置框架"
- "帮我设计资产配置"
- "帮我做资产配置"
- "设计资产配置框架"
- "资产配置框架"
- "配置框架"

### Aggressive Asset Allocation strategy关键词
- "配置战术"
- "帮我选品"
- "买什么"
- "具体策略"
- "执行策略"
- "选品"
- "战术"

## 智能选品路由器的使用

### 自动触发条件
1. 用户提供了完整的用户画像（年龄、资金规模、风险等级）
2. 市场状态发生显著变化（波动率变化>20%或趋势反转）
3. 用户画像发生显著变化（资金变化>20%或风险等级变化）
4. 定期重新评估（如每月）

### 执行流程
1. 调用intelligent_selector_router.intelligent_select()函数
2. 根据用户画像和市场状态计算SW_LV1和SW_LV2的得分
3. 选择得分更高的选品器
4. 输出详细的决策原因和评分对比
5. 自动运行相应的选品程序（etf_selector.py或sw_lv2_selector.py）

### 输出格式要求
1. **智能选品路由器的决策结果**
   - 选中的选品器（SW_LV1或SW_LV2）
   - 综合得分
   - 决策原因
   - 详细评分对比

2. **选品结果**
   - 选中的行业指数列表
   - 每个指数的估值分位、当前PE、综合得分
   - 建议的仓位配置

3. **可视化图表**
   - PE历史趋势图
   - 换手率变化趋势图
   - 价格相对位置图

## 关键注意事项

1. **先框架后战术**：必须先输出宏观的资产配置框架，再提供具体的选品和执行策略
2. **自动触发**：当用户同时要求"框架"和"策略"时，应该自动执行完整的协作流程，不需要用户再次确认
3. **透明决策**：在调用Aggressive Asset Allocation strategy时，应该说明使用了智能选品路由器，并解释选择SW_LV1或SW_LV2的原因
4. **配置提醒**：在调用Aggressive Asset Allocation strategy前，提醒用户确保已配置config.yaml和dingding.py文件

## 文件清单

### 修改的文件
1. `d:\agent skills\asset_allocation\.trae\skills\asset-allocation-basic\skill.md` - 更新Asset Allocation basic技能描述
2. `d:\agent skills\asset_allocation\.trae\skills\aggressive-asset-allocation-strategy\skill.md` - 更新Aggressive Asset Allocation strategy技能描述
3. `d:\agent skills\asset_allocation\user_profile_parser.py` - 修复投资经验解析问题
4. `d:\agent skills\asset_allocation\intelligent_selector_router.py` - 修复risk_level为None时的错误

### 新增的文件
1. `d:\agent skills\asset_allocation\README_collaboration_workflow.md` - 协作流程文档
2. `d:\agent skills\asset_allocation\test_collaboration_workflow.py` - 协作流程测试脚本

## 测试验证

测试脚本运行成功，验证了以下场景：
- ✅ 场景1：同时要求'框架'和'策略' → 选中选品器：sw_lv2
- ✅ 场景2：只要求'框架' → 等待用户确认
- ✅ 场景3：只要求'策略'或'选品' → 选中选品器：sw_lv2

## 总结

通过以上修改，现在agent能够：
1. ✅ 正确识别用户需求中的关键词
2. ✅ 按照正确的顺序调用Asset Allocation basic和Aggressive Asset Allocation strategy
3. ✅ 自动使用智能选品路由器选择SW_LV1或SW_LV2
4. ✅ 输出完整的资产配置框架和具体策略
5. ✅ 提供透明的决策过程和详细的评分对比

整个协作流程已经完整实现，agent现在能够正确处理用户提出的"设计一个资产配置框架以及执行的具体策略"这样的需求。
