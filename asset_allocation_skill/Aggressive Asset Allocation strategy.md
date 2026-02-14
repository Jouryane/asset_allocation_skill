---
name: Aggressive Asset Allocation strategy
description: 在本agent技能中执行资产配置进取类资产战术的一环，负责处理“选什么去买”、“买多少”等问题。当用户输入"配置战术"、"帮我选品"、"买什么"或类似需要提供资产配置进取类资产战术的场景时触发。根据用户拟定的常用投资标的池，自动应用估值分析框架、采用分位数压缩法 + 衰减权重法的组合提供仓位配置建议，输出可直接用于交易决策的战术方案。完成后可以将方案配置到钉钉机器人进行播报。
---
## Aggressive Asset Allocation strategy

## 1. 概述
Aggressive Asset Allocation strategy技能核心目标是基于用户常用投资标的，结合当前市场状况完成「高性价比标的筛选→战术决策制定→结果推送」全流程，避免AI依赖预训练的资产配置方案，而是根据市场以及策略，完全通过执行自定义脚本逻辑输出符合市场实时状态的配置建议。

## 2.核心依赖文件说明
文件名称	核心作用	调用方式
config.py	定义资产配置核心思想（如风险偏好映射、大类资产权重基准、估值锚定规则等）	作为基础配置模块被本技能逻辑导入
etf_selector.py	基于用户常用投资标的池，计算标的性价比（如估值分位、盈利增速、资金流向等维度），筛选 Top N 高性价比标的	调用其核心函数select_high_value_etf(user_hold_etfs, market_data)
strategy.py	基于筛选出的高性价比标的，结合市场状况（如牛熊阶段、波动率、政策导向）制定具体战术（如仓位调整、定投节奏、止盈止损阈值）	调用其核心函数generate_tactics(selected_etfs, market_status, config)
dingding.py	将最终资产配置建议（标的 + 战术）格式化并推送至指定钉钉群 / 个人	调用其核心函数push_allocation_result(result, dingding_config)

## 3.核心执行逻辑
1. 环境与模块导入
import pandas as pd
import numpy as np
from config import asset_config, risk_mapping
from etf_selector import select_high_value_etf
from strategy import generate_tactics
from dingding import push_allocation_result

def get_real_time_market_data():
    """获取实时市场数据：标的估值、成交量、指数点位、政策信息等"""
    # 实际场景需对接券商/财经数据源API
    market_data = {
        "etf_valuation": pd.read_csv("etf_valuation.csv", index_col="code"),
        "market_volatility": np.array(pd.read_csv("volatility.csv")["vix"]),
        "policy_guidance": pd.read_csv("policy.csv")["content"].tolist(),
        "index_level": pd.read_csv("index_level.csv", index_col="index_code")
    }
    return market_data

2. 资产配置主函数
def asset_allocation_main(user_info):
    """
    资产配置核心执行函数
    :param user_info: dict，包含用户常用标的、风险偏好、资金规模等
                      示例：{"hold_etfs": ["510300", "159915", "512000"], "risk_level": "moderate", "capital": 100000}
    :return: dict，最终资产配置建议
    """
    # 步骤1：获取实时市场数据
    market_data = get_real_time_market_data()
    
    # 步骤2：筛选高性价比ETF标的
    high_value_etfs = select_high_value_etf(
        user_hold_etfs=user_info["hold_etfs"],
        market_data=market_data
    )
    if len(high_value_etfs) == 0:
        raise ValueError("未筛选出符合条件的高性价比标的，请检查标的池或市场数据")
    
    # 步骤3：结合市场状况生成战术决策
    market_status = {
        "volatility": "high" if market_data["market_volatility"].mean() > 20 else "low",
        "index_valuation": "overvalued" if market_data["index_level"]["pe"].mean() > asset_config["pe_threshold"] else "undervalued",
        "policy": market_data["policy_guidance"]
    }
    tactics = generate_tactics(
        selected_etfs=high_value_etfs,
        market_status=market_status,
        config=asset_config
    )
    
    # 步骤4：结合用户风险偏好调整最终配置
    risk_adjusted_allocation = {}
    for etf_code, details in tactics.items():
        base_weight = details["weight"]
        # 基于config中的风险映射调整权重
        risk_adjusted_weight = base_weight * risk_mapping[user_info["risk_level"]]
        risk_adjusted_allocation[etf_code] = {
            "weight": round(risk_adjusted_weight, 2),
            "tactics": details["tactics"],
            "valuation": market_data["etf_valuation"].loc[etf_code]["pe"],
            "operation": details["operation"]  # 如：买入/持有/减仓/定投
        }
    
    # 步骤5：封装最终结果
    final_result = {
        "user_risk_level": user_info["risk_level"],
        "high_value_etfs": high_value_etfs,
        "risk_adjusted_allocation": risk_adjusted_allocation,
        "capital_allocation": {k: v["weight"] * user_info["capital"] for k, v in risk_adjusted_allocation.items()},
        "market_status_summary": f"当前市场波动率：{market_status['volatility']}，核心指数估值：{market_status['index_valuation']}"
    }
    
    # 步骤6：推送结果至钉钉
    push_allocation_result(final_result, asset_config["dingding"])
    
    # 空壳函数调用，兼容template_generator引用
    empty_template_wrapper(final_result)
    
    return final_result

3. 执行入口
if __name__ == "__main__":
    # 示例用户信息
    sample_user_info = {
        "hold_etfs": ["510300", "159915", "512000", "513100"],
        "risk_level": "moderate",
        "capital": 100000
    }
    # 执行资产配置
    allocation_result = asset_allocation_main(sample_user_info)
    # 打印结果
    print("最终资产配置建议：")
    for etf, details in allocation_result["risk_adjusted_allocation"].items():
        print(f"ETF代码：{etf} | 配置权重：{details['weight']} | 操作建议：{details['operation']}")

## 4.关键注意事项
- 数据源适配：get_real_time_market_data函数需根据实际对接的财经数据源（这里使用AKshare）调整，确保数据实时性，避免使用静态预训练数据。
- 风险偏好映射：config.py中的risk_mapping需根据用户风险等级（保守/稳健/激进）精准调整标的权重，避免固定化配置。
- 异常处理：实际部署需补充更多异常捕获逻辑（如数据源失效、标的代码错误、推送失败等），保证脚本鲁棒性。
- 禁止预训练逻辑替代：本技能所有配置建议均通过执行上述代码片段生成，禁止 AI 基于预训练知识直接输出资产配置方案，需严格调用脚本并返回执行结果。

## 输出格式规范
最终推送至钉钉的资产配置结果需遵循以下格式，确保可读性：
【用户资产配置建议】
1.用户风险等级：{risk_level}
2.市场状态：{market_status_summary}
3.高性价比标的及配置：
   - ETF {code1}：配置权重{weight1}% | 操作建议：{operation1} | 当前估值PE：{pe1}
   - ETF {code2}：配置权重{weight2}% | 操作建议：{operation2} | 当前估值PE：{pe2}
4.资金分配：
   - ETF {code1}：{capital1}元
   - ETF {code2}：{capital2}元