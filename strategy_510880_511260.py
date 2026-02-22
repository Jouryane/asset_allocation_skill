import akshare as ak
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import time, hmac, hashlib, base64, urllib.parse, requests, json, os
import yaml

# ==========================================
# 0. 配置加载
# ==========================================
def load_config():
    """从config.yaml加载配置"""
    config_path = "d:/agent skills/asset_allocation/config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config

def get_dingtalk_config(config):
    """从config.yaml获取钉钉配置"""
    return {
        'access_token': config.get('MY_ACCESS_TOKEN'),
        'secret': config.get('MY_SECRET')
    }

def get_gitee_config(config):
    """从config.yaml获取Gitee配置"""
    return {
        'access_token': config.get('ACCESS_TOKEN'),
        'owner': config.get('OWNER'),
        'repo': config.get('REPO')
    }

# ==========================================
# 1. 策略核心逻辑 (多维监控：趋势偏离 + 510880 真实回撤)
# ==========================================
def get_strategy_data(start_date="20200101"):
    """获取策略数据"""
    df_dividend = ak.fund_etf_hist_em(symbol="510880", period="daily", start_date=start_date, adjust="hfq")
    df_bond = ak.fund_etf_hist_em(symbol="511260", period="daily", start_date=start_date, adjust="hfq")

    df = pd.merge(df_dividend[['日期', '收盘']], df_bond[['日期', '收盘']], on='日期')
    df.columns = ['date', 'dividend', 'bond']
    df['date'] = pd.to_datetime(df['date'])
    df['product'] = df['dividend'] * df['bond']
    return df

def calculate_indicators(df):
    """计算策略指标"""
    # A. 拟合长期趋势线
    X = np.arange(len(df)).reshape(-1, 1)
    y = df['product'].values.reshape(-1, 1)
    model = LinearRegression().fit(X, y)
    df['trend_line'] = model.predict(X)

    # B. 计算物理偏离百分比 (性价比指标)
    df['diff_pct'] = ((df['product'] - df['trend_line']) / df['trend_line']) * 100

    # C. 计算 510880 滚动回撤 (经验硬指标：以250日最高价为基准)
    window = 250 
    rolling_max = df['dividend'].rolling(window=window, min_periods=1).max()
    df['div_drawdown'] = ((df['dividend'] - rolling_max) / rolling_max) * 100
    
    return df

def generate_chart(df, image_path="daily_trend.png"):
    """生成趋势分析图"""
    plt.rcParams['font.sans-serif'] = ['SimHei']; plt.rcParams['axes.unicode_minus'] = False
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 15), sharex=True)

    ax1.plot(df['date'], df['product'], label='价格乘积', color='#1f77b4')
    ax1.plot(df['date'], df['trend_line'], linestyle='--', color='red', label='长期趋势中轴')
    ax1.set_title("红利/十债价格乘积长期复利趋势线")
    ax1.legend()

    ax2.plot(df['date'], df['diff_pct'], color='purple', label='物理偏离百分比')
    ax2.axhline(0, color='black', linewidth=1)
    ax2.set_title("相对于趋势线的物理偏离度 (%)")
    ax2.legend()

    ax3.plot(df['date'], df['div_drawdown'], color='blue', label='510880 滚动回撤')
    ax3.axhline(-7, color='green', linestyle=':', linewidth=2, label='7% 经验买入警戒线')
    ax3.fill_between(df['date'], -7, df['div_drawdown'], where=(df['div_drawdown'] <= -7), color='green', alpha=0.2)
    ax3.set_title("510880 单资产回撤监测 (买入胜率锚点)")
    ax3.legend()

    plt.tight_layout()
    plt.savefig(image_path)
    plt.close()
    return image_path

# ==========================================
# 2. Gitee 图片上传
# ==========================================
def upload_to_gitee(file_path, gitee_config):
    """
    利用 Gitee (码云) 接口上传图片
    国内直连，速度极快，100% 解决 400 错误和连接中止问题
    """
    ACCESS_TOKEN = gitee_config['access_token']
    OWNER = gitee_config['owner']
    REPO = gitee_config['repo']

    remote_file_name = f"chart_{int(time.time())}.png"
    api_url = f"https://gitee.com/api/v5/repos/{OWNER}/{REPO}/contents/{remote_file_name}"
    
    try:
        with open(file_path, "rb") as f:
            content = base64.b64encode(f.read()).decode('utf-8')
        
        payload = {
            "access_token": ACCESS_TOKEN,
            "content": content,
            "message": "理财经理每日报告更新"
        }
        
        res = requests.post(api_url, json=payload, timeout=30)
        if res.status_code == 201:
            img_url = res.json()['content']['download_url']
            print(f"Gitee 部署成功: {img_url}")
            return img_url
        else:
            print(f"Gitee 报错 {res.status_code}: {res.text}")
    except Exception as e:
        print(f"Gitee 上传异常: {e}")
    return None

