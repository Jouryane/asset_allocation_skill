import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import akshare as ak
import yaml
import sys
import os
import argparse

warnings.filterwarnings('ignore')

# 添加dingding模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class NonlinearTwoStepInvestmentStrategy:
    """
    非线性两步法ETF投资策略
    核心改进：使用非线性函数处理估值分位到仓位的映射
    
    估值分位 vs 仓位的关系：
    - 0% 估值 -> 100% 仓位（极端低估，满仓）
    - 50% 估值 -> 50% 仓位（正常估值，半仓）
    - 100% 估值 -> 0% 仓位（极端高估，空仓）
    """
    
    def __init__(self, 
                 total_capital=1000000,
                 lookback_years=5,
                 rebalance_freq='Q',
                 nonlinear_type='sigmoid',  # 'sigmoid', 'power', 'custom'
                 aggressiveness=1.0,  # 激进程度：>1更激进，<1更保守
                 lambda_decay=0.95,  # 衰减因子，用于加权百分位计算
                 winsorize_pct=0.05):  # 缩尾处理比例，用于削弱极端值
        
        self.total_capital = total_capital
        self.lookback_years = lookback_years
        self.rebalance_freq = rebalance_freq
        self.aggressiveness = aggressiveness
        self.lambda_decay = lambda_decay
        self.winsorize_pct = winsorize_pct
        
        # 非线性函数类型
        self.nonlinear_type = nonlinear_type
        
        # 存储ETF数据
        self.etf_data = {}
        
        # ETF到指数的映射表
        self.etf_to_index = {
            "510050": "000016",  # 上证50ETF → 上证50指数
            "510880": "000015",  # 红利ETF → 红利指数
            "516950": "930608"   # 碳中和ETF → 中证芯片
        }
        
        # ETF名称映射
        self.etf_names = {
            "510050": "上证50ETF",
            "510880": "红利ETF",
            "516950": "碳中和ETF"
        }
    
    def load_config(self):
        """加载配置文件"""
        with open("d:/agent skills/asset_allocation/config.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    
    def get_etf_valuation_data(self, etf_code):
        """
        获取ETF的估值数据
        :param etf_code: ETF代码
        :return: 包含历史估值数据的DataFrame
        """
        try:
            # 映射到指数代码
            if etf_code not in self.etf_to_index:
                print(f"ETF {etf_code} 无匹配的指数代码")
                return None
            
            index_code = self.etf_to_index[etf_code]
            
            # 获取指数估值数据
            df = ak.stock_zh_index_value_csindex(symbol=index_code)
            
            if df.empty:
                print(f"指数 {index_code} 无估值数据")
                return None
            
            # 重命名列以便统一处理
            df = df.rename(columns={'市盈率1': 'pe', '日期': 'date'})
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            return df
        except Exception as e:
            print(f"获取ETF {etf_code} 估值数据失败：{str(e)}")
            return None
    
    def load_etf_data(self, etf_codes):
        """
        加载指定ETF的数据
        :param etf_codes: ETF代码列表
        """
        print("正在获取ETF估值数据...")
        
        for etf_code in etf_codes:
            data = self.get_etf_valuation_data(etf_code)
            if data is not None:
                etf_name = self.etf_names.get(etf_code, etf_code)
                self.etf_data[etf_name] = data
                print(f"  ✓ {etf_name} ({etf_code}) 数据加载成功")
            else:
                print(f"  ✗ {etf_code} 数据加载失败")
        
        print(f"\n成功加载 {len(self.etf_data)} 个ETF的数据")
        return self.etf_data
    
    def winsorize(self, data, pct):
        """
        缩尾处理，削弱极端值的影响
        :param data: 数据序列
        :param pct: 缩尾比例（如0.05表示两端各5%）
        :return: 缩尾后的数据
        """
        if len(data) == 0:
            return data
        
        lower_bound = np.percentile(data, pct * 100)
        upper_bound = np.percentile(data, (1 - pct) * 100)
        
        winsorized_data = np.clip(data, lower_bound, upper_bound)
        return winsorized_data
    
    def calculate_weighted_percentile(self, data, column='pe'):
        """
        计算加权百分位，削弱极端行情的干扰
        
        公式：p_final = Σ(λ^(T-t) * I(winsorize(x_t) < winsorize(x_current))) / Σ(λ^(T-t))
        
        其中：
        - λ：衰减因子（lambda_decay），通常取0.9-0.99
        - T：历史数据总期数
        - t：时间索引（t=1表示最早，t=T表示当前）
        - I(·)：指示函数，条件为真时为1，否则为0
        - winsorize(·)：缩尾处理函数
        
        :param data: 历史估值数据
        :param column: 估值列名
        :return: 加权百分位
        """
        if len(data) == 0:
            return 0.0
        
        # 获取当前值
        current_value = data[column].iloc[-1]
        
        # 对历史数据进行缩尾处理
        historical_values = data[column].values
        winsorized_values = self.winsorize(historical_values, self.winsorize_pct)
        
        # 对当前值进行缩尾处理
        winsorized_current = self.winsorize(np.array([current_value]), self.winsorize_pct)[0]
        
        # 计算加权百分位
        T = len(historical_values)
        weights = []
        indicators = []
        
        for t in range(T):
            # 计算权重：λ^(T-t)
            weight = self.lambda_decay ** (T - t)
            weights.append(weight)
            
            # 计算指示函数：I(winsorize(x_t) < winsorize(x_current))
            indicator = 1 if winsorized_values[t] < winsorized_current else 0
            indicators.append(indicator)
        
        # 计算加权百分位
        weighted_sum = sum(w * i for w, i in zip(weights, indicators))
        total_weight = sum(weights)
        
        weighted_percentile = (weighted_sum / total_weight) * 100 if total_weight > 0 else 50.0
        
        return weighted_percentile, current_value
    
    def nonlinear_position_sizing(self, percentile):
        """
        非线性仓位计算（核心改进）
        
        输入：估值分位 percentile (0-100)
        输出：建议仓位 (0-1)
        
        不同非线性函数的对比：
        1. 线性：position = 1 - percentile/100  # 简单但过于保守
        2. Sigmoid：在中间区域更敏感，两端更钝化
        3. 幂函数：根据不同指数调整激进程度
        4. 自定义：完全手工调整关键点
        """
        # 归一化到0-1
        x = percentile / 100
        
        if self.nonlinear_type == 'linear':
            # 线性基准
            position = 1 - x
            
        elif self.nonlinear_type == 'sigmoid':
            # Sigmoid函数：在中性区域更敏感
            # 调整参数使f(0.5)=0.5
            k = 5 * self.aggressiveness  # 斜率参数
            position = 1 / (1 + np.exp(k * (x - 0.5)))
            
        elif self.nonlinear_type == 'power':
            # 幂函数：根据不同指数调整激进程度
            # power < 1: 更激进（估值<50%时仓位更高）
            # power > 1: 更保守
            power = 0.7 / self.aggressiveness  # 默认0.7，较激进
            position = (1 - x) ** power
            
        elif self.nonlinear_type == 'custom':
            # 自定义关键点
            # 估值分位: 0%, 20%, 50%, 80%, 100%
            # 对应仓位: 100%, 90%, 50%, 20%, 0%
            points_x = [0, 0.2, 0.5, 0.8, 1.0]
            points_y = [1.0, 0.9, 0.5, 0.2, 0.0]  # 非线性下降
            
            # 线性插值
            position = np.interp(x, points_x, points_y)
            
        else:
            # 默认使用幂函数
            position = (1 - x) ** 0.7
        
        # 确保在0-1范围内
        position = np.clip(position, 0, 1)
        
        return position
    
    def calculate_valuation_percentile(self, data, column='pe'):
        """计算估值分位数（使用加权百分位）"""
        return self.calculate_weighted_percentile(data, column)
    
    def calculate_market_valuation(self):
        """
        计算全市场估值水平 - 使用非线性仓位和加权百分位
        """
        all_percentiles = []
        
        for etf_name, data in self.etf_data.items():
            pe_percentile, _ = self.calculate_valuation_percentile(data, 'pe')
            all_percentiles.append(pe_percentile)
        
        # 使用加权平均，给大盘股权重更高
        market_percentile = np.percentile(all_percentiles, 50)  # 中位数
        
        # 非线性仓位计算
        macro_position = self.nonlinear_position_sizing(market_percentile)
        
        # 添加市场状态描述
        if market_percentile < 20:
            signal = '极度低估🔥'
        elif market_percentile < 40:
            signal = '低估💎'
        elif market_percentile < 60:
            signal = '合理⚖️'
        elif market_percentile < 80:
            signal = '高估⚠️'
        else:
            signal = '极度高估🚫'
            
        return {
            'market_percentile': market_percentile,
            'macro_position': macro_position,
            'signal': signal,
            'available_capital': self.total_capital * macro_position,
            'idle_capital': self.total_capital * (1 - macro_position)
        }
    
    def select_top_etfs(self, n_select=3, valuation_col='pe'):
        """
        选择性价比最高的ETF - 考虑行业轮动
        """
        etf_scores = []
        
        for etf_name, data in self.etf_data.items():
            percentile, current_val = self.calculate_valuation_percentile(data, valuation_col)
            
            # 改进的得分系统
            # 1. 估值得分（越低越好）
            valuation_score = 100 - percentile
            
            # 2. 动量得分（可选）- 短期趋势
            # 由于我们只有PE数据，无法计算动量，这里设为0
            momentum_score = 10  # 默认中等得分
            
            # 3. 波动率调整（可选）- 低波动加分
            # 由于我们只有PE数据，无法计算波动率，这里设为5
            volatility_score = 5  # 默认中等得分
            
            # 综合得分（可以调整权重）
            total_score = valuation_score * 0.8 + momentum_score * 0.1 + volatility_score * 0.1
            
            etf_scores.append({
                'name': etf_name,
                'percentile': percentile,
                'current_value': current_val,
                'valuation_score': valuation_score,
                'momentum_score': momentum_score,
                'volatility_score': volatility_score,
                'total_score': total_score,
                'latest_price': current_val  # 使用PE作为参考价格
            })
        
        # 按总得分排序
        etf_scores = sorted(etf_scores, key=lambda x: x['total_score'], reverse=True)
        selected = etf_scores[:n_select]
        
        return selected
    
    def calculate_nonlinear_weights(self, selected_etfs):
        """
        非线性权重分配 - 避免中庸配置
        让便宜的最便宜，贵的相对保守
        """
        percentiles = [etf['percentile'] for etf in selected_etfs]
        
        # 使用指数函数放大差异
        # 将估值分位转换为权重因子
        weights_raw = []
        for p in percentiles:
            # 估值分位越低，权重因子越大（非线性放大）
            # 例如：p=20 -> factor=4, p=50 -> factor=1, p=80 -> factor=0.25
            factor = ((100 - p) / 50) ** 2  # 平方放大差异
            weights_raw.append(factor)
        
        # 归一化
        total = sum(weights_raw)
        weights = [w / total for w in weights_raw]
        
        return weights
    
    def generate_investment_plan(self, selected_etfs, weights, macro_info):
        """生成投资计划"""
        plan = []
        available_capital = macro_info['available_capital']
        
        for etf, weight in zip(selected_etfs, weights):
            invest_amount = available_capital * weight
            shares = invest_amount / etf['latest_price']
            
            # 添加风险提示
            if etf['percentile'] < 20:
                risk_level = '低风险🔥'
            elif etf['percentile'] < 40:
                risk_level = '较低风险💎'
            elif etf['percentile'] < 60:
                risk_level = '中等风险⚖️'
            elif etf['percentile'] < 80:
                risk_level = '较高风险⚠️'
            else:
                risk_level = '高风险🚫'
            
            plan.append({
                'etf_name': etf['name'],
                'valuation_percentile': f"{etf['percentile']:.1f}%",
                'risk_level': risk_level,
                'momentum': f"{etf['momentum_score']:.1f}",
                'total_score': f"{etf['total_score']:.1f}",
                'weight': f"{weight*100:.1f}%",
                'invest_amount': f"¥{invest_amount:,.0f}",
                'estimated_shares': int(shares)
            })
        
        return plan
    
    def run_strategy(self):
        """运行完整策略"""
        print("="*80)
        print("非线性两步法ETF投资策略报告")
        print("="*80)
        print(f"报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"总资金: ¥{self.total_capital:,.0f}")
        print(f"非线性类型: {self.nonlinear_type}")
        print(f"激进系数: {self.aggressiveness}")
        print(f"衰减因子(λ): {self.lambda_decay}")
        print(f"缩尾比例: {self.winsorize_pct*100:.1f}%")
        print("-"*80)
        
        # 第一步：宏观仓位控制（非线性）
        print("\n【第一步】宏观仓位分析（使用加权百分位）")
        print("加权百分位公式：p_final = Σ(λ^(T-t) * I(winsorize(x_t) < winsorize(x_current))) / Σ(λ^(T-t))")
        print(f"其中：λ={self.lambda_decay}（衰减因子），缩尾比例={self.winsorize_pct*100:.1f}%")
        print()
        macro_info = self.calculate_market_valuation()
        
        print(f"全市场估值分位: {macro_info['market_percentile']:.1f}%")
        print(f"市场信号: {macro_info['signal']}")
        print(f"建议仓位: {macro_info['macro_position']*100:.1f}%")
        print(f"可用资金: ¥{macro_info['available_capital']:,.0f}")
        print(f"闲置资金: ¥{macro_info['idle_capital']:,.0f} (可放入货币基金)")
        
        # 第二步：选择标的（非线性权重）
        print("\n【第二步】标的筛选与权重分配")
        selected_etfs = self.select_top_etfs(n_select=3)
        
        print("\n性价比最高的3个ETF:")
        for i, etf in enumerate(selected_etfs, 1):
            print(f"  {i}. {etf['name']}")
            print(f"     - 估值分位: {etf['percentile']:.1f}%")
            print(f"     - 当前PE: {etf['current_value']:.2f}")
            print(f"     - 综合得分: {etf['total_score']:.1f}")
        
        # 非线性权重计算
        weights = self.calculate_nonlinear_weights(selected_etfs)
        
        print(f"\n【非线性权重分配】")
        print("（通过平方函数放大估值差异，避免中庸配置）")
        
        # 生成投资计划
        plan = self.generate_investment_plan(selected_etfs, weights, macro_info)
        
        print("\n【投资计划】")
        print("-" * 100)
        print(f"{'ETF名称':<15} {'估值分位':<10} {'风险等级':<12} {'权重':<10} {'投资金额':<15} {'预估份额':<12}")
        print("-" * 100)
        
        for item in plan:
            print(f"{item['etf_name']:<15} {item['valuation_percentile']:<10} "
                  f"{item['risk_level']:<12} {item['weight']:<10} "
                  f"{item['invest_amount']:<15} {item['estimated_shares']:<12}")
        
        print("="*80)
        
        # 资金效率分析
        total_invested = sum([float(p['invest_amount'].replace('¥', '').replace(',', '')) 
                             for p in plan])
        efficiency = total_invested / self.total_capital * 100
        
        print(f"\n【资金效率分析】")
        print(f"实际投资金额: ¥{total_invested:,.0f}")
        print(f"资金使用率: {efficiency:.1f}%")
        print(f"建议货币基金配置: ¥{macro_info['idle_capital']:,.0f}")
        
        return {
            'macro_info': macro_info,
            'selected_etfs': selected_etfs,
            'weights': weights,
            'investment_plan': plan,
            'timestamp': datetime.now()
        }

def compare_strategies():
    """对比线性和非线性策略"""
    
    print("\n" + "="*80)
    print("策略对比分析")
    print("="*80)
    
    # 测试不同的估值分位场景
    test_scenarios = [10, 30, 50, 70, 90]  # 不同的市场估值分位
    
    results = []
    for percentile in test_scenarios:
        # 线性策略
        linear_position = 1 - percentile/100
        
        # 非线性策略（使用不同的函数）
        strategy = NonlinearTwoStepInvestmentStrategy(nonlinear_type='sigmoid')
        sigmoid_position = strategy.nonlinear_position_sizing(percentile)
        
        strategy.nonlinear_type = 'power'
        power_position = strategy.nonlinear_position_sizing(percentile)
        
        strategy.nonlinear_type = 'custom'
        custom_position = strategy.nonlinear_position_sizing(percentile)
        
        results.append({
            '估值分位': f"{percentile}%",
            '线性仓位': f"{linear_position*100:.1f}%",
            'Sigmoid仓位': f"{sigmoid_position*100:.1f}%",
            '幂函数仓位': f"{power_position*100:.1f}%",
            '自定义仓位': f"{custom_position*100:.1f}%"
        })
    
    df = pd.DataFrame(results)
    print("\n不同估值水平下的仓位对比：")
    print(df.to_string(index=False))
    
    # 资金效率分析
    print("\n【资金效率分析】")
    print("假设市场70%时间处于30%-70%估值区间：")
    print("- 线性策略：平均仓位约50%，长期半仓")
    print("- 非线性策略：通过曲线调整，可以在合理区间保持更高仓位")
    print("  例如在估值40%时：")
    print("  线性仓位=60%，非线性(sigmoid)仓位≈70%，多出10%资金效率")

def main(user_info=None):
    """
    主函数
    
    :param user_info: 用户信息字典，包含age, annual_income, total_capital, monthly_expense等
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='非线性两步法ETF投资策略')
    parser.add_argument('--age', type=int, help='用户年龄')
    parser.add_argument('--annual_income', type=float, help='年收入')
    parser.add_argument('--total_capital', type=float, help='总资金')
    parser.add_argument('--monthly_expense', type=float, help='月开支')
    parser.add_argument('--risk_level', type=str, help='风险偏好')
    parser.add_argument('--investment_experience', type=str, help='投资经验')
    parser.add_argument('--career_stage', type=str, help='职业生涯阶段')
    
    args = parser.parse_args()
    
    # 如果命令行提供了参数，则使用命令行参数覆盖user_info
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
    
    # 设置默认用户信息
    if user_info is None:
        user_info = {
            'age': 40,
            'annual_income': 550000,
            'total_capital': 7000000,
            'monthly_expense': 20000,
            'risk_level': '进取',
            'investment_experience': '丰富'
        }
    
    # 加载配置文件
    with open("d:/agent skills/asset_allocation/config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    appropriateness_matrix = config.get('appropriateness_matrix', {})
    
    # 根据年龄判断职业生涯阶段
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
    
    # 将计算结果添加到用户信息中
    user_info['career_stage'] = career_stage
    user_info['aggressive_ratio'] = aggressive_ratio
    user_info['aggressive_capital'] = aggressive_capital
    
    # 创建策略实例（使用进取类投资资金）
    strategy = NonlinearTwoStepInvestmentStrategy(
        total_capital=aggressive_capital,  # 使用进取类投资资金
        lookback_years=5,
        rebalance_freq='Q',
        nonlinear_type='sigmoid',  # 可以选择 'sigmoid', 'power', 'custom'
        aggressiveness=1.2,  # 略激进
        lambda_decay=0.95,  # 衰减因子
        winsorize_pct=0.05  # 缩尾比例5%
    )
    
    # 加载实际的ETF数据
    etf_codes = ["510050", "510880", "516950"]  # 我们选出的3个高性价比ETF
    strategy.load_etf_data(etf_codes)
    
    # 运行策略
    print("\n运行非线性投资策略...")
    result = strategy.run_strategy()
    
    # 对比线性和非线性
    compare_strategies()
    
    # 保存结果
    df_plan = pd.DataFrame(result['investment_plan'])
    df_plan.to_csv('nonlinear_investment_plan.csv', index=False, encoding='utf-8-sig')
    print(f"\n投资计划已保存到 nonlinear_investment_plan.csv")
    
    # 发送到钉钉机器人
    try:
        from dingding import DingTalkBot, send_strategy_report_to_dingding
        
        # 配置钉钉机器人
        MY_ACCESS_TOKEN = "93d77b7421d98344c580175f59ee74a88fde3910a8050c8c548be3bfdca4152d"
        MY_SECRET = "SEC05951317384421f5f6d3919dec390acd7d0771b85a9c7318dfce1329adf4d38e"
        
        # 创建机器人实例
        bot = DingTalkBot(MY_ACCESS_TOKEN, MY_SECRET)
        
        # 发送策略报告到钉钉（传递用户信息）
        print("\n正在发送策略报告到钉钉机器人...")
        dingding_result = send_strategy_report_to_dingding(result, bot, user_info)
        
        if dingding_result['success']:
            print("✓ 策略报告已成功发送到钉钉机器人")
        else:
            print(f"✗ 发送到钉钉失败: {dingding_result['message']}")
            
    except ImportError:
        print("\n⚠️ 未找到dingding模块，跳过发送到钉钉")
    except Exception as e:
        print(f"\n⚠️ 发送到钉钉时出错: {str(e)}")
    
    return result

if __name__ == "__main__":
    # 直接调用main()函数，命令行参数会被argparse解析
    result = main()
