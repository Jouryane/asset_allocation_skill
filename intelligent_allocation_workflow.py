"""
智能选品集成脚本
根据智能选品路由器的决策，自动调用相应的选品程序
"""

import sys
import os
from intelligent_selector_router import intelligent_select, SelectorType


def run_sw_lv1_selector(user_profile: dict):
    """
    运行申万一级行业指数选品程序
    
    :param user_profile: 用户画像
    :return: 选品结果
    """
    print("\n正在运行申万一级行业指数选品程序...")
    print("-" * 80)
    
    try:
        # 导入etf_selector模块
        from etf_selector import select_best_sw_lv1_indices_by_valuation
        
        # 运行选品
        result = select_best_sw_lv1_indices_by_valuation()
        
        print("\n✓ 申万一级行业指数选品完成")
        return result
        
    except ImportError:
        print("\n✗ 未找到etf_selector模块")
        return None
    except Exception as e:
        print(f"\n✗ 申万一级行业指数选品失败: {str(e)}")
        return None


def run_sw_lv2_selector(user_profile: dict):
    """
    运行申万二级行业指数选品程序
    
    :param user_profile: 用户画像
    :return: 选品结果
    """
    print("\n正在运行申万二级行业指数选品程序...")
    print("-" * 80)
    
    try:
        # 导入sw_lv2_selector模块
        from sw_lv2_selector import select_best_sw_lv2_indices_by_valuation
        
        # 运行选品
        result = select_best_sw_lv2_indices_by_valuation()
        
        print("\n✓ 申万二级行业指数选品完成")
        return result
        
    except ImportError:
        print("\n✗ 未找到sw_lv2_selector模块")
        return None
    except Exception as e:
        print(f"\n✗ 申万二级行业指数选品失败: {str(e)}")
        return None


def run_visualization(selector_type: str, result: dict):
    """
    运行可视化程序
    
    :param selector_type: 选品器类型（sw_lv1或sw_lv2）
    :param result: 选品结果
    """
    print(f"\n正在生成{selector_type.upper()}可视化图表...")
    print("-" * 80)
    
    try:
        if selector_type == 'sw_lv1':
            from draw import draw_all_indices
            # 提取选中的指数信息
            selected_indices = [
                {
                    'code': item['指数代码'],
                    'name': item['指数名称']
                }
                for item in result.get('selected_indices', [])
            ]
            draw_all_indices(selected_indices)
        else:  # sw_lv2
            from draw_lv2 import draw_all_indices
            # 提取选中的指数信息
            selected_indices = [
                {
                    'code': item['指数代码'],
                    'name': item['指数名称']
                }
                for item in result.get('selected_indices', [])
            ]
            draw_all_indices(selected_indices)
        
        print(f"\n✓ {selector_type.upper()}可视化图表生成完成")
        
    except ImportError:
        print(f"\n✗ 未找到draw_{selector_type}.py模块")
    except Exception as e:
        print(f"\n✗ {selector_type.upper()}可视化图表生成失败: {str(e)}")


