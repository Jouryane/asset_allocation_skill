"""
用户画像解析与资产配置集成示例
展示如何使用user_profile_parser模块解析用户输入，并将其转换为strategy.py的参数
"""

from user_profile_parser import UserProfileParser
import sys
import os

def analyze_user_profile(user_text: str):
    """
    分析用户画像并生成资产配置建议
    
    :param user_text: 用户输入的文本
    """
    print("=" * 80)
    print("用户画像解析与资产配置分析")
    print("=" * 80)
    print()
    
    # 步骤1：解析用户画像
    print("【步骤1】解析用户画像")
    print("-" * 80)
    
    parser = UserProfileParser()
    profile = parser.parse_text(user_text)
    
    # 显示解析结果
    print(parser.format_profile(profile))
    print()
    
    # 验证画像
    validation = parser.validate_profile(profile)
    
    if not validation['is_valid']:
        print("⚠️  警告：")
        for warning in validation['warnings']:
            print(f"  - {warning}")
        print()
        print("❌ 缺失必填字段：")
        for field in validation['missing_fields']:
            print(f"  - {field}")
        print()
        print("请补充完整信息后重新分析。")
        return
    
    if validation['suggestions']:
        print("💡 建议：")
        for suggestion in validation['suggestions']:
            print(f"  - {suggestion}")
        print()
    
    # 步骤2：转换为strategy.py参数
    print("【步骤2】转换为strategy.py参数")
    print("-" * 80)
    
    strategy_params = parser.export_to_strategy_params(profile)
    for key, value in strategy_params.items():
        print(f"  {key}: {value}")
    print()
    
    # 步骤3：计算进取系数建议
    print("【步骤3】进取系数建议（基于Asset Allocation basic）")
    print("-" * 80)
    
    aggressiveness_suggestion = calculate_aggressiveness(profile)
    print(aggressiveness_suggestion)
    print()
    
    # 步骤4：风险管理分析
    print("【步骤4】风险管理分析")
    print("-" * 80)
    
    risk_analysis = analyze_risk_management(profile)
    print(risk_analysis)
    print()
    
    # 步骤5：流动性管理分析
    print("【步骤5】流动性管理分析")
    print("-" * 80)
    
    liquidity_analysis = analyze_liquidity_management(profile)
    print(liquidity_analysis)
    print()
    
    # 步骤6：资产配置建议
    print("【步骤6】资产配置建议")
    print("-" * 80)
    
    asset_allocation = generate_asset_allocation(profile, aggressiveness_suggestion)
    print(asset_allocation)
    print()
    
    # 步骤7：执行strategy.py（可选）
    print("【步骤7】执行strategy.py（可选）")
    print("-" * 80)
    print("如需执行具体的投资策略，请运行以下命令：")
    print()
    cmd = f"python strategy.py"
    for key, value in strategy_params.items():
        cmd += f" --{key} {value}"
    print(f"  {cmd}")
    print()
    print("或者使用Aggressive Asset Allocation strategy功能进行具体的选品和仓位配置。")
    print()
    
    return {
        'profile': profile,
        'validation': validation,
        'strategy_params': strategy_params,
        'aggressiveness_suggestion': aggressiveness_suggestion,
    }


