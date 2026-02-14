import requests
import json
import hmac
import hashlib
import base64
import urllib.parse
import time

class DingTalkBot:
    """
    钉钉机器人发送消息类
    支持文本、Markdown等消息类型
    """
    
    def __init__(self, access_token, secret):
        """
        初始化钉钉机器人
        
        :param access_token: 钉钉机器人的access_token
        :param secret: 钉钉机器人的加签密钥
        """
        self.access_token = access_token
        self.secret = secret
        self.webhook_url = f"https://oapi.dingtalk.com/robot/send?access_token={access_token}"
    
    def _generate_sign(self, timestamp):
        """
        生成签名
        
        :param timestamp: 当前时间戳（毫秒）
        :return: 签名字符串
        """
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{self.secret}'
        string_to_sign_enc = string_to_sign.encode('utf-8')
        
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        
        return sign
    
    def send_text(self, text, at_mobiles=None, at_all=False):
        """
        发送文本消息
        
        :param text: 文本内容
        :param at_mobiles: @的手机号列表
        :param at_all: 是否@所有人
        :return: 发送结果
        """
        timestamp = str(round(time.time() * 1000))
        sign = self._generate_sign(timestamp)
        
        url = f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"
        
        data = {
            "msgtype": "text",
            "text": {
                "content": text
            },
            "at": {
                "atMobiles": at_mobiles or [],
                "isAtAll": at_all
            }
        }
        
        return self._send_request(url, data)
    
    def send_markdown(self, title, text, at_mobiles=None, at_all=False):
        """
        发送Markdown消息
        
        :param title: 标题
        :param text: Markdown文本内容
        :param at_mobiles: @的手机号列表
        :param at_all: 是否@所有人
        :return: 发送结果
        """
        timestamp = str(round(time.time() * 1000))
        sign = self._generate_sign(timestamp)
        
        url = f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"
        
        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": text
            },
            "at": {
                "atMobiles": at_mobiles or [],
                "isAtAll": at_all
            }
        }
        
        return self._send_request(url, data)
    
    def _send_request(self, url, data):
        """
        发送HTTP请求
        
        :param url: 请求URL
        :param data: 请求数据
        :return: 响应结果
        """
        headers = {
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data, ensure_ascii=False))
            result = response.json()
            
            if result.get('errcode') == 0:
                return {'success': True, 'message': '发送成功', 'data': result}
            else:
                return {'success': False, 'message': result.get('errmsg', '发送失败'), 'data': result}
                
        except Exception as e:
            return {'success': False, 'message': f'请求异常: {str(e)}', 'data': None}


