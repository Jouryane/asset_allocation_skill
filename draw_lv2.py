import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import os
import yaml

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

DATA_PATH = r"D:\A_data\stock_data"

def load_config():
    """加载配置文件"""
    with open(r"d:/agent skills/asset_allocation/config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

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

def get_index_data(index_code, current_df, monthly_df):
    """
    获取申万二级行业指数的当前和历史数据
    :param index_code: 申万二级行业指数代码
    :param current_df: 当前估值数据DataFrame
    :param monthly_df: 月度估值数据DataFrame
    :return: 包含当前PE、当前价格和历史数据的字典
    """
    # 处理代码类型
    if isinstance(index_code, str):
        try:
            index_code_int = int(index_code)
        except ValueError:
            index_code_int = None
    else:
        index_code_int = int(index_code)
    
    # 获取当前数据
    if index_code_int is not None:
        mask = (current_df['指数代码'] == index_code_int) | (current_df['指数代码'].astype(str) == str(index_code))
    else:
        mask = current_df['指数代码'].astype(str) == str(index_code)
    
    current_data = current_df[mask]
    
    if current_data.empty:
        return None
    
    # 获取历史数据
    if index_code_int is not None:
        mask = (monthly_df['指数代码'] == index_code_int) | (monthly_df['指数代码'].astype(str) == str(index_code))
    else:
        mask = monthly_df['指数代码'].astype(str) == str(index_code)
    
    history_data = monthly_df[mask].sort_values(by='发布日期', ascending=False).head(120)
    history_data = history_data.sort_values(by='发布日期', ascending=True)
    
    # 获取当前数据
    current_pe = float(current_data.iloc[0]['市盈率'])
    
    # 从当前数据中获取发布日期作为最新日期
    latest_date_str = str(current_data.iloc[0]['发布日期']).split()[0]
    latest_date = pd.to_datetime(latest_date_str)
    
    # 将当前PE添加到历史数据的最后
    if len(history_data) > 0:
        # 检查最新历史日期是否与当前日期相同
        last_history_date = pd.to_datetime(history_data['发布日期'].iloc[-1])
        
        if last_history_date < latest_date:
            # 添加当前数据点
            new_row = history_data.iloc[-1].copy()
            new_row['发布日期'] = latest_date
            new_row['市盈率'] = float(current_pe)
            
            # 保持收盘指数不变（使用最后一个历史值）
            history_data = pd.concat([history_data, new_row.to_frame().T], ignore_index=True)
            
            # 确保数值列是数值类型
            history_data['市盈率'] = pd.to_numeric(history_data['市盈率'], errors='coerce')
            history_data['收盘指数'] = pd.to_numeric(history_data['收盘指数'], errors='coerce')
            history_data['换手率'] = pd.to_numeric(history_data['换手率'], errors='coerce')
    
    return {
        'current_pe': current_pe,
        'current_price': history_data['收盘指数'].iloc[-1] if len(history_data) > 0 else None,
        'history': history_data
    }

def draw_index_chart(index_info, output_dir='charts_lv2'):
    """
    为单个申万二级行业指数绘制综合图表
    :param index_info: 包含指数代码、名称、当前PE等信息的字典
    :param output_dir: 输出目录
    """
    # 加载数据
    config = load_config()
    current_df = load_sw_lv2_current()
    monthly_df = load_sw_lv2_monthly()
    
    # 获取指数数据
    index_data = get_index_data(index_info['code'], current_df, monthly_df)
    
    if index_data is None:
        print(f"无法获取 {index_info['name']} ({index_info['code']}) 的数据")
        return
    
    history = index_data['history']
    current_pe = index_data['current_pe']
    
    # 获取日期范围
    dates = history['发布日期']
    min_date = dates.min()
    max_date = dates.max()
    
    # 创建图表
    fig, axes = plt.subplots(3, 1, figsize=(14, 12))
    fig.suptitle(f"{index_info['name']} ({index_info['code']}) - 综合分析", fontsize=16, fontweight='bold')
    
    # 1. PE历史趋势图
    ax1 = axes[0]
    pe_values = history['市盈率']
    
    ax1.plot(dates, pe_values, linewidth=2, color='#2E86AB', label='历史PE')
    ax1.axhline(y=current_pe, color='#E63946', linestyle='--', linewidth=2, label=f'当前PE: {current_pe:.2f}')
    ax1.fill_between(dates, pe_values, current_pe, where=(pe_values <= current_pe), 
                    alpha=0.3, color='#90BE6D', label='低于当前PE')
    ax1.fill_between(dates, pe_values, current_pe, where=(pe_values > current_pe), 
                    alpha=0.3, color='#F94144', label='高于当前PE')
    
    ax1.set_ylabel('PE值', fontsize=12, fontweight='bold')
    ax1.set_title('PE历史趋势', fontsize=14, fontweight='bold')
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    
    # 格式化x轴 - 动态设置范围和刻度
    ax1.set_xlim(min_date, max_date)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    
    # 根据数据长度动态设置刻度间隔
    date_range_days = (max_date - min_date).days
    if date_range_days > 365 * 5:  # 超过5年，每年一个刻度
        ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=12))
    elif date_range_days > 365 * 2:  # 超过2年，每半年一个刻度
        ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    else:  # 2年以内，每季度一个刻度
        ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    
    # 2. 价格历史趋势图
    ax2 = axes[1]
    price_values = history['收盘指数']
    current_price = history['收盘指数'].iloc[-1]
    
    ax2.plot(dates, price_values, linewidth=2, color='#2E86AB', label='历史价格')
    ax2.axhline(y=current_price, color='#E63946', linestyle='--', linewidth=2, label=f'当前价格: {current_price:.2f}')
    ax2.fill_between(dates, price_values, current_price, where=(price_values <= current_price), 
                    alpha=0.3, color='#90BE6D', label='低于当前价格')
    ax2.fill_between(dates, price_values, current_price, where=(price_values > current_price), 
                    alpha=0.3, color='#F94144', label='高于当前价格')
    
    ax2.set_ylabel('指数点位', fontsize=12, fontweight='bold')
    ax2.set_title('价格历史趋势', fontsize=14, fontweight='bold')
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)
    
    # 格式化x轴 - 动态设置范围和刻度
    ax2.set_xlim(min_date, max_date)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    
    # 根据数据长度动态设置刻度间隔
    if date_range_days > 365 * 5:  # 超过5年，每年一个刻度
        ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=12))
    elif date_range_days > 365 * 2:  # 超过2年，每半年一个刻度
        ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    else:  # 2年以内，每季度一个刻度
        ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
    
    # 3. 换手率趋势图
    ax3 = axes[2]
    turnover_values = history['换手率']
    
    ax3.plot(dates, turnover_values, linewidth=2, color='#2E86AB', label='换手率')
    ax3.fill_between(dates, turnover_values, alpha=0.3, color='#A8DADC')
    
    # 计算并标注近20日和近120日均值
    recent_20 = turnover_values.tail(20)
    recent_120 = turnover_values.tail(120)
    avg_20 = recent_20.mean()
    avg_120 = recent_120.mean()
    
    ax3.axhline(y=avg_20, color='#F94144', linestyle='--', linewidth=2, label=f'近20日均值: {avg_20:.2f}')
    ax3.axhline(y=avg_120, color='#E63946', linestyle=':', linewidth=2, label=f'近120日均值: {avg_120:.2f}')
    
    ax3.set_ylabel('换手率 (%)', fontsize=12, fontweight='bold')
    ax3.set_xlabel('日期', fontsize=12, fontweight='bold')
    ax3.set_title('换手率变化趋势', fontsize=14, fontweight='bold')
    ax3.legend(loc='best')
    ax3.grid(True, alpha=0.3)
    
    # 格式化x轴 - 动态设置范围和刻度
    ax3.set_xlim(min_date, max_date)
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    
    # 根据数据长度动态设置刻度间隔
    if date_range_days > 365 * 5:  # 超过5年，每年一个刻度
        ax3.xaxis.set_major_locator(mdates.MonthLocator(interval=12))
    elif date_range_days > 365 * 2:  # 超过2年，每半年一个刻度
        ax3.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    else:  # 2年以内，每季度一个刻度
        ax3.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    filename = os.path.join(output_dir, f"{index_info['code']}_{index_info['name']}_综合分析.png")
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"已生成图表: {filename}")
    
    return filename

def draw_all_indices(selected_indices, output_dir='charts_lv2'):
    """
    为所有筛选出的申万二级行业指数绘制图表
    :param selected_indices: 筛选出的指数列表
    :param output_dir: 输出目录
    """
    print("\n开始生成 {} 个申万二级行业指数的可视化图表...".format(len(selected_indices)))
    print("=" * 140)
    
    generated_files = []
    for index_info in selected_indices:
        filename = draw_index_chart(index_info, output_dir)
        if filename:
            generated_files.append(filename)
    
    print("=" * 140)
    print(f"\n成功生成 {len(generated_files)} 个图表")
    print(f"图表保存位置: {output_dir}")
    
    return generated_files

if __name__ == "__main__":
    # 从sw_lv2_selector导入筛选函数
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from sw_lv2_selector import select_best_sw_lv2_indices_by_valuation
    
    # 获取sw_lv2_selector的筛选结果
    print("正在从sw_lv2_selector获取筛选结果...")
    selected_indices = select_best_sw_lv2_indices_by_valuation()
    
    if not selected_indices:
        print("未获取到有效的申万二级行业指数筛选结果")
        sys.exit(1)
    
    # 生成所有图表
    draw_all_indices(selected_indices)
