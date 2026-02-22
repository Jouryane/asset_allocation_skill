"""
用户画像解析模块
将非结构化/半结构化的用户输入转换为结构化字段
"""

import re
from typing import Dict, Optional, Tuple
from enum import Enum

class RiskLevel(Enum):
    """风险承受能力等级"""
    VERY_CONSERVATIVE = 1  # 非常保守
    CONSERVATIVE = 2  # 保守
    MODERATE = 3  # 稳健
    AGGRESSIVE = 4  # 激进
    VERY_AGGRESSIVE = 5  # 非常激进

class CareerStage(Enum):
    """职业生涯阶段"""
    EARLY = "职业生涯起步"  # 0-5年
    STABLE = "职业生涯稳健期"  # 6-15年
    LATE = "职业生涯中后期"  # 16年以上

class UserProfileParser:
    """用户画像解析器"""
    
    def __init__(self):
        self.patterns = {
            # 年龄模式
            'age': [
                r'(\d+)\s*岁',
                r'年龄[：:]\s*(\d+)',
                r'我今年\s*(\d+)\s*岁',
                r'(\d+)\s*周岁',
                r'(\d+)\s*years?\s*old',
            ],
            # 年收入模式
            'annual_income': [
                r'年(?:收入|薪|收入)[：:]\s*(\d+(?:\.\d+)?)\s*万',
                r'年(?:收入|薪|收入)[：:]\s*(\d+(?:\.\d+)?)\s*元',
                r'年(?:收入|薪|收入)[：:]\s*(\d+(?:\.\d+)?)\s*k',
                r'收入\s*(\d+(?:\.\d+)?)\s*万',
                r'年薪\s*(\d+(?:\.\d+)?)\s*万',
                r'收入在\s*年\s*(\d+(?:\.\d+)?)\s*万',
                r'收入在\s*年\s*(\d+(?:\.\d+)?)\s*人民币',
                r'目前收入在\s*年\s*(\d+(?:\.\d+)?)\s*万',
                r'目前收入在\s*年\s*(\d+(?:\.\d+)?)\s*人民币',
            ],
            # 月支出模式
            'monthly_expense': [
                r'月(?:支出|开支|消费)[：:]\s*(\d+(?:\.\d+)?)\s*万',
                r'月(?:支出|开支|消费)[：:]\s*(\d+(?:\.\d+)?)\s*元',
                r'月(?:支出|开支|消费)[：:]\s*(\d+(?:\.\d+)?)\s*k',
                r'每月(?:支出|开支|消费)\s*(\d+(?:\.\d+)?)\s*万',
                r'每月(?:支出|开支|消费)\s*(\d+(?:\.\d+)?)\s*元',
                r'每月开支在\s*(\d+(?:\.\d+)?)\s*人民币',
                r'月开支在\s*(\d+(?:\.\d+)?)\s*人民币',
                r'月开支在\s*(\d+(?:\.\d+)?)\s*元',
            ],
            # 总资金模式
            'total_capital': [
                r'资金\s*(\d+(?:\.\d+)?)\s*万',
                r'总资金\s*(\d+(?:\.\d+)?)\s*万',
                r'可投资金额\s*(\d+(?:\.\d+)?)\s*万',
                r'可支配金融资产\s*(\d+(?:\.\d+)?)\s*万',
                r'资金\s*(\d+(?:\.\d+)?)\s*元',
                r'总资金\s*(\d+(?:\.\d+)?)\s*元',
                r'可投资金额\s*(\d+(?:\.\d+)?)\s*元',
                r'可支配金融资产\s*(\d+(?:\.\d+)?)\s*元',
                r'大约\s*(\d+(?:\.\d+)?)\s*万',
                r'资金大约是\s*(\d+(?:\.\d+)?)\s*万',
                r'资金大约是\s*(\d+(?:\.\d+)?)\s*人民币',
                r'目前我的资金大约是\s*(\d+(?:\.\d+)?)\s*万',
                r'目前我的资金大约是\s*(\d+(?:\.\d+)?)\s*人民币',
            ],
            # 风险偏好模式
            'risk_preference': [
                r'风险(?:偏好|承受能力|等级)[：:]\s*(保守|稳健|激进|平衡|中性|低|中|高)',
                r'我是\s*(保守|稳健|激进|平衡|中性)型',
                r'风险承受能力\s*(\d+)\s*级',
                r'风险等级\s*(\d+)',
            ],
            # 投资经验模式
            'investment_experience': [
                r'投资经验[：:]\s*(丰富|一般|匮乏|较少|较多|无)',
                r'投资经验\s*(丰富|一般|匮乏|较少|较多|无)',
                r'有(丰富|一般|匮乏|较少|较多)\s*投资经验',
                r'没有投资经验',
                r'投资经验较少',
                r'投资经验匮乏',
            ],
            # 职业阶段模式
            'career_stage': [
                r'职业生涯(?:阶段|时期)[：:]\s*(起步|稳健|中后期|早期|中期|后期)',
                r'工作年限\s*(\d+)\s*年',
            ],
            # 婚姻状态模式
            'marital_status': [
                r'(已婚|单身|离异)',
            ],
            # 负债状态模式
            'debt_status': [
                r'(有|无)\s*负债',
                r'负债\s*(\d+(?:\.\d+)?)\s*万',
            ],
        }
    
    def parse_text(self, text: str) -> Dict[str, any]:
        """
        解析用户输入的文本，提取结构化字段
        
        :param text: 用户输入的文本
        :return: 包含结构化字段的字典
        """
        result = {
            'age': None,
            'annual_income': None,
            'monthly_expense': None,
            'total_capital': None,
            'risk_preference': None,
            'risk_level': None,
            'investment_experience': None,
            'career_stage': None,
            'marital_status': None,
            'debt_status': None,
            'work_years': None,
        }
        
        # 提取年龄
        result['age'] = self._extract_value(text, self.patterns['age'])
        
        # 提取年收入
        result['annual_income'] = self._extract_financial_value(text, self.patterns['annual_income'])
        
        # 提取月支出
        result['monthly_expense'] = self._extract_financial_value(text, self.patterns['monthly_expense'])
        
        # 提取总资金
        result['total_capital'] = self._extract_financial_value(text, self.patterns['total_capital'])
        
        # 提取风险偏好
        result['risk_preference'] = self._extract_text_value(text, self.patterns['risk_preference'])
        
        # 提取投资经验
        result['investment_experience'] = self._extract_text_value(text, self.patterns['investment_experience'])
        
        # 提取职业阶段
        result['career_stage'] = self._extract_text_value(text, self.patterns['career_stage'])
        
        # 提取婚姻状态
        result['marital_status'] = self._extract_text_value(text, self.patterns['marital_status'])
        
        # 提取负债状态
        result['debt_status'] = self._extract_debt_status(text)
        
        # 解析风险等级
        result['risk_level'] = self._parse_risk_level(result['risk_preference'])
        
        # 解析职业生涯阶段
        result['career_stage'] = self._parse_career_stage(result['career_stage'], result['work_years'])
        
        return result
    
    def _extract_value(self, text: str, patterns: list) -> Optional[float]:
        """
        从文本中提取数值
        
        :param text: 输入文本
        :param patterns: 正则表达式模式列表
        :return: 提取的数值
        """
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(1))
                except (ValueError, IndexError):
                    continue
        return None
    
    def _extract_text_value(self, text: str, patterns: list) -> Optional[str]:
        """
        从文本中提取文本值
        
        :param text: 输入文本
        :param patterns: 正则表达式模式列表
        :return: 提取的文本值
        """
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return match.group(1)
                except IndexError:
                    continue
        return None
    
    def _extract_financial_value(self, text: str, patterns: list) -> Optional[float]:
        """
        从文本中提取财务数值（自动识别单位）
        
        :param text: 输入文本
        :param patterns: 正则表达式模式列表
        :return: 提取的财务数值（单位：万元）
        """
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    value = float(match.group(1))
                    matched_text = match.group(0)
                    
                    # 检查是否包含"万"字
                    if '万' in matched_text:
                        return value
                    # 检查是否包含"元"字
                    elif '元' in matched_text or '人民币' in matched_text:
                        # 如果数值大于1000，可能是以元为单位，需要转换为万元
                        if value >= 1000:
                            return value / 10000
                        else:
                            return value
                    # 检查是否包含"k"或"K"
                    elif 'k' in matched_text.lower():
                        return value / 10000  # 转换为万元
                    else:
                        return value
                except (ValueError, IndexError):
                    continue
        return None
    
    def _extract_debt_status(self, text: str) -> Optional[Dict[str, any]]:
        """
        提取负债状态
        
        :param text: 输入文本
        :return: 负债状态字典
        """
        # 检查是否有负债
        if re.search(r'有负债', text):
            # 尝试提取负债金额
            debt_match = re.search(r'负债\s*(\d+(?:\.\d+)?)\s*万', text)
            if debt_match:
                return {
                    'has_debt': True,
                    'debt_amount': float(debt_match.group(1))
                }
            else:
                return {
                    'has_debt': True,
                    'debt_amount': None
                }
        elif re.search(r'无负债|没有负债', text):
            return {
                'has_debt': False,
                'debt_amount': 0
            }
        else:
            return {
                'has_debt': None,
                'debt_amount': None
            }
    
    def _parse_risk_level(self, risk_preference: Optional[str]) -> Optional[int]:
        """
        解析风险等级
        
        :param risk_preference: 风险偏好文本
        :return: 风险等级（1-5）
        """
        if risk_preference is None:
            return None
        
        # 文本映射到等级
        risk_mapping = {
            '非常保守': RiskLevel.VERY_CONSERVATIVE.value,
            '保守': RiskLevel.CONSERVATIVE.value,
            '低': RiskLevel.CONSERVATIVE.value,
            '稳健': RiskLevel.MODERATE.value,
            '平衡': RiskLevel.MODERATE.value,
            '中性': RiskLevel.MODERATE.value,
            '中': RiskLevel.MODERATE.value,
            '激进': RiskLevel.AGGRESSIVE.value,
            '高': RiskLevel.AGGRESSIVE.value,
            '非常激进': RiskLevel.VERY_AGGRESSIVE.value,
        }
        
        # 检查是否是数字等级
        if risk_preference.isdigit():
            level = int(risk_preference)
            if 1 <= level <= 5:
                return level
        
        # 检查文本映射
        for key, level in risk_mapping.items():
            if key in risk_preference:
                return level
        
        return None
    
    def _parse_career_stage(self, career_stage: Optional[str], work_years: Optional[float]) -> Optional[str]:
        """
        解析职业生涯阶段
        
        :param career_stage: 职业阶段文本
        :param work_years: 工作年限
        :return: 职业生涯阶段
        """
        # 如果已经明确指定了阶段
        if career_stage:
            if '起步' in career_stage or '早期' in career_stage:
                return CareerStage.EARLY.value
            elif '稳健' in career_stage or '中期' in career_stage:
                return CareerStage.STABLE.value
            elif '中后期' in career_stage or '后期' in career_stage:
                return CareerStage.LATE.value
        
        # 如果有工作年限，根据年限推断
        if work_years is not None:
            if work_years <= 5:
                return CareerStage.EARLY.value
            elif work_years <= 15:
                return CareerStage.STABLE.value
            else:
                return CareerStage.LATE.value
        
        return None
    
    def validate_profile(self, profile: Dict[str, any]) -> Dict[str, any]:
        """
        验证用户画像的完整性和合理性
        
        :param profile: 用户画像字典
        :return: 包含验证结果和建议的字典
        """
        validation = {
            'is_valid': True,
            'missing_fields': [],
            'warnings': [],
            'suggestions': []
        }
        
        # 检查必填字段
        required_fields = ['age', 'annual_income', 'total_capital']
        for field in required_fields:
            if profile.get(field) is None:
                validation['is_valid'] = False
                validation['missing_fields'].append(field)
        
        # 检查年龄合理性
        if profile.get('age') is not None:
            age = profile['age']
            if age < 18 or age > 80:
                validation['warnings'].append(f"年龄{age}岁不在合理范围（18-80岁）")
        
        # 检查收入与资金的关系
        if profile.get('annual_income') and profile.get('total_capital'):
            annual_income = profile['annual_income']
            total_capital = profile['total_capital']
            if total_capital > annual_income * 10:
                validation['warnings'].append(f"总资金（{total_capital}万）超过年收入的10倍，请确认")
        
        # 检查风险等级
        if profile.get('risk_level') is None:
            validation['suggestions'].append("未明确风险偏好，建议根据年龄和经验设定")
        
        # 检查月支出
        if profile.get('monthly_expense') is None:
            validation['suggestions'].append("未提供月支出信息，可能影响流动性管理建议")
        
        return validation
    
    def format_profile(self, profile: Dict[str, any]) -> str:
        """
        格式化用户画像为易读的文本
        
        :param profile: 用户画像字典
        :return: 格式化后的文本
        """
        lines = []
        lines.append("=" * 80)
        lines.append("用户画像结构化解析结果")
        lines.append("=" * 80)
        lines.append("")
        
        # 基础属性
        lines.append("【基础属性】")
        if profile.get('age'):
            lines.append(f"  年龄：{profile['age']}岁")
        if profile.get('risk_level'):
            risk_level_map = {
                1: "非常保守",
                2: "保守",
                3: "稳健",
                4: "激进",
                5: "非常激进",
            }
            lines.append(f"  风险承受能力：{risk_level_map.get(profile['risk_level'], '未知')}（等级{profile['risk_level']}）")
        if profile.get('career_stage'):
            lines.append(f"  职业生涯阶段：{profile['career_stage']}")
        if profile.get('investment_experience'):
            lines.append(f"  投资经验：{profile['investment_experience']}")
        if profile.get('marital_status'):
            lines.append(f"  婚姻状态：{profile['marital_status']}")
        lines.append("")
        
        # 财务属性
        lines.append("【财务属性】")
        if profile.get('annual_income'):
            lines.append(f"  年收入：{profile['annual_income']:.2f}万元")
        if profile.get('monthly_expense'):
            lines.append(f"  月支出：{profile['monthly_expense']:.2f}万元")
        if profile.get('total_capital'):
            lines.append(f"  可投资金额：{profile['total_capital']:.2f}万元")
        if profile.get('debt_status'):
            debt = profile['debt_status']
            if debt.get('has_debt'):
                if debt.get('debt_amount'):
                    lines.append(f"  负债状态：有负债（{debt['debt_amount']:.2f}万元）")
                else:
                    lines.append(f"  负债状态：有负债")
            else:
                lines.append(f"  负债状态：无负债")
        lines.append("")
        
        lines.append("=" * 80)
        return "\n".join(lines)
    
    def export_to_strategy_params(self, profile: Dict[str, any]) -> Dict[str, any]:
        """
        将用户画像转换为strategy.py所需的参数
        
        :param profile: 用户画像字典
        :return: strategy.py参数字典
        """
        params = {}
        
        # 基础参数
        if profile.get('age'):
            params['age'] = int(profile['age'])
        
        if profile.get('annual_income'):
            params['annual_income'] = float(profile['annual_income']) * 10000  # 转换为元
        
        if profile.get('total_capital'):
            params['total_capital'] = float(profile['total_capital']) * 10000  # 转换为元
        
        if profile.get('monthly_expense'):
            params['monthly_expense'] = float(profile['monthly_expense']) * 10000  # 转换为元
        
        # 风险等级
        if profile.get('risk_level'):
            params['risk_level'] = profile['risk_level']
        
        # 投资经验
        if profile.get('investment_experience'):
            exp_map = {
                '丰富': '丰富',
                '一般': '一般',
                '匮乏': '匮乏',
                '较少': '较少',
                '较多': '较多',
                '无': '无',
            }
            params['investment_experience'] = exp_map.get(profile['investment_experience'], '一般')
        
        # 职业生涯阶段
        if profile.get('career_stage'):
            params['career_stage'] = profile['career_stage']
        
        return params