def calculate_aggressiveness(profile: dict) -> str:
    """
    根据用户画像计算进取系数建议
    
    :param profile: 用户画像字典
    :return: 进取系数建议文本
    """
    lines = []
    
    # 获取风险等级
    risk_level = profile.get('risk_level')
    if risk_level is None:
        # 根据年龄和投资经验推断风险等级
        age = profile.get('age', 30)
        experience = profile.get('investment_experience', '一般')
        
        if age < 35 and experience in ['丰富', '较多']:
            risk_level = 4  # 激进
        elif age < 35:
            risk_level = 3  # 稳健
        elif age < 50:
            risk_level = 3  # 稳健
        else:
            risk_level = 2  # 保守
        
        lines.append(f"  根据年龄({age}岁)和投资经验({experience})推断风险等级：{risk_level}级")
    
    # 获取职业生涯阶段
    career_stage = profile.get('career_stage')
    if career_stage is None:
        age = profile.get('age', 30)
        if age <= 35:
            career_stage = "职业生涯起步"
        elif age <= 50:
            career_stage = "职业生涯稳健期"
        else:
            career_stage = "职业生涯中后期"
        lines.append(f"  根据年龄推断职业生涯阶段：{career_stage}")
    
    # 进取系数建议表
    aggressiveness_table = {
        ("职业生涯起步", 1): 0.15,
        ("职业生涯起步", 2): 0.15,
        ("职业生涯起步", 3): 0.35,
        ("职业生涯起步", 4): 0.65,
        ("职业生涯起步", 5): 0.65,
        ("职业生涯稳健期", 1): 0.25,
        ("职业生涯稳健期", 2): 0.25,
        ("职业生涯稳健期", 3): 0.50,
        ("职业生涯稳健期", 4): 0.80,
        ("职业生涯稳健期", 5): 0.80,
        ("职业生涯中后期", 1): 0.10,
        ("职业生涯中后期", 2): 0.10,
        ("职业生涯中后期", 3): 0.25,
        ("职业生涯中后期", 4): 0.60,
        ("职业生涯中后期", 5): 0.60,
    }
    
    # 获取进取系数
    aggressiveness = aggressiveness_table.get((career_stage, risk_level), 0.25)
    
    lines.append(f"  风险等级：{risk_level}级")
    lines.append(f"  职业生涯阶段：{career_stage}")
    lines.append(f"  建议进取系数：{aggressiveness:.2f}（进取类资产占比）")
    lines.append("")
    lines.append("  说明：")
    lines.append("  - 进取系数是指为追求目标配置方案，用户选取进取类资产的投资比例")
    lines.append("  - 金融知识、投资经验相对匮乏的用户优先关注风险管理项目，选择相对低的进取系数")
    lines.append("  - 每月盈余状态不佳的用户优先关注流动性管理项目")
    
    return "\n".join(lines)


def analyze_risk_management(profile: dict) -> str:
    """
    分析风险管理
    
    :param profile: 用户画像字典
    :return: 风险管理分析文本
    """
    lines = []
    
    age = profile.get('age', 30)
    risk_level = profile.get('risk_level', 3)
    experience = profile.get('investment_experience', '一般')
    total_capital = profile.get('total_capital', 0)
    
    # 如果risk_level为None，使用默认值3
    if risk_level is None:
        risk_level = 3
    
    lines.append(f"  用户年龄：{age}岁")
    lines.append(f"  风险等级：{risk_level}级")
    lines.append(f"  投资经验：{experience}")
    lines.append(f"  总资金：{total_capital:.2f}万元")
    lines.append("")
    
    # 风险承受能力评估
    if risk_level <= 2:
        lines.append("  风险承受能力：较低")
        lines.append("  建议：")
        lines.append("  - 优先选择低风险资产（如货币基金、国债）")
        lines.append("  - 进取类资产占比控制在15%-25%以内")
        lines.append("  - 注重资产保值，避免大幅回撤")
    elif risk_level == 3:
        lines.append("  风险承受能力：中等")
        lines.append("  建议：")
        lines.append("  - 平衡配置稳健类和进取类资产")
        lines.append("  - 进取类资产占比控制在25%-50%之间")
        lines.append("  - 可适当配置指数基金、债券基金等")
    else:
        lines.append("  风险承受能力：较高")
        lines.append("  建议：")
        lines.append("  - 可配置较高比例的进取类资产")
        lines.append("  - 进取类资产占比可达到50%-80%")
        lines.append("  - 注意分散投资，控制单一资产风险")
    
    lines.append("")
    lines.append("  风险管理优先级：⭐⭐⭐⭐⭐")
    lines.append("  - 直接关系到用户的资产安全和长期收益")
    lines.append("  - 确保资产配置方案中的进取类资产占比小于等于用户的进取系数")
    lines.append("  - 一旦超出将触发预警 ⚠️")
    
    return "\n".join(lines)


def analyze_liquidity_management(profile: dict) -> str:
    """
    分析流动性管理
    
    :param profile: 用户画像字典
    :return: 流动性管理分析文本
    """
    lines = []
    
    monthly_expense = profile.get('monthly_expense', 0)
    total_capital = profile.get('total_capital', 0)
    
    lines.append(f"  月支出：{monthly_expense:.2f}万元")
    lines.append(f"  总资金：{total_capital:.2f}万元")
    lines.append("")
    
    # 计算流动性需求
    liquidity_need_3m = monthly_expense * 3  # 三个月支出
    liquidity_need_6m = monthly_expense * 6  # 六个月支出
    
    lines.append(f"  流动性需求（3个月）：{liquidity_need_3m:.2f}万元")
    lines.append(f"  流动性需求（6个月）：{liquidity_need_6m:.2f}万元")
    lines.append("")
    
    # 流动性配置建议
    if monthly_expense == 0:
        lines.append("  ⚠️  未提供月支出信息，无法准确计算流动性需求")
        lines.append("  建议：补充月支出信息以便进行流动性管理")
    else:
        liquidity_ratio = (liquidity_need_3m / total_capital) * 100 if total_capital > 0 else 0
        lines.append(f"  流动性资金占比建议：{liquidity_ratio:.1f}%（3个月支出）")
        lines.append("")
        lines.append("  流动性配置建议：")
        lines.append("  - 货币基金：满足日常消费和应急资金需求")
        lines.append("  - 短期理财：满足未来3-6个月的确定性支出")
        lines.append("  - 确保流动性资金能够覆盖资金需求")
    
    lines.append("")
    lines.append("  流动性管理优先级：⭐⭐⭐⭐")
    lines.append("  - 直接关系到用户的资金需求和应急资金需求")
    lines.append("  - 确保资产组合的资金能够满足用户的资金需求")
    lines.append("  - 一旦流动性资金配置低于三个月内的每月必要支出将触发预警 ⚠️")
    
    return "\n".join(lines)


