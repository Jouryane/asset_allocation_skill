import pandas as pd
import yaml
from datetime import datetime, timedelta
import os

DATA_PATH = r"D:\A_data\stock_data"

def load_config():
    """加载配置文件"""
    with open(r"d:/agent skills/asset_allocation/config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_sw_lv2_monthly():
    """加载申万二级行业指数历史估值数据（使用日度数据提取月度数据）"""
    daily_path = os.path.join(DATA_PATH, "sw_lv2_index_valuation_daily_10years.csv")
    df = pd.read_csv(daily_path)
    
    # 过滤掉未来日期的数据（只保留今天及之前的数据）
    today = datetime.now().strftime('%Y-%m-%d')
    df = df[df['发布日期'] <= today]
    
    # 转换为月度数据：取每月最后一条记录
    df['发布日期'] = pd.to_datetime(df['发布日期'])
    df['年月'] = df['发布日期'].dt.to_period('M')
    monthly_df = df.groupby(['指数代码', '年月']).last().reset_index()
    monthly_df = monthly_df.drop(columns=['年月'])
    
    return monthly_df

def load_sw_lv2_current():
    """加载申万二级行业指数当前估值数据（从历史数据中提取最新一条）"""
    daily_path = os.path.join(DATA_PATH, "sw_lv2_index_valuation_daily_10years.csv")
    df = pd.read_csv(daily_path)
    
    # 过滤掉未来日期的数据
    today = datetime.now().strftime('%Y-%m-%d')
    df = df[df['发布日期'] <= today]
    
    # 转换日期格式
    df['发布日期'] = pd.to_datetime(df['发布日期'])
    
    # 按指数代码分组，取每个指数的最新一条记录
    current_df = df.sort_values('发布日期', ascending=False).groupby('指数代码').head(1)
    
    return current_df

def get_index_current_pe(index_code, current_df):
    """
    获取申万二级行业指数的当前PE值
    :param index_code: 申万二级行业指数代码（如801880）
    :param current_df: 当前估值数据DataFrame
    :return: 当前PE值
    """
    # 处理代码类型
    if isinstance(index_code, str):
        try:
            index_code_int = int(index_code)
        except ValueError:
            index_code_int = None
    else:
        index_code_int = int(index_code)
    
    # 尝试匹配
    if index_code_int is not None:
        mask = (current_df['指数代码'] == index_code_int) | (current_df['指数代码'].astype(str) == str(index_code))
    else:
        mask = current_df['指数代码'].astype(str) == str(index_code)
    
    index_data = current_df[mask]
    
    if index_data.empty:
        return None
    
    pe_value = index_data.iloc[0]['市盈率']
    
    if pd.notna(pe_value) and pe_value > 0:
        return pe_value
    
    return None

def get_index_monthly_pe_history(index_code, monthly_df):
    """
    获取申万二级行业指数的月度PE和价格历史数据
    :param index_code: 申万二级行业指数代码（如801880）
    :param monthly_df: 月度估值数据DataFrame
    :return: 该指数的月度PE和价格历史数据列表
    """
    # 处理代码类型：可能是字符串或整数
    if isinstance(index_code, str):
        try:
            index_code_int = int(index_code)
        except ValueError:
            index_code_int = None
    else:
        index_code_int = int(index_code)
    
    # 尝试匹配整数和字符串两种格式
    if index_code_int is not None:
        mask = (monthly_df['指数代码'] == index_code_int) | (monthly_df['指数代码'].astype(str) == str(index_code))
    else:
        mask = monthly_df['指数代码'].astype(str) == str(index_code)
    
    index_data = monthly_df[mask]
    
    if index_data.empty:
        return []
    
    # 获取最近120个月的数据（10年）
    index_data = index_data.sort_values(by='发布日期', ascending=False).head(120)
    
    history = []
    for _, row in index_data.iterrows():
        pe_value = row['市盈率']
        price_value = row['收盘指数']
        if pd.notna(pe_value) and pe_value > 0 and pd.notna(price_value) and price_value > 0:
            history.append({
                'date': row['发布日期'],
                'pe': pe_value,
                'price': price_value
            })
    
    return history

def calculate_pe_percentile(latest_pe, pe_history):
    """
    计算PE在历史数据中的百分位
    :param latest_pe: 最新PE值
    :param pe_history: 历史PE数据列表（月度数据）
    :return: PE百分位（0~1）
    """
    if not pe_history or latest_pe is None:
        return None
    
    pe_values = [item['pe'] for item in pe_history if item['pe'] > 0]
    
    if not pe_values:
        return None
    
    # 计算当前PE在历史PE中的百分位
    percentile = sum(1 for pe in pe_values if pe < latest_pe) / len(pe_values)
    
    return percentile

def calculate_price_percentile(current_price, price_history):
    """
    计算价格在历史数据中的百分位
    :param current_price: 当前价格值
    :param price_history: 历史价格数据列表（月度数据）
    :return: 价格百分位（0~1）
    """
    if not price_history or current_price is None:
        return None
    
    price_values = [item['price'] for item in price_history if item['price'] > 0]
    
    if not price_values:
        return None
    
    # 计算当前价格在历史价格中的百分位
    percentile = sum(1 for price in price_values if price < current_price) / len(price_values)
    
    return percentile

def check_valuation_declining(pe_history):
    """
    检查估值是否连续下跌
    :param pe_history: 历史PE数据列表（按时间倒序）
    :return: 连续下跌的月数
    """
    if len(pe_history) < 2:
        return 0
    
    declining_months = 0
    for i in range(len(pe_history) - 1):
        if pe_history[i]['pe'] < pe_history[i + 1]['pe']:
            declining_months += 1
        else:
            break
    
    return declining_months

def check_valuation_rising(pe_history):
    """
    检查近1个月估值是否环比上涨
    :param pe_history: 历史PE数据列表（按时间倒序）
    :return: True如果近1个月估值环比上涨
    """
    if len(pe_history) < 2:
        return False
    
    # 最新PE > 上月PE
    return pe_history[0]['pe'] > pe_history[1]['pe']

def calculate_valuation_safety_score(pe_percentile, price_percentile, pe_history):
    """
    计算估值安全分（加入价格贵贱过滤）
    :param pe_percentile: 当前PE在历史120个月中的分位数（0~1）
    :param price_percentile: 当前价格在历史120个月中的分位数（0~1）
    :param pe_history: 历史PE数据列表（按时间倒序）
    :return: 估值安全分（0~1），得分越高代表估值越安全且有性价比
    """
    if pe_percentile is None or price_percentile is None:
        return 0.0
    
    q = pe_percentile * 100
    pct_price = price_percentile * 100
    
    # 检查估值连跌情况
    declining_months = check_valuation_declining(pe_history)
    
    # 排除极致低估（防回撤）或估值连跌3个月
    if q < 10 or declining_months >= 3:
        return 0.0
    # 排除价格处于历史高位（价格贵贱过滤）
    elif pct_price > 70:
        return 0.0
    # 双低核心区：10% ≤ Q ≤ 30% 且 Pct_Price ≤ 50%（得分最高）
    elif 10 <= q <= 30 and pct_price <= 50:
        return (30 - q) / 20 * (70 - pct_price) / 70
    # 估值低但价格适中：10% ≤ Q ≤ 30% 且 50% < Pct_Price ≤ 70%（降权）
    elif 10 <= q <= 30 and 50 < pct_price <= 70:
        return (30 - q) / 20 * 0.5
    # 弱关注区间：30% < Q ≤ 50% 且 Pct_Price ≤ 50%
    elif 30 < q <= 50 and pct_price <= 50:
        return 0.1 * (50 - q) / 20
    # 其他情况
    else:
        return 0.0

def calculate_price_resilience_coefficient(index_code, monthly_df, all_indices_avg_change):
    """
    计算价格抗跌系数
    :param index_code: 申万二级行业指数代码
    :param monthly_df: 月度估值数据DataFrame
    :param all_indices_avg_change: 所有行业指数的平均涨跌幅
    :return: 价格抗跌系数（0~1）
    """
    # 处理代码类型
    if isinstance(index_code, str):
        try:
            index_code_int = int(index_code)
        except ValueError:
            index_code_int = None
    else:
        index_code_int = int(index_code)
    
    # 尝试匹配
    if index_code_int is not None:
        mask = (monthly_df['指数代码'] == index_code_int) | (monthly_df['指数代码'].astype(str) == str(index_code))
    else:
        mask = monthly_df['指数代码'].astype(str) == str(index_code)
    
    index_data = monthly_df[mask]
    
    if index_data.empty:
        return 0.0
    
    # 获取最近1个月的涨跌幅
    recent_data = index_data.sort_values(by='发布日期', ascending=False).head(1)
    
    if len(recent_data) == 0:
        return 0.0
    
    etf_change = recent_data.iloc[0]['涨跌幅']
    
    if pd.isna(etf_change):
        return 0.0
    
    # 相对抗跌：ETF涨跌幅 ≥ 所有行业平均涨跌幅
    if etf_change >= all_indices_avg_change:
        return 1.0
    # 轻度下跌：ETF涨跌幅 < 所有行业平均 但 ≥ -10%
    elif etf_change >= -10:
        return max(0, (etf_change + 10) / 10)
    # 大幅下跌：ETF涨跌幅 < -10%
    else:
        return 0.0

def calculate_trading_activity_coefficient(index_code, monthly_df):
    """
    计算交易活跃度系数
    :param index_code: 申万二级行业指数代码
    :param monthly_df: 月度估值数据DataFrame
    :return: 交易活跃度系数（0~1）
    """
    # 处理代码类型
    if isinstance(index_code, str):
        try:
            index_code_int = int(index_code)
        except ValueError:
            index_code_int = None
    else:
        index_code_int = int(index_code)
    
    # 尝试匹配
    if index_code_int is not None:
        mask = (monthly_df['指数代码'] == index_code_int) | (monthly_df['指数代码'].astype(str) == str(index_code))
    else:
        mask = monthly_df['指数代码'].astype(str) == str(index_code)
    
    index_data = monthly_df[mask]
    
    if index_data.empty:
        return 0.0
    
    # 获取最近20日的换手率数据
    recent_20 = index_data.sort_values(by='发布日期', ascending=False).head(20)
    
    if len(recent_20) < 20:
        return 0.0
    
    # 获取近120日的换手率数据
    recent_120 = index_data.sort_values(by='发布日期', ascending=False).head(120)
    
    if len(recent_120) < 120:
        return 0.0
    
    # 计算近20日和近120日的平均换手率
    avg_turnover_20 = recent_20['换手率'].mean()
    avg_turnover_120 = recent_120['换手率'].mean()
    
    if pd.isna(avg_turnover_20) or pd.isna(avg_turnover_120) or avg_turnover_120 == 0:
        return 0.0
    
    # 活跃度不下降：近20日ETF日均换手率 ≥ 自身近120日日均换手率
    if avg_turnover_20 >= avg_turnover_120:
        return 1.0
    # 轻度下降：0.5×近120日均值 ≤ 近20日均值 < 近120日均值
    elif avg_turnover_20 >= 0.5 * avg_turnover_120:
        return 0.7
    # 显著下降：0.2×近120日均值 ≤ 近20日均值 < 0.5×近120日均值
    elif avg_turnover_20 >= 0.2 * avg_turnover_120:
        return 0.3
    # 活跃度几乎枯竭：近20日均值 < 0.2×近120日均值
    else:
        return 0.0

def calculate_comprehensive_score(safety_score, trading_activity, price_resilience):
    """
    计算综合性价比得分
    :param safety_score: 估值安全分（0~1）
    :param trading_activity: 交易活跃度系数（0~1）
    :param price_resilience: 价格抗跌系数（0~1）
    :return: 综合性价比得分（0~100）
    """
    return safety_score * trading_activity * price_resilience * 100

def get_sw_lv2_indices():
    """
    获取申万二级行业指数列表
    :return: 申万二级行业指数字典
    """
    daily_path = os.path.join(DATA_PATH, "sw_lv2_index_valuation_daily_10years.csv")
    df = pd.read_csv(daily_path)
    
    # 获取所有唯一的指数代码和名称
    indices = df[['指数代码', '指数名称']].drop_duplicates()
    
    # 转换为字典格式
    indices_dict = {}
    for _, row in indices.iterrows():
        code = row['指数代码']
        name = row['指数名称']
        indices_dict[code] = {"name": name}
    
    return indices_dict

def select_best_sw_lv2_indices_by_valuation():
    """
    从申万二级行业指数中选出综合性价比最高的指数
    基于申万二级行业指数的估值数据
    """
    # 加载配置
    config = load_config()
    
    # 加载数据
    current_df = load_sw_lv2_current()
    monthly_df = load_sw_lv2_monthly()
    
    # 计算所有行业指数的平均涨跌幅（作为基准）
    recent_all = monthly_df.sort_values(by='发布日期', ascending=False).groupby('指数代码').head(1)
    all_indices_avg_change = recent_all['涨跌幅'].mean()
    
    # 获取申万二级行业指数列表
    sw_lv2_indices = get_sw_lv2_indices()
    
    print(f"\n开始处理 {len(sw_lv2_indices)} 个申万二级行业...")
    print(f"所有行业指数平均涨跌幅: {all_indices_avg_change:.2f}%")
    
    # 计算每个行业的综合性价比得分
    index_valuations = []
    processed_count = 0
    for code, info in sw_lv2_indices.items():
        industry_name = info['name']
        processed_count += 1
        
        # 获取当前PE
        current_pe = get_index_current_pe(code, current_df)
        
        if current_pe is None:
            print(f"[{processed_count}/{len(sw_lv2_indices)}] {industry_name} ({code}): 无法获取当前PE")
            continue
        
        # 获取月度PE和价格历史
        history = get_index_monthly_pe_history(code, monthly_df)
        
        if not history:
            print(f"[{processed_count}/{len(sw_lv2_indices)}] {industry_name} ({code}): 无法获取历史数据")
            continue
        
        # 计算PE百分位
        pe_percentile = calculate_pe_percentile(current_pe, history)
        
        if pe_percentile is None:
            print(f"[{processed_count}/{len(sw_lv2_indices)}] {industry_name} ({code}): 无法计算PE百分位")
            continue
        
        # 计算价格百分位
        price_percentile = calculate_price_percentile(history[0]['price'], history)
        
        if price_percentile is None:
            print(f"[{processed_count}/{len(sw_lv2_indices)}] {industry_name} ({code}): 无法计算价格百分位")
            continue
        
        # 计算估值安全分
        safety_score = calculate_valuation_safety_score(pe_percentile, price_percentile, history)
        
        # 计算价格抗跌系数
        price_resilience = calculate_price_resilience_coefficient(code, monthly_df, all_indices_avg_change)
        
        # 计算交易活跃度系数
        trading_activity = calculate_trading_activity_coefficient(code, monthly_df)
        
        # 计算综合性价比得分
        comprehensive_score = calculate_comprehensive_score(safety_score, trading_activity, price_resilience)
        
        # 只保留得分大于0的行业
        if comprehensive_score > 0:
            print(f"[{processed_count}/{len(sw_lv2_indices)}] {industry_name} ({code}): 综合得分={comprehensive_score:.2f}, PE百分位={pe_percentile*100:.1f}%, 价格百分位={price_percentile*100:.1f}%, 估值安全分={safety_score:.3f}, 交易活跃度={trading_activity:.3f}, 价格抗跌={price_resilience:.3f}")
            
            index_valuations.append({
                "code": code,
                "name": industry_name,
                "current_pe": current_pe,
                "current_pe_percentile": pe_percentile,
                "current_price_percentile": price_percentile,
                "safety_score": safety_score,
                "trading_activity": trading_activity,
                "price_resilience": price_resilience,
                "comprehensive_score": comprehensive_score
            })
        else:
            print(f"[{processed_count}/{len(sw_lv2_indices)}] {industry_name} ({code}): 综合得分=0 (被筛选)")
    
    # 按综合性价比得分排序（得分越高，性价比越高）
    if index_valuations:
        index_valuations.sort(key=lambda x: x["comprehensive_score"], reverse=True)
        
        # 实现行业池筛选逻辑
        if len(index_valuations) > 8:
            index_valuations = index_valuations[:8]
        
        return index_valuations
    
    return []

if __name__ == "__main__":
    print("正在加载数据...")
    print("数据路径:", DATA_PATH)
    print("-" * 140)
    
    # 测试数据加载
    print("\n测试数据加载:")
    current_df = load_sw_lv2_current()
    monthly_df = load_sw_lv2_monthly()
    
    print(f"申万二级行业当前估值: {len(current_df)} 个行业")
    print(f"申万二级行业月度估值: {len(monthly_df)} 条记录")
    
    if len(monthly_df) > 0:
        print(f"月度数据时间范围: {monthly_df['发布日期'].min()} 到 {monthly_df['发布日期'].max()}")
    
    print("-" * 140)
    
    # 执行筛选
    best_indices = select_best_sw_lv2_indices_by_valuation()
    
    if best_indices:
        print("\n申万二级行业指数综合性价比排序（得分从高到低）：")
        print("-" * 140)
        print(f"{'排名':<6} {'指数代码':<10} {'指数名称':<12} {'当前PE':<10} {'PE百分位':<12} {'价格百分位':<12} {'估值安全分':<12} {'交易活跃度':<12} {'价格抗跌':<12} {'综合得分':<10}")
        print("-" * 140)
        
        for i, index in enumerate(best_indices, 1):
            current_pe_str = f"{index['current_pe']:.2f}" if index['current_pe'] is not None else "N/A"
            percentile_str = f"{index['current_pe_percentile']*100:.1f}%" if index['current_pe_percentile'] is not None else "N/A"
            price_percentile_str = f"{index['current_price_percentile']*100:.1f}%" if index['current_price_percentile'] is not None else "N/A"
            safety_str = f"{index['safety_score']:.3f}" if index['safety_score'] is not None else "N/A"
            activity_str = f"{index['trading_activity']:.3f}" if index['trading_activity'] is not None else "N/A"
            resilience_str = f"{index['price_resilience']:.3f}" if index['price_resilience'] is not None else "N/A"
            score_str = f"{index['comprehensive_score']:.2f}" if index['comprehensive_score'] is not None else "N/A"
            print(f"{i:<6} {index['code']:<10} {index['name']:<12} {current_pe_str:<10} {percentile_str:<12} {price_percentile_str:<12} {safety_str:<12} {activity_str:<12} {resilience_str:<12} {score_str:<10}")
        
        print("-" * 140)
        print(f"\n筛选结果：{len(best_indices)} 个申万二级行业指数通过四重筛选")
        print("\n说明：")
        print("- 当前PE：申万二级行业指数的TTM滚动市盈率")
        print("- PE百分位：当前PE在历史120个月中的位置")
        print("- 价格百分位：当前价格在历史120个月中的位置")
        print("- 估值安全分：基于PE百分位和价格百分位计算的安全得分（0~1）")
        print("- 交易活跃度：基于换手率计算的活跃度系数（0~1）")
        print("- 价格抗跌：基于涨跌幅计算的抗跌系数（0~1）")
        print("- 综合得分：估值安全分 × 交易活跃度 × 价格抗跌 × 100（0~100）")
        print("- 筛选规则：")
        print("  - 排除PE百分位 < 10% 的极致低估（防回撤）")
        print("  - 排除估值连跌3个月的行业（估值未企稳）")
        print("  - 排除价格百分位 > 70% 的行业（价格处于历史高位，价格贵贱过滤）")
        print("  - 排除PE百分位 > 50% 的高估行业")
        print("  - 双低核心区：10% ≤ PE百分位 ≤ 30% 且 价格百分位 ≤ 50%（得分最高）")
        print("  - 估值低但价格适中：10% ≤ PE百分位 ≤ 30% 且 50% < 价格百分位 ≤ 70%（降权）")
        print("  - 弱关注区间：30% < PE百分位 ≤ 50% 且 价格百分位 ≤ 50%")
        print("  - 价格抗跌：相对所有行业平均涨跌幅的抗跌能力")
        print("  - 交易活跃度：基于换手率的活跃程度")
        print("  - 若筛选后 > 8个行业，取前8名（控制分散度）")
        print("  - 若筛选后 < 5个行业，全部保留（最低分散要求）")
        print("- 排序标准：按综合得分从高到低排序，得分越高性价比越高")
        print("- 数据来源：申万二级行业指数估值数据（sw_lv2_index_valuation_daily_10years.csv）")
    else:
        print("未获取到有效的申万二级行业指数估值数据")
