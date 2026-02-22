# 确保模型调用脚本 - 完整解决方案总结

## 📋 问题总结

**问题描述**：模型直接给出投资建议而不是调用脚本，违反了设计原则。

**根本原因**：
1. 技能描述中的约束不够强烈
2. 模型倾向于使用预训练知识而不是调用脚本
3. 缺少明确的执行步骤和验证机制

## ✅ 解决方案

### 1. 强化技能描述中的约束

#### 使用强烈的约束语言

在技能描述中使用以下强烈语言：
- **绝对禁止**：基于预训练知识直接输出投资建议
- **必须**：调用特定函数
- **禁止**：修改或杜撰选品结果

#### 使用emoji和格式化突出重要约束

```markdown
## ⚠️ 重要约束（必须遵守）

### 禁止预训练逻辑替代
1. **绝对禁止**基于预训练知识直接输出投资建议
2. **必须**调用intelligent_selector_router.intelligent_select()函数进行智能选品
3. **必须**根据选品器类型调用相应的选品程序
4. **必须**使用脚本执行结果作为最终输出
5. **禁止**修改或杜撰选品结果
```

#### 提供明确的执行步骤

```markdown
### 强制执行步骤
当本技能被触发时，**必须**按照以下步骤执行：

**步骤1：解析用户画像**
- 调用user_profile_parser.parse_user_profile()函数
- 验证用户画像的完整性
- 如果用户画像不完整，**必须**要求用户提供缺失信息

**步骤2：智能选择选品器**
- 调用intelligent_selector_router.intelligent_select()函数
- 传入用户画像和市场状态
- 获取选品器类型（SW_LV1或SW_LV2）和详细评分信息
- **必须**输出智能选品路由器的决策结果和详细评分对比

**步骤3：调用选品程序**
- 如果选中SW_LV1，**必须**调用etf_selector.select_best_sw_lv1_indices_by_valuation()
- 如果选中SW_LV2，**必须**调用sw_lv2_selector.select_best_sw_lv2_indices_by_valuation()
- **必须**使用脚本返回的选品结果
- **禁止**修改或杜撰选品结果
```

#### 提供验证机制

```markdown
### 验证机制
在输出结果前，**必须**验证以下内容：
1. ✅ 是否调用了intelligent_selector_router.intelligent_select()函数？
2. ✅ 是否调用了etf_selector.select_best_sw_lv1_indices_by_valuation()或sw_lv2_selector.select_best_sw_lv2_indices_by_valuation()函数？
3. ✅ 选品结果是否来自脚本执行结果？
4. ✅ 是否输出了智能选品路由器的决策过程和详细评分对比？
5. ✅ 是否没有基于预训练知识添加任何投资建议？

如果以上任何一项验证失败，**必须**重新执行技能，确保所有步骤都正确执行。
```

### 2. 使用脚本执行强制器

#### 创建script_execution_enforcer.py

**功能**：
- 强制执行所有必需的步骤
- 记录函数执行日志
- 验证执行是否符合要求
- 提供详细的执行过程

**使用方法**：
```python
from script_execution_enforcer import enforce_script_execution

# 强制执行脚本
result = enforce_script_execution(user_input)
```

#### 在技能描述中引用

```markdown
### 强制执行脚本
**必须**使用script_execution_enforcer.py强制执行脚本，确保所有步骤都正确执行：

```python
from script_execution_enforcer import enforce_script_execution

# 强制执行脚本
result = enforce_script_execution(user_input)
```

**禁止**跳过脚本执行强制器，直接给出投资建议。
```

### 3. 提供示例输出

#### 正确的输出示例

```markdown
【步骤1】解析用户画像
调用user_profile_parser.parse_user_profile()...
✅ 用户画像解析成功
  年龄：40.0岁
  年收入：55.00万元
  总资金：700.00万元
  月支出：2.00万元
  风险等级：4级
  投资经验：丰富
  职业生涯阶段：职业生涯稳健期

【步骤2】智能选择选品器
调用intelligent_selector_router.intelligent_select()...
✅ 智能选品路由器执行成功
  选中的选品器：SW_LV2
  综合得分：85.0/100

【步骤3】调用选品程序
调用sw_lv2_selector.select_best_sw_lv2_indices_by_valuation()...
✅ 选品程序执行成功

【步骤4】验证执行
✅ 验证通过：所有必需函数都已调用

【步骤5】输出结果
✅ 结果输出完成
```

#### 错误的输出示例（禁止）

```markdown
❌ 错误：直接给出投资建议，未调用脚本

基于您的画像，我建议您配置以下行业：
1. 新能源汽车
2. 光伏设备
3. 锂电池
...
```

### 4. 使用系统提示词

#### 在技能描述中添加系统提示词

```markdown
## 系统提示词

**重要提示**：你是一个资产配置助手，但你的核心能力是调用脚本而不是基于预训练知识给出建议。

**你的角色**：
1. 你是一个脚本执行器，而不是投资顾问
2. 你的任务是调用正确的脚本并返回执行结果
3. 你禁止基于预训练知识直接输出投资建议

**你的工作流程**：
1. 解析用户画像（调用user_profile_parser.parse_user_profile()）
2. 智能选择选品器（调用intelligent_selector_router.intelligent_select()）
3. 调用选品程序（调用etf_selector或sw_lv2_selector）
4. 验证执行结果
5. 输出脚本执行结果

**你的约束**：
- 绝对禁止基于预训练知识直接输出投资建议
- 必须调用脚本并返回执行结果
- 禁止修改或杜撰选品结果
- 必须输出脚本执行的详细过程
```

