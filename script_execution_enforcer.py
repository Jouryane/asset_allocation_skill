"""
强制执行脚本包装器
确保模型必须调用脚本而不是基于预训练知识给出建议
"""

import sys
import subprocess
from typing import Dict, Optional
from user_profile_parser import parse_user_profile
from intelligent_selector_router import intelligent_select


class ScriptExecutionEnforcer:
    """脚本执行强制器"""
    
    def __init__(self):
        self.required_functions = {
            'user_profile_parser': 'parse_user_profile',
            'intelligent_selector_router': 'intelligent_select',
            'etf_selector': 'select_best_sw_lv1_indices_by_valuation',
            'sw_lv2_selector': 'select_best_sw_lv2_indices_by_valuation',
        }
        self.execution_log = []
    
    def log_execution(self, function_name: str, params: Dict, result: any):
        """
        记录函数执行日志
        
        :param function_name: 函数名称
        :param params: 函数参数
        :param result: 函数返回结果
        """
        log_entry = {
            'function': function_name,
            'params': params,
            'result': result,
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }
        self.execution_log.append(log_entry)
        print(f"[EXECUTION LOG] {function_name} called with params: {params}")
    
    def validate_execution(self) -> bool:
        """
        验证执行是否符合要求
        
        :return: 是否符合要求
        """
        # 检查是否调用了必需的函数
        called_functions = [log['function'] for log in self.execution_log]
        
        # 必须调用的函数
        required_functions = [
            'user_profile_parser.parse_user_profile',
            'intelligent_selector_router.intelligent_select',
        ]
        
        # 必须调用选品程序之一
        selector_functions = [
            'etf_selector.select_best_sw_lv1_indices_by_valuation',
            'sw_lv2_selector.select_best_sw_lv2_indices_by_valuation',
        ]
        
        # 验证必需函数
        for func in required_functions:
            if func not in called_functions:
                print(f"❌ 验证失败：未调用必需函数 {func}")
                return False
        
        # 验证选品程序
        selector_called = any(func in called_functions for func in selector_functions)
        if not selector_called:
            print(f"❌ 验证失败：未调用选品程序")
            return False
        
        print(f"✅ 验证通过：所有必需函数都已调用")
        return True
    
    def execute_with_validation(self, user_input: str) -> Dict:
        """
        执行并验证
        
        :param user_input: 用户输入
        :return: 执行结果
        """
        print("=" * 80)
        print("脚本执行强制器启动")
        print("=" * 80)
        print()
        
        # 步骤1：解析用户画像
        print("【步骤1】解析用户画像")
        print("-" * 80)
        try:
            profile, validation = parse_user_profile(user_input)
            self.log_execution('user_profile_parser.parse_user_profile', {'user_input': user_input}, {'profile': profile, 'validation': validation})
            
            if not validation['is_valid']:
                print(f"❌ 用户画像不完整，缺失字段：{validation['missing_fields']}")
                return {'error': '用户画像不完整', 'missing_fields': validation['missing_fields']}
            
            print(f"✅ 用户画像解析成功")
            print(f"  年龄：{profile.get('age', '未知')}岁")
            print(f"  年收入：{profile.get('annual_income', 0):.2f}万元")
            print(f"  总资金：{profile.get('total_capital', 0):.2f}万元")
            print(f"  月支出：{profile.get('monthly_expense', 0):.2f}万元")
            print(f"  风险等级：{profile.get('risk_level', '未知')}级")
            print(f"  投资经验：{profile.get('investment_experience', '未知')}")
            print(f"  职业生涯阶段：{profile.get('career_stage', '未知')}")
            print()
        except Exception as e:
            print(f"❌ 用户画像解析失败：{str(e)}")
            return {'error': '用户画像解析失败', 'exception': str(e)}
        
        # 步骤2：智能选择选品器
        print("【步骤2】智能选择选品器")
        print("-" * 80)
        try:
            market_state = {
                'volatility': 'medium',
                'trend': 'neutral'
            }
            
            selected_type, routing_info = intelligent_select(profile, market_state)
            self.log_execution('intelligent_selector_router.intelligent_select', {'profile': profile, 'market_state': market_state}, {'selected_type': selected_type, 'routing_info': routing_info})
            
            print(f"✅ 智能选品路由器执行成功")
            print(f"  选中的选品器：{selected_type}")
            print(f"  综合得分：{routing_info['selected_score']:.1f}/100")
            print()
        except Exception as e:
            print(f"❌ 智能选品路由器执行失败：{str(e)}")
            return {'error': '智能选品路由器执行失败', 'exception': str(e)}
        
        # 步骤3：调用选品程序
        print("【步骤3】调用选品程序")
        print("-" * 80)
        try:
            if selected_type == 'sw_lv1':
                print(f"调用etf_selector.select_best_sw_lv1_indices_by_valuation()...")
                from etf_selector import select_best_sw_lv1_indices_by_valuation
                result = select_best_sw_lv1_indices_by_valuation()
                self.log_execution('etf_selector.select_best_sw_lv1_indices_by_valuation', {}, result)
            else:  # sw_lv2
                print(f"调用sw_lv2_selector.select_best_sw_lv2_indices_by_valuation()...")
                from sw_lv2_selector import select_best_sw_lv2_indices_by_valuation
                result = select_best_sw_lv2_indices_by_valuation()
                self.log_execution('sw_lv2_selector.select_best_sw_lv2_indices_by_valuation', {}, result)
            
            print(f"✅ 选品程序执行成功")
            print()
        except Exception as e:
            print(f"❌ 选品程序执行失败：{str(e)}")
            return {'error': '选品程序执行失败', 'exception': str(e)}
        
        # 步骤4：验证执行
        print("【步骤4】验证执行")
        print("-" * 80)
        if not self.validate_execution():
            print(f"❌ 执行验证失败")
            return {'error': '执行验证失败', 'execution_log': self.execution_log}
        
        print(f"✅ 执行验证通过")
        print()
        
        # 步骤5：输出结果
        print("【步骤5】输出结果")
        print("-" * 80)
        final_result = {
            'profile': profile,
            'selected_type': selected_type,
            'routing_info': routing_info,
            'selection_result': result,
            'execution_log': self.execution_log
        }
        
        print(f"✅ 结果输出完成")
        print()
        
        return final_result


def enforce_script_execution(user_input: str) -> Dict:
    """
    强制执行脚本（便捷函数）
    
    :param user_input: 用户输入
    :return: 执行结果
    """
    enforcer = ScriptExecutionEnforcer()
    return enforcer.execute_with_validation(user_input)


if __name__ == "__main__":
    # 测试用例
    test_input = "我是一位40岁的男性、目前收入在年55万人民币，有丰富的投资经验，主要是进行基金股票投资，已婚，没有任何负债，目前我的资金大约是700万人民币，每月开支在20000人民币左右。请帮我选品。"
    
    result = enforce_script_execution(test_input)
    
    print("=" * 80)
    print("执行结果")
    print("=" * 80)
    print(f"选中的选品器：{result.get('selected_type', '未知')}")
    print(f"路由决策得分：{result.get('routing_info', {}).get('selected_score', 0):.1f}/100")
    print(f"选品结果：{result.get('selection_result', {})}")
    print()
