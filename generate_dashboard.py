
import pandas as pd
import json

# --- 读取数据 ---
print("Reading backtest data...")
results_df = pd.read_csv('backtest_results_with_market_filter.csv')
trades_df = pd.read_csv('backtest_trades_with_market_filter.csv')
stock_data_df = pd.read_csv('stock_data.csv')

# --- 股票名称映射 ---
stock_names = {
    34: '神州数码',
    703: '恒逸石化',
    807: '云铝股份',
    2273: '水晶光电',
    2432: '九安医疗',
    2466: '天齐锂业',
    2607: '中公教育',
    300394: '天孚通信',
    300750: '宁德时代',
    600519: '贵州茅台',
    600522: '中天科技',
    600875: '东方电气',
    601088: '中国神华',
    601288: '农业银行',
    601319: '中国人保',
    601857: '中国石油',
    601872: '招商轮船',
    603816: '中国人保'
}

# --- 准备数据结构 ---
all_data = {
    'prices': {},
    'trades': {},
    'results': {}
}

# 1. 准备整体汇总结果
print("Preparing summary results...")
for phase in ['牛市', '震荡', '熊市']:
    phase_results = results_df[results_df['阶段'] == phase]
    all_data['results'][phase] = phase_results[[
        '股票代码', '股票名称', '交易次数', '胜率', '总收益', '最大回撤', '年化收益'
    ]].rename(columns={
        '股票代码': 'code',
        '股票名称': 'name',
        '交易次数': 'trades',
        '胜率': 'winRate',
        '总收益': 'totalReturn',
        '最大回撤': 'maxDrawdown',
        '年化收益': 'annualReturn'
    }).to_dict('records')

# 2. 准备每个股票的价格和交易数据
print("Preparing price and trade data for each stock...")
from backtest_strategy_with_market_filter import calculate_indicators

# 先计算所有股票的指标（用于信号）
stock_groups = stock_data_df.groupby('股票代码')

for stock_code, group in stock_groups:
    if stock_code == 999999:
        continue
    stock_code_int = int(stock_code)
    if stock_code_int not in stock_names:
        continue
    
    print(f"Processing {stock_names[stock_code_int]} ({stock_code_int})...")
    
    # 计算指标
    df_with_indicators = calculate_indicators(group.copy())
    
    all_data['prices'][str(stock_code_int)] = {}
    all_data['trades'][str(stock_code_int)] = {}
    
    for phase in ['牛市', '震荡', '熊市']:
        # 确定阶段日期范围
        if phase == '牛市':
            start_date, end_date = '2025-05-01', '2025-10-31'
        elif phase == '震荡':
            start_date, end_date = '2024-11-01', '2025-04-01'
        else:
            start_date, end_date = '2024-05-20', '2024-09-12'
        
        # 筛选价格数据
        phase_start = pd.to_datetime(start_date)
        phase_end = pd.to_datetime(end_date)
        mask = (df_with_indicators['日期'] >= phase_start) & (df_with_indicators['日期'] <= phase_end)
        phase_prices = df_with_indicators[mask][['日期', '收盘']].copy()
        phase_prices['日期'] = phase_prices['日期'].dt.strftime('%Y-%m-%d')
        all_data['prices'][str(stock_code_int)][phase] = phase_prices.rename(columns={'收盘': 'close'}).to_dict('records')
        
        # 筛选交易数据
        phase_trades = trades_df[
            (trades_df['股票代码'] == stock_code_int) & (trades_df['阶段'] == phase)
        ][['日期', '类型', '价格', '数量', '利润', '利润率']].copy()
        phase_trades['日期'] = pd.to_datetime(phase_trades['日期']).dt.strftime('%Y-%m-%d')
        all_data['trades'][str(stock_code_int)][phase] = phase_trades.rename(columns={
            '类型': 'type',
            '价格': 'price',
            '数量': 'qty',
            '利润率': 'profitPct'
        }).to_dict('records')

# --- 读取HTML模板并嵌入数据 ---
print("Generating HTML dashboard...")
with open('backtest_dashboard.html', 'r', encoding='utf-8') as f:
    html_template = f.read()

# 替换loadSampleData部分
data_json = json.dumps(all_data, ensure_ascii=False)
new_html = html_template.replace(
    'loadSampleData();',
    f'allData = {data_json};'
)

# 保存
with open('backtest_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print("Dashboard generated successfully! Saved as backtest_dashboard.html")