# ==========================================
# 3. 钉钉推送
# ==========================================
class DingTalkManager:
    def __init__(self, access_token, secret):
        self.access_token = access_token
        self.secret = secret
        self.webhook_url = f"https://oapi.dingtalk.com/robot/send?access_token={access_token}"

    def _get_sign_url(self):
        timestamp = str(round(time.time() * 1000))
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, self.secret)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote(base64.b64encode(hmac_code))
        return f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"

    def send_professional_report(self, diff_pct, div_dd, diff_change, date_str, img_url):
        sign_url = self._get_sign_url()
        
        # 经验判断逻辑
        trend_icon = "逐级走强 📈" if diff_change > 0 else "震荡回落 📉"
        if div_dd <= -7:
            status, color = "【🟢 经验触发：510880回撤已达标】", "#FF4500"
        elif diff_pct < -6:
            status, color = "【极具性价比 / 长期价值点】", "#FF0000"
        else:
            status, color = "【常态波动区间】", "#000000"

        img_display = f"![趋势图]({img_url})" if img_url else "*(图片上传失败，请查看本地文件)*"
        
        content = f"### <font color={color}>{status}</font>\n" \
                  f"---\n" \
                  f"**1. 物理偏离度 (性价比)**：**{diff_pct:.2f}%**\n" \
                  f"* **变动趋势**：{trend_icon} (较昨日 {diff_change:+.2f}%)\n\n" \
                  f"**2. 510880 真实回撤 (硬指标)**：<font color={color} size=4>**{div_dd:.2f}%**</font>\n" \
                  f"* **经验参考**：回撤达 -7% 时买入胜率显著提升。\n\n" \
                  f"**更新日期**：{date_str}\n" \
                  f"---\n" \
                  f"#### 📊 高清多维诊断详情\n" \
                  f"{img_display}\n\n" \
                  f"[🔗 点击此处查看全屏详情图]({img_url if img_url else 'about:blank'})\n" \
                  f"---\n" \
                  f"来自：私有理财经理"

        payload = {"msgtype": "markdown", "markdown": {"title": "策略经理报告", "text": content}}
        requests.post(sign_url, json=payload)

# ==========================================
# 4. 主执行函数
# ==========================================
def run_strategy():
    """执行完整策略流程"""
    print("="*80)
    print("红利策略资产配置 - 510880 & 511260")
    print("="*80)
    
    # 加载配置
    config = load_config()
    dingtalk_config = get_dingtalk_config(config)
    gitee_config = get_gitee_config(config)
    
    print(f"配置加载完成")
    print(f"钉钉配置: access_token={dingtalk_config['access_token'][:20]}...")
    print(f"Gitee配置: owner={gitee_config['owner']}, repo={gitee_config['repo']}")
    print("-"*80)
    
    # 获取数据
    print("正在获取数据...")
    df = get_strategy_data()
    print(f"数据获取完成，共{len(df)}条记录")
    
    # 计算指标
    print("正在计算指标...")
    df = calculate_indicators(df)
    
    # 生成图表
    print("正在生成图表...")
    image_path = generate_chart(df)
    print(f"图表已保存: {image_path}")
    
    # 上传到Gitee
    print("正在上传图片到Gitee...")
    online_img_url = upload_to_gitee(image_path, gitee_config)
    
    # 钉钉推送
    print("正在发送钉钉报告...")
    curr_diff = df['diff_pct'].iloc[-1]
    curr_div_dd = df['div_drawdown'].iloc[-1]
    curr_change = df['diff_pct'].iloc[-1] - df['diff_pct'].iloc[-2]
    curr_date = df['date'].iloc[-1].strftime('%Y-%m-%d')
    
    bot = DingTalkManager(dingtalk_config['access_token'], dingtalk_config['secret'])
    bot.send_professional_report(curr_diff, curr_div_dd, curr_change, curr_date, online_img_url)
    
    print("钉钉报告发送完成")
    print("="*80)
    
    return {
        'diff_pct': curr_diff,
        'div_drawdown': curr_div_dd,
        'diff_change': curr_change,
        'date': curr_date,
        'img_url': online_img_url
    }

if __name__ == "__main__":
    result = run_strategy()
    print("\n策略执行结果:")
    print(f"物理偏离度: {result['diff_pct']:.2f}%")
    print(f"510880回撤: {result['div_drawdown']:.2f}%")
    print(f"偏离度变动: {result['diff_change']:+.2f}%")
    print(f"更新日期: {result['date']}")
    print(f"图表链接: {result['img_url']}")
