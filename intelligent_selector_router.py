"""
智能选品路由器
根据用户画像和市场状态，智能选择使用sw_lv1或sw_lv2选品程序
"""

from typing import Dict, Optional, Tuple
from enum import Enum
import pandas as pd


class SelectorType(Enum):
    """选品器类型"""
    SW_LV1 = "sw_lv1"  # 申万一级行业指数
    SW_LV2 = "sw_lv2"  # 申万二级行业指数


class IntelligentSelectorRouter:
    """智能选品路由器"""
    
    def __init__(self):
        # 权重配置（可根据实际情况调整）
        self.weights = {
            'capital': 0.3,          # 资金规模权重
            'risk_level': 0.25,       # 风险偏好权重
            'experience': 0.2,        # 投资经验权重
            'market_state': 0.15,      # 市场状态权重
            'diversification': 0.1,    # 分散化需求权重
        }
    
    def calculate_selector_score(self, selector_type: SelectorType, user_profile: Dict, market_state: Dict) -> float:
        """
        计算选品器的适用性得分
        
        :param selector_type: 选品器类型（SW_LV1或SW_LV2）
        :param user_profile: 用户画像
        :param market_state: 市场状态
        :return: 适用性得分（0-100）
        """
        scores = {}
        
        # 1. 资金规模评分
        capital_score = self._evaluate_capital(selector_type, user_profile)
        scores['capital'] = capital_score
        
        # 2. 风险偏好评分
        risk_score = self._evaluate_risk_preference(selector_type, user_profile)
        scores['risk_level'] = risk_score
        
        # 3. 投资经验评分
        experience_score = self._evaluate_investment_experience(selector_type, user_profile)
        scores['experience'] = experience_score
        
        # 4. 市场状态评分
        market_score = self._evaluate_market_state(selector_type, market_state)
        scores['market_state'] = market_score
        
        # 5. 分散化需求评分
        diversification_score = self._evaluate_diversification(selector_type, user_profile)
        scores['diversification'] = diversification_score
        
        # 计算加权总分
        total_score = sum(scores[key] * self.weights[key] for key in scores.keys())
        
        return total_score, scores
    
    def _evaluate_capital(self, selector_type: SelectorType, user_profile: Dict) -> float:
        """
        评估资金规模适配性
        
        :param selector_type: 选品器类型
        :param user_profile: 用户画像
        :return: 资金规模评分（0-100）
        """
        total_capital = user_profile.get('total_capital', 0)
        
        if selector_type == SelectorType.SW_LV1:
            # 一级行业适合中小资金
            if total_capital < 100:  # <100万
                return 90
            elif total_capital < 500:  # 100-500万
                return 80
            else:  # >=500万
                return 60
        else:  # SW_LV2
            # 二级行业适合大资金
            if total_capital < 100:  # <100万
                return 40
            elif total_capital < 500:  # 100-500万
                return 70
            else:  # >=500万
                return 95
    
    def _evaluate_risk_preference(self, selector_type: SelectorType, user_profile: Dict) -> float:
        """
        评估风险偏好适配性
        
        :param selector_type: 选品器类型
        :param user_profile: 用户画像
        :return: 风险偏好评分（0-100）
        """
        risk_level = user_profile.get('risk_level', 3)
        
        # 如果risk_level为None，使用默认值3（稳健型）
        if risk_level is None:
            risk_level = 3
        
        if selector_type == SelectorType.SW_LV1:
            # 一级行业适合保守到稳健型
            if risk_level <= 2:  # 保守
                return 90
            elif risk_level == 3:  # 稳健
                return 85
            else:  # 激进
                return 60
        else:  # SW_LV2
            # 二级行业适合稳健到激进型
            if risk_level <= 2:  # 保守
                return 50
            elif risk_level == 3:  # 稳健
                return 80
            else:  # 激进
                return 95
    
    def _evaluate_investment_experience(self, selector_type: SelectorType, user_profile: Dict) -> float:
        """
        评估投资经验适配性
        
        :param selector_type: 选品器类型
        :param user_profile: 用户画像
        :return: 投资经验评分（0-100）
        """
        experience = user_profile.get('investment_experience', '一般')
        
        # 将投资经验映射为数值
        experience_map = {
            '无': 1,
            '匮乏': 2,
            '较少': 3,
            '一般': 4,
            '较多': 5,
            '丰富': 6
        }
        exp_level = experience_map.get(experience, 4)
        
        if selector_type == SelectorType.SW_LV1:
            # 一级行业适合投资经验较少的用户
            if exp_level <= 3:  # 无/匮乏/较少
                return 90
            elif exp_level == 4:  # 一般
                return 80
            else:  # 较多/丰富
                return 70
        else:  # SW_LV2
            # 二级行业适合投资经验较多的用户
            if exp_level <= 3:  # 无/匮乏/较少
                return 40
            elif exp_level == 4:  # 一般
                return 75
            else:  # 较多/丰富
                return 95
    
    def _evaluate_market_state(self, selector_type: SelectorType, market_state: Dict) -> float:
        """
        评估市场状态适配性
        
        :param selector_type: 选品器类型
        :param market_state: 市场状态
        :return: 市场状态评分（0-100）
        """
        volatility = market_state.get('volatility', 'medium')
        trend = market_state.get('trend', 'neutral')
        
        if selector_type == SelectorType.SW_LV1:
            # 一级行业适合震荡市场
            if volatility == 'low':
                return 75
            elif volatility == 'medium':
                return 90
            else:  # high
                return 65
        else:  # SW_LV2
            # 二级行业适合趋势市场
            if volatility == 'low':
                return 70
            elif volatility == 'medium':
                return 80
            else:  # high
                return 85
    
    def _evaluate_diversification(self, selector_type: SelectorType, user_profile: Dict) -> float:
        """
        评估分散化需求适配性
        
        :param selector_type: 选品器类型
        :param user_profile: 用户画像
        :return: 分散化需求评分（0-100）
        """
        total_capital = user_profile.get('total_capital', 0)
        
        if selector_type == SelectorType.SW_LV1:
            # 一级行业数量少（31个），适合集中投资
            if total_capital < 200:  # <200万
                return 90
            elif total_capital < 500:  # 100-500万
                return 75
            else:  # >=500万
                return 60
        else:  # SW_LV2
            # 二级行业数量多（131个），适合分散投资
            if total_capital < 200:  # <200万
                return 50
            elif total_capital < 500:  # 100-500万
                return 80
            else:  # >=500万
                return 95
    
    def select_best_selector(self, user_profile: Dict, market_state: Optional[Dict] = None) -> Tuple[SelectorType, Dict]:
        """
        选择最佳选品器
        
        :param user_profile: 用户画像
        :param market_state: 市场状态（可选）
        :return: (选品器类型, 详细评分信息)
        """
        # 如果没有提供市场状态，使用默认值
        if market_state is None:
            market_state = {
                'volatility': 'medium',
                'trend': 'neutral'
            }
        
        # 计算两个选品器的得分
        sw_lv1_score, sw_lv1_scores = self.calculate_selector_score(SelectorType.SW_LV1, user_profile, market_state)
        sw_lv2_score, sw_lv2_scores = self.calculate_selector_score(SelectorType.SW_LV2, user_profile, market_state)
        
        # 选择得分更高的选品器
        if sw_lv1_score >= sw_lv2_score:
            selected_type = SelectorType.SW_LV1
            selected_score = sw_lv1_score
            selected_scores = sw_lv1_scores
        else:
            selected_type = SelectorType.SW_LV2
            selected_score = sw_lv2_score
            selected_scores = sw_lv2_scores
        
        # 构建详细评分信息
        detail_info = {
            'selected_type': selected_type.value,
            'selected_score': selected_score,
            'sw_lv1_score': sw_lv1_score,
            'sw_lv2_score': sw_lv2_score,
            'sw_lv1_scores': sw_lv1_scores,
            'sw_lv2_scores': sw_lv2_scores,
            'decision_reason': self._generate_decision_reason(selected_type, selected_scores, user_profile, market_state),
            'market_state': market_state
        }
        
        return selected_type, detail_info
    
    def _generate_decision_reason(self, selected_type: SelectorType, scores: Dict, user_profile: Dict, market_state: Dict) -> str:
        """
        生成决策原因说明
        
        :param selected_type: 选中的选品器类型
        :param scores: 得分详情
        :param user_profile: 用户画像
        :param market_state: 市场状态
        :return: 决策原因说明
        """
        reasons = []
        
        # 找出得分最高的几个维度
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_dimensions = [item[0] for item in sorted_scores[:2]]
        
        dimension_names = {
            'capital': '资金规模',
            'risk_level': '风险偏好',
            'experience': '投资经验',
            'market_state': '市场状态',
            'diversification': '分散化需求'
        }
        
        if selected_type == SelectorType.SW_LV1:
            reasons.append(f"选择申万一级行业指数（SW_LV1）")
            reasons.append(f"主要考虑因素：{dimension_names.get(top_dimensions[0], top_dimensions[0])}、{dimension_names.get(top_dimensions[1], top_dimensions[1])}")
            
            # 添加具体原因
            if 'capital' in top_dimensions:
                capital = user_profile.get('total_capital', 0)
                reasons.append(f"- 资金规模{capital:.0f}万元，适合一级行业集中投资")
            if 'risk_level' in top_dimensions:
                risk_level = user_profile.get('risk_level', 3)
                reasons.append(f"- 风险等级{risk_level}级，一级行业相对稳定")
            if 'experience' in top_dimensions:
                experience = user_profile.get('investment_experience', '一般')
                reasons.append(f"- 投资经验{experience}，一级行业更容易理解")
        else:  # SW_LV2
            reasons.append(f"选择申万二级行业指数（SW_LV2）")
            reasons.append(f"主要考虑因素：{dimension_names.get(top_dimensions[0], top_dimensions[0])}、{dimension_names.get(top_dimensions[1], top_dimensions[1])}")
            
            # 添加具体原因
            if 'capital' in top_dimensions:
                capital = user_profile.get('total_capital', 0)
                reasons.append(f"- 资金规模{capital:.0f}万元，适合二级行业分散投资")
            if 'risk_level' in top_dimensions:
                risk_level = user_profile.get('risk_level', 3)
                reasons.append(f"- 风险等级{risk_level}级，二级行业机会更多")
            if 'experience' in top_dimensions:
                experience = user_profile.get('investment_experience', '一般')
                reasons.append(f"- 投资经验{experience}，二级行业需要更强的分析能力")
        
        return "\n".join(reasons)
    
    def format_selection_result(self, detail_info: Dict) -> str:
        """
        格式化选择结果
        
        :param detail_info: 详细评分信息
        :return: 格式化的结果文本
        """
        lines = []
        lines.append("=" * 80)
        lines.append("智能选品路由器决策结果")
        lines.append("=" * 80)
        lines.append("")
        
        # 决策结果
        lines.append("【决策结果】")
        lines.append(f"  选中选品器：{detail_info['selected_type'].upper()}")
        lines.append(f"  综合得分：{detail_info['selected_score']:.1f}/100")
        lines.append("")
        
        # 决策原因
        lines.append("【决策原因】")
        lines.append(detail_info['decision_reason'])
        lines.append("")
        
        # 详细评分对比
        lines.append("【详细评分对比】")
        lines.append(f"{'维度':<15} {'SW_LV1得分':<15} {'SW_LV2得分':<15} {'权重':<10}")
        lines.append("-" * 60)
        
        dimension_names = {
            'capital': '资金规模',
            'risk_level': '风险偏好',
            'experience': '投资经验',
            'market_state': '市场状态',
            'diversification': '分散化需求'
        }
        
        for dimension in ['capital', 'risk_level', 'experience', 'market_state', 'diversification']:
            sw_lv1_score = detail_info['sw_lv1_scores'][dimension]
            sw_lv2_score = detail_info['sw_lv2_scores'][dimension]
            weight = self.weights[dimension]
            lines.append(f"{dimension_names[dimension]:<15} {sw_lv1_score:>10.1f} {sw_lv2_score:>10.1f} {weight*100:>6.0f}%")
        
        lines.append("")
        
        # 市场状态
        lines.append("【市场状态】")
        lines.append(f"  波动率：{detail_info['market_state'].get('volatility', 'medium')}")
        lines.append(f"  趋势：{detail_info['market_state'].get('trend', 'neutral')}")
        lines.append("")
        
        # 下一步操作
        lines.append("【下一步操作】")
        if detail_info['selected_type'] == 'sw_lv1':
            lines.append("  1. 运行 etf_selector.py 进行申万一级行业指数筛选")
            lines.append("  2. 查看筛选结果和可视化图表")
        else:
            lines.append("  1. 运行 sw_lv2_selector.py 进行申万二级行业指数筛选")
            lines.append("  2. 查看筛选结果和可视化图表")
        lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)