def parse_user_profile(text: str) -> Tuple[Dict[str, any], Dict[str, any]]:
    """
    解析用户画像的主函数
    
    :param text: 用户输入的文本
    :return: (用户画像字典, 验证结果字典)
    """
    parser = UserProfileParser()
    
    # 解析文本
    profile = parser.parse_text(text)
    
    # 验证画像
    validation = parser.validate_profile(profile)
    
    return profile, validation


if __name__ == "__main__":
    # 测试用例
    test_cases = [
        "我是一位34岁的男性、目前收入在年30万人民币，投资经验比较匮乏，主要是进行存款，但现在想要学习一些股票基金投资，已婚，没有任何负债，目前我的资金大约是100万人民币，每月开支在10000人民币左右。",
        "35岁，年收入50万，月支出8000元，可投资金额100万，风险等级3（稳健型）",
        "年龄40岁，年薪80万，总资金200万，月支出1.5万，已婚有负债50万，投资经验一般，风险偏好激进",
        "我今年28岁，工作3年，年收入35万，资金80万，无负债，投资经验较少，风险承受能力2级（保守）",
    ]
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"测试用例 {i}")
        print(f"{'='*80}")
        print(f"输入文本：{test_text}")
        print()
        
        profile, validation = parse_user_profile(test_text)
        
        # 创建解析器实例用于格式化
        parser = UserProfileParser()
        
        # 显示解析结果
        print(parser.format_profile(profile))
        print()
        
        # 显示验证结果
        if not validation['is_valid']:
            print("⚠️  警告：")
            for warning in validation['warnings']:
                print(f"  - {warning}")
            print()
            print("❌ 缺失字段：")
            for field in validation['missing_fields']:
                print(f"  - {field}")
        else:
            print("✅ 用户画像验证通过")
        
        if validation['suggestions']:
            print()
            print("💡 建议：")
            for suggestion in validation['suggestions']:
                print(f"  - {suggestion}")
        
        # 显示strategy.py参数
        print()
        print("【转换为strategy.py参数】")
        strategy_params = parser.export_to_strategy_params(profile)
        for key, value in strategy_params.items():
            print(f"  {key}: {value}")