def intelligent_allocation_workflow(user_profile: dict, market_state: dict = None, auto_visualize: bool = True):
    """
    智能资产配置工作流
    
    :param user_profile: 用户画像
    :param market_state: 市场状态（可选）
    :param auto_visualize: 是否自动生成可视化图表
    :return: (选品器类型, 选品结果, 路由决策信息)
    """
    print("=" * 80)
    print("智能资产配置工作流")
    print("=" * 80)
    print(f"\n用户画像：")
    print(f"  年龄：{user_profile.get('age', '未知')}岁")
    print(f"  年收入：{user_profile.get('annual_income', 0):.2f}万元")
    print(f"  总资金：{user_profile.get('total_capital', 0):.2f}万元")
    print(f"  月支出：{user_profile.get('monthly_expense', 0):.2f}万元")
    print(f"  风险等级：{user_profile.get('risk_level', '未知')}级")
    print(f"  投资经验：{user_profile.get('investment_experience', '未知')}")
    print(f"  职业生涯阶段：{user_profile.get('career_stage', '未知')}")
    print()
    
    # 步骤1：智能选择选品器
    print("【步骤1】智能选择选品器")
    print("=" * 80)
    selected_type, routing_info = intelligent_select(user_profile, market_state)
    print()
    
    # 步骤2：运行选品程序
    print("【步骤2】运行选品程序")
    print("=" * 80)
    
    if selected_type == 'sw_lv1':
        result = run_sw_lv1_selector(user_profile)
    else:  # sw_lv2
        result = run_sw_lv2_selector(user_profile)
    
    if result is None:
        print("\n✗ 选品程序执行失败")
        return None, None, routing_info
    
    # 步骤3：生成可视化图表（可选）
    if auto_visualize:
        print("\n【步骤3】生成可视化图表")
        print("=" * 80)
        run_visualization(selected_type, result)
    
    # 步骤4：总结
    print("\n【步骤4】工作流总结")
    print("=" * 80)
    print(f"  使用的选品器：{selected_type.upper()}")
    print(f"  路由决策得分：{routing_info['selected_score']:.1f}/100")
    print(f"  SW_LV1得分：{routing_info['sw_lv1_score']:.1f}/100")
    print(f"  SW_LV2得分：{routing_info['sw_lv2_score']:.1f}/100")
    print()
    
    return selected_type, result, routing_info


def main(user_profile: dict = None, market_state: dict = None):
    """
    主函数
    
    :param user_profile: 用户画像（可选）
    :param market_state: 市场状态（可选）
    """
    # 如果没有提供用户画像，使用示例数据
    if user_profile is None:
        print("未提供用户画像，使用示例数据...")
        user_profile = {
            'age': 34,
            'annual_income': 30,
            'total_capital': 100,
            'monthly_expense': 1,
            'risk_level': 3,
            'investment_experience': '匮乏',
            'career_stage': '职业生涯起步'
        }
    
    # 如果没有提供市场状态，使用默认值
    if market_state is None:
        print("未提供市场状态，使用默认值...")
        market_state = {
            'volatility': 'medium',
            'trend': 'neutral'
        }
    
    # 运行智能资产配置工作流
    selected_type, result, routing_info = intelligent_allocation_workflow(
        user_profile=user_profile,
        market_state=market_state,
        auto_visualize=True
    )
    
    return selected_type, result, routing_info


if __name__ == "__main__":
    # 测试用例1：小资金+保守型
    print("\n" + "=" * 80)
    print("测试用例1：小资金+保守型")
    print("=" * 80)
    
    user_profile_1 = {
        'age': 34,
        'annual_income': 30,
        'total_capital': 80,
        'monthly_expense': 1,
        'risk_level': 2,
        'investment_experience': '匮乏',
        'career_stage': '职业生涯起步'
    }
    
    market_state_1 = {
        'volatility': 'medium',
        'trend': 'neutral'
    }
    
    main(user_profile_1, market_state_1)
    
    # 测试用例2：大资金+激进型
    print("\n" + "=" * 80)
    print("测试用例2：大资金+激进型")
    print("=" * 80)
    
    user_profile_2 = {
        'age': 40,
        'annual_income': 80,
        'total_capital': 500,
        'monthly_expense': 1.5,
        'risk_level': 4,
        'investment_experience': '丰富',
        'career_stage': '职业生涯稳健期'
    }
    
    market_state_2 = {
        'volatility': 'high',
        'trend': 'up'
    }
    
    main(user_profile_2, market_state_2)
    
    # 测试用例3：中等资金+稳健型
    print("\n" + "=" * 80)
    print("测试用例3：中等资金+稳健型")
    print("=" * 80)
    
    user_profile_3 = {
        'age': 35,
        'annual_income': 50,
        'total_capital': 200,
        'monthly_expense': 0.8,
        'risk_level': 3,
        'investment_experience': '一般',
        'career_stage': '职业生涯稳健期'
    }
    
    market_state_3 = {
        'volatility': 'medium',
        'trend': 'neutral'
    }
    
    main(user_profile_3, market_state_3)