def send_strategy_report_to_dingding(strategy_result, bot, user_info=None):
    """
    将策略报告发送到钉钉
    
    :param strategy_result: 策略运行结果
    :param bot: DingTalkBot实例
    :param user_info: 用户信息字典，包含age, annual_income, total_capital, monthly_expense等
    :return: 发送结果
    """
    macro_info = strategy_result['macro_info']
    selected_etfs = strategy_result['selected_etfs']
    weights = strategy_result['weights']
    investment_plan = strategy_result['investment_plan']
    
    # 获取用户信息，如果没有提供则使用默认值
    if user_info is None:
        user_info = {
            'age': '未提供',
            'annual_income': '未提供',
            'total_capital': 20000000,
            'monthly_expense': '未提供',
            'risk_level': '未提供',
            'investment_experience': '未提供',
            'career_stage': '未提供',
            'aggressive_ratio': 0.8,
            'aggressive_capital': 20000000
        }
    
    # 构建Markdown消息
    markdown_text = f"""## 📊 非线性两步法ETF投资策略报告

### 👤 用户信息
- **年龄**: {user_info.get('age', '未提供')}
- **年收入**: ¥{user_info.get('annual_income', '未提供'):,}
- **总投资资金**: ¥{user_info.get('total_capital', 0):,}
- **职业生涯阶段**: {user_info.get('career_stage', '未提供')}
- **风险偏好**: {user_info.get('risk_level', '未提供')}
- **投资经验**: {user_info.get('investment_experience', '未提供')}

### � 资金配置
- **进取类投资比例**: {user_info.get('aggressive_ratio', 0.8)*100:.1f}%
- **进取类投资资金**: ¥{user_info.get('aggressive_capital', 0):,}
- **其他资产配置**: ¥{user_info.get('total_capital', 0) - user_info.get('aggressive_capital', 0):,} (低风险资产)

### � 宏观仓位分析（基于进取类投资资金）
- **全市场估值分位**: {macro_info['market_percentile']:.1f}%
- **市场信号**: {macro_info['signal']}
- **建议仓位**: {macro_info['macro_position']*100:.1f}%
- **可用资金**: ¥{macro_info['available_capital']:,.0f}
- **闲置资金**: ¥{macro_info['idle_capital']:,.0f}

### 🎯 性价比最高的3个ETF
"""
    
    for i, etf in enumerate(selected_etfs, 1):
        markdown_text += f"""
#### {i}. {etf['name']}
- 估值分位: {etf['percentile']:.1f}%
- 当前PE: {etf['current_value']:.2f}
- 综合得分: {etf['total_score']:.1f}
"""
    
    markdown_text += f"""
### 💰 投资计划
| ETF名称 | 估值分位 | 风险等级 | 权重 | 投资金额 | 预估份额 |
|---------|---------|---------|------|---------|---------|
"""
    
    for item in investment_plan:
        markdown_text += f"| {item['etf_name']} | {item['valuation_percentile']} | {item['risk_level']} | {item['weight']} | {item['invest_amount']} | {item['estimated_shares']} |\n"
    
    total_invested = sum([float(p['invest_amount'].replace('¥', '').replace(',', '')) 
                         for p in investment_plan])
    aggressive_capital = user_info.get('aggressive_capital', 20000000)
    efficiency = total_invested / aggressive_capital * 100
    
    markdown_text += f"""
### 📊 资金效率分析
- **实际投资金额**: ¥{total_invested:,.0f}
- **进取类资金使用率**: {efficiency:.1f}%
- **建议货币基金配置**: ¥{macro_info['idle_capital']:,.0f} (来自进取类资金)
- **总资金使用率**: {total_invested / user_info.get('total_capital', 20000000) * 100:.1f}%

---
*报告生成时间: {strategy_result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    # 发送消息
    result = bot.send_markdown("非线性两步法ETF投资策略报告", markdown_text)
    
    return result


def send_text_to_dingding(text, bot):
    """
    发送普通文本到钉钉
    
    :param text: 文本内容
    :param bot: DingTalkBot实例
    :return: 发送结果
    """
    result = bot.send_text(text)
    return result


if __name__ == "__main__":
    # 配置钉钉机器人
    MY_ACCESS_TOKEN = "93d77b7421d98344c580175f59ee74a88fde3910a8050c8c548be3bfdca4152d"
    MY_SECRET = "SEC05951317384421f5f6d3919dec390acd7d0771b85a9c7318dfce1329adf4d38e"
    
    # 创建机器人实例
    bot = DingTalkBot(MY_ACCESS_TOKEN, MY_SECRET)
    
    # 测试发送文本消息
    print("测试发送文本消息...")
    result = bot.send_text("🤖 钉钉机器人测试消息：配置成功！")
    print(f"发送结果: {result}")
    
    # 测试发送Markdown消息
    print("\n测试发送Markdown消息...")
    markdown_text = """## 📊 测试Markdown消息

### 这是一个测试标题
- 测试项目1
- 测试项目2
- 测试项目3

**粗体文本** 和 *斜体文本*

---
*测试完成*
"""
    result = bot.send_markdown("测试Markdown消息", markdown_text)
    print(f"发送结果: {result}")
