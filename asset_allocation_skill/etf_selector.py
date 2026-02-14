# etf_selector.py
import akshare as ak
import yaml
import pandas as pd
from datetime import datetime, timedelta

def load_config():
    """加载配置文件"""
    with open("d:/agent skills/asset_allocation/config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# 第一步：构建A股主流ETF与对应指数的映射表
ETF_TO_INDEX = {
    # 宽基ETF
    "510300": "000300",  # 沪深300ETF → 沪深300指数
    "510050": "000016",  # 上证50ETF → 上证50指数
    "159338": "000510",  # 中证A500ETF → 中证A500
    "159201": "980092",  # 自由现金流ETF → 自由现金流指数
    "159629": "000852",  # 1000etf → 中证1000
    # 行业ETF
    "512880": "399975",  # 证券ETF → 证券公司指数
    "159807": "931380",  # 科技ETF → 科技50指数
    "159928": "000932",  # 消费ETF → 中证消费
    "512690": "399987",  # 酒ETF → 中证白酒
    "510880": "000015",  # 红利ETF → 红利指数
    # 主题ETF
    "515790": "931151",  # 光伏ETF → 光伏产业
    "159637": "399976",  # 新能源车ETF → CS新能源车
    "159599": "H30184",  # 芯片ETF → 芯片产业指数
    "159796": "931719",  # 电池ETF → 电池主题指数
    "512400": "000819"   # 有色金属ETF → 有色金属指数
}

def get_index_valuation(index_code: str) -> dict:
    """
    获取指数的PE/估值百分位（核心接口，替代直接查ETF）
    :param index_code: 指数代码（如000300）
    :return: 包含pe、pe_percentile的字典
    """
    try:
        # 调用AKShare指数估值接口（重点：用指数代码，不是ETF代码）
        df = ak.stock_zh_index_value_csindex(symbol=index_code)
        
        if df.empty:
            print(f"指数{index_code}无估值数据")
            return {"pe": None, "pe_percentile": None}
        
        # 获取最新一条数据（按日期排序取最后一条）
        df = df.sort_values("日期", ascending=False).head(1)
        
        # 提取PE数据（使用市盈率1）
        pe = float(df["市盈率1"].iloc[0]) if pd.notna(df["市盈率1"].iloc[0]) else None
        
        # 计算PE百分位（当前PE在历史PE中的位置）
        all_pe = df["市盈率1"].dropna()
        pe_percentile = (all_pe < pe).mean() if pe is not None else None
        
        result = {
            "pe": pe,
            "pe_percentile": pe_percentile
        }
        return result
    except Exception as e:
        print(f"获取指数{index_code}估值失败：{str(e)}")
        return {"pe": None, "pe_percentile": None}

def get_etf_valuation(etf_code: str) -> dict:
    """
    对外暴露的接口：输入ETF代码，返回对应指数的估值数据
    """
    # 1. 检查ETF是否在映射表中
    if etf_code not in ETF_TO_INDEX:
        print(f"ETF{etf_code}无匹配的指数代码，请补充映射表")
        return {"pe": None, "pe_percentile": None}
    
    # 2. 映射到指数代码，获取估值
    index_code = ETF_TO_INDEX[etf_code]
    return get_index_valuation(index_code)

def select_best_etfs_by_valuation():
    """
    从每个类别中选出PE值最低的ETF（估值最便宜）
    """
    # 1. 加载配置
    config = load_config()
    
    # 2. 定义类别
    categories = {
        "broad_based": "宽基ETF",
        "industry": "行业ETF",
        "theme": "主题ETF"
    }
    
    # 3. 从每个类别中选出PE值最低的ETF
    best_etfs = {}
    
    for category, category_name in categories.items():
        if category not in config:
            print(f"未找到 {category_name} 类别")
            continue
        
        etf_codes = config[category]
        if not etf_codes:
            print(f"{category_name} 类别为空")
            continue
        
        # 计算每个ETF的估值
        etf_valuations = []
        for code in etf_codes:
            valuation = get_etf_valuation(code)
            
            # 获取PE值
            pe = valuation.get("pe", None)
            
            etf_valuations.append({
                "code": code,
                "pe": pe,
                "pe_percentile": valuation.get("pe_percentile", None)
            })
        
        # 按PE值排序，选择最低的（PE值越低，估值越便宜）
        # 过滤掉PE为None的ETF
        valid_etfs = [etf for etf in etf_valuations if etf["pe"] is not None]
        
        if valid_etfs:
            valid_etfs.sort(key=lambda x: x["pe"])
            best_etf = valid_etfs[0]
            best_etfs[category] = best_etf
    
    return best_etfs

if __name__ == "__main__":
    # 执行筛选
    best_etfs = select_best_etfs_by_valuation()
    
    if best_etfs:
        print("各类别估值最低的ETF（PE值最低）：")
        print("-" * 80)
        print(f"{'类别':<10} {'代码':<8} {'PE':<8} {'PE百分位':<10}")
        print("-" * 80)
        
        categories = {
            "broad_based": "宽基ETF",
            "industry": "行业ETF",
            "theme": "主题ETF"
        }
        
        for category, best_etf in best_etfs.items():
            category_name = categories.get(category, category)
            pe_str = f"{best_etf['pe']:.2f}" if best_etf['pe'] is not None else "N/A"
            pe_percentile_str = f"{best_etf['pe_percentile']:.2%}" if best_etf['pe_percentile'] is not None else "N/A"
            print(f"{category_name:<10} {best_etf['code']:<8} {pe_str:<8} {pe_percentile_str:<10}")
        
        print("-" * 80)
        print("\n说明：")
        print("- PE值：市盈率，越低表示估值越便宜")
        print("- PE百分位：当前PE在历史PE中的位置（基于最近20天数据）")
        print("- 选择标准：PE值最低的ETF，即估值最便宜的ETF")