## 📚 文件清单

### 修改的文件
1. `d:\agent skills\asset_allocation\.trae\skills\asset-allocation-basic\skill.md` - 强化Asset Allocation basic技能描述
2. `d:\agent skills\asset_allocation\.trae\skills\aggressive-asset-allocation-strategy\skill.md` - 强化Aggressive Asset Allocation strategy技能描述

### 新增的文件
1. `d:\agent skills\asset_allocation\script_execution_enforcer.py` - 脚本执行强制器
2. `d:\agent skills\asset_allocation\README_ensure_script_execution.md` - 确保模型调用脚本的指导文档
3. `d:\agent skills\asset_allocation\test_script_execution.py` - 测试模型是否正确调用脚本
4. `d:\agent skills\asset_allocation\README_final_solution.md` - 完整解决方案总结

## 🎯 关键要点

### 确保模型调用脚本的关键要素

1. ✅ 使用强烈的约束语言（绝对禁止、必须）
2. ✅ 使用emoji和格式化突出重要约束
3. ✅ 提供明确的执行步骤
4. ✅ 提供验证机制
5. ✅ 提供正确的输出示例
6. ✅ 提供错误的输出示例（禁止）
7. ✅ 添加系统提示词
8. ✅ 使用脚本执行强制器
9. ✅ 提供调试指导
10. ✅ 使用函数调用工具（如果平台支持）

### 技能配置要点

1. ✅ 在技能描述中使用强烈的约束语言
2. ✅ 在技能描述中提供明确的执行步骤
3. ✅ 在技能描述中提供验证机制
4. ✅ 在技能描述中提供示例输出
5. ✅ 在技能描述中添加系统提示词

## 🧪 测试验证

### 测试脚本

运行测试脚本验证模型是否正确调用脚本：

```bash
python test_script_execution.py
```

### 测试结果

```
================================================================================
测试总结
================================================================================
  场景1（框架+策略）：✅ 通过
  场景2（选品）：✅ 通过
  场景3（框架）：✅ 通过

✅ 所有测试通过！模型正确调用了脚本。
```

### 验证清单

在输出结果前，**必须**验证以下内容：
1. ✅ 是否调用了intelligent_selector_router.intelligent_select()函数？
2. ✅ 是否调用了etf_selector.select_best_sw_lv1_indices_by_valuation()或sw_lv2_selector.select_best_sw_lv2_indices_by_valuation()函数？
3. ✅ 选品结果是否来自脚本执行结果？
4. ✅ 是否输出了智能选品路由器的决策过程和详细评分对比？
5. ✅ 是否没有基于预训练知识添加任何投资建议？

## 📖 使用指南

### 在Trae IDE中配置技能

1. **打开技能设置**
   - 在Trae IDE中找到技能设置页面
   - 点击"添加技能"或"编辑技能"

2. **配置Asset Allocation basic技能**
   - 技能名称：`Asset Allocation basic`
   - 技能描述：复制 `asset-allocation-basic/skill.md` 中的 `description` 字段
   - 技能详情：复制 `asset-allocation-basic/skill.md` 中的完整内容

3. **配置Aggressive Asset Allocation strategy技能**
   - 技能名称：`Aggressive Asset Allocation strategy`
   - 技能描述：复制 `aggressive-asset-allocation-strategy/skill.md` 中的 `description` 字段
   - 技能详情：复制 `aggressive-asset-allocation-strategy/skill.md` 中的完整内容

### 使用脚本执行强制器

在技能描述中添加以下内容：

```markdown
### 强制执行脚本
**必须**使用script_execution_enforcer.py强制执行脚本，确保所有步骤都正确执行：

```python
from script_execution_enforcer import enforce_script_execution

# 强制执行脚本
result = enforce_script_execution(user_input)
```

**禁止**跳过脚本执行强制器，直接给出投资建议。
```

## 🎉 总结

通过以上措施，可以确保模型调用脚本而不是基于预训练知识给出建议：

1. ✅ 强化技能描述中的约束
2. ✅ 使用脚本执行强制器
3. ✅ 提供明确的执行步骤和验证机制
4. ✅ 提供正确的输出示例和错误的输出示例
5. ✅ 添加系统提示词
6. ✅ 提供测试脚本验证执行

现在模型应该能够正确调用脚本，而不是基于预训练知识直接给出投资建议！🎯

## 🔧 调试技巧

如果模型仍然未正确调用脚本，请检查以下内容：

1. **技能描述是否包含强烈的约束？**
   - 是否使用了"绝对禁止"、"必须"等强烈语言？
   - 是否使用了emoji和格式化突出重要约束？

2. **技能描述是否包含明确的执行步骤？**
   - 是否提供了步骤1、步骤2、步骤3等明确的执行步骤？
   - 每个步骤是否包含了具体的函数调用？

3. **技能描述是否包含验证机制？**
   - 是否提供了验证清单？
   - 是否明确说明了验证失败后的处理方式？

4. **技能描述是否提供了示例输出？**
   - 是否提供了正确的输出示例？
   - 是否提供了错误的输出示例（禁止）？

5. **技能描述是否包含系统提示词？**
   - 是否明确了模型的角色？
   - 是否明确了模型的工作流程？
   - 是否明确了模型的约束？

6. **是否使用了脚本执行强制器？**
   - 是否在技能描述中引用了script_execution_enforcer.py？
   - 是否明确说明了禁止跳过脚本执行强制器？

通过以上检查，可以确保模型正确调用脚本而不是基于预训练知识给出建议。