def generate_asset_allocation(profile: dict, aggressiveness_suggestion: str) -> str:
    """
    生成资产配置建议
    
    :param profile: 用户画像字典
    :param aggressiveness_suggestion: 进取系数建议文本
    :return: 资产配置建议文本
    """
    lines = []
    
    total_capital = profile.get('total_capital', 0)
    monthly_expense = profile.get('monthly_expense', 0)
    risk_level = profile.get('risk_level', 3)
    
    # 提取进取系数
    aggressiveness = 0.25  # 默认值
    for line in aggressiveness_suggestion.split('\n'):
        if '建议进取系数' in line:
            try:
                aggressiveness = float(line.split('：')[-1].split('（')[0].strip())
            except (ValueError, IndexError):
                pass
            break
    
    # 计算各类资产配置
    liquidity_amount = monthly_expense * 3  # 流动性资产（3个月支出）
    aggressive_amount = (total_capital - liquidity_amount) * aggressiveness  # 进取类资产
    stable_amount = total_capital - liquidity_amount - aggressive_amount  # 稳健类资产
    
    lines.append(f"  总资金：{total_capital:.2f}万元")
    lines.append("")
    lines.append("  资产配置方案：")
    lines.append(f"  ┌─────────────────────────────────────────────────────────┐")
    lines.append(f"  │ 活钱管理（流动性资产）：{liquidity_amount:8.2f}万元（{liquidity_amount/total_capital*100:5.1f}%） │")
    lines.append(f"  ├─────────────────────────────────────────────────────────┤")
    lines.append(f"  │ 稳健投资（稳健类资产）：{stable_amount:8.2f}万元（{stable_amount/total_capital*100:5.1f}%） │")
    lines.append(f"  ├─────────────────────────────────────────────────────────┤")
    lines.append(f"  │ 进取投资（进取类资产）：{aggressive_amount:8.2f}万元（{aggressive_amount/total_capital*100:5.1f}%） │")
    lines.append(f"  └─────────────────────────────────────────────────────────┘")
    lines.append("")
    lines.append("  资产配置说明：")
    lines.append("  【活钱管理】")
    lines.append("  - 目的：满足日常消费和应急资金需求")
    lines.append("  - 配置：货币基金、短期理财、活期存款")
    lines.append("  - 特点：高流动性、低风险、收益稳定")
    lines.append("")
    lines.append("  【稳健投资】")
    lines.append("  - 目的：在控制风险的前提下获得稳定收益")
    lines.append("  - 配置：债券基金、货币基金、银行理财")
    lines.append("  - 特点：中等风险、中等收益、流动性较好")
    lines.append("")
    lines.append("  【进取投资】")
    lines.append("  - 目的：追求长期资本增值")
    lines.append("  - 配置：股票基金、指数基金、混合基金")
    lines.append("  - 特点：高风险、高收益、流动性一般")
    lines.append("")
    lines.append("  下一步操作：")
    lines.append("  1. 配置config.yaml文件，填入目标投资标的")
    lines.append("  2. 配置dingding.py文件，填入钉钉机器人webhook地址")
    lines.append("  3. 使用'配置战术'、'帮我选品'、'买什么'等指令触发Aggressive Asset Allocation strategy功能")
    lines.append("  4. 根据选品结果进行具体的仓位配置")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # 测试用例
    test_user_text = """
    我是一位34岁的男性、目前收入在年30万人民币，投资经验比较匮乏，
    主要是进行存款，但现在想要学习一些股票基金投资，已婚，没有任何负债，
    目前我的资金大约是100万人民币，每月开支在10000人民币左右。
    """
    
    # 执行分析
    result = analyze_user_profile(test_user_text)
    
    print("=" * 80)
    print("分析完成")
    print("=" * 80)