def intelligent_select(user_profile: Dict, market_state: Optional[Dict] = None) -> Tuple[str, Dict]:
    """
    智能选择选品器（便捷函数）
    
    :param user_profile: 用户画像
    :param market_state: 市场状态（可选）
    :return: (选品器类型, 详细评分信息)
    """
    router = IntelligentSelectorRouter()
    selected_type, detail_info = router.select_best_selector(user_profile, market_state)
    
    # 格式化并打印结果
    print(router.format_selection_result(detail_info))
    
    return selected_type.value, detail_info


if __name__ == "__main__":
    # 测试用例
    test_cases = [
        {
            'name': '测试用例1：小资金+保守型',
            'user_profile': {
                'age': 34,
                'annual_income': 30,
                'total_capital': 80,
                'monthly_expense': 1,
                'risk_level': 2,
                'investment_experience': '匮乏',
                'career_stage': '职业生涯起步'
            },
            'market_state': {
                'volatility': 'medium',
                'trend': 'neutral'
            }
        },
        {
            'name': '测试用例2：大资金+激进型',
            'user_profile': {
                'age': 40,
                'annual_income': 80,
                'total_capital': 500,
                'monthly_expense': 1.5,
                'risk_level': 4,
                'investment_experience': '丰富',
                'career_stage': '职业生涯稳健期'
            },
            'market_state': {
                'volatility': 'high',
                'trend': 'up'
            }
        },
        {
            'name': '测试用例3：中等资金+稳健型',
            'user_profile': {
                'age': 35,
                'annual_income': 50,
                'total_capital': 200,
                'monthly_expense': 0.8,
                'risk_level': 3,
                'investment_experience': '一般',
                'career_stage': '职业生涯稳健期'
            },
            'market_state': {
                'volatility': 'medium',
                'trend': 'neutral'
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"{test_case['name']}")
        print(f"{'='*80}\n")
        
        selected_type, detail_info = intelligent_select(
            test_case['user_profile'],
            test_case['market_state']
        )
