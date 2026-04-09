
import pandas as pd
import numpy as np
from datetime import datetime

def calculate_indicators(df, kdj_short_n=9, kdj_short_m1=3, kdj_short_m2=3, 
                       kdj_long_n=21, kdj_long_m1=3, kdj_long_m2=5,
                       adx_n=14, adx_smooth=6):
    """计算通达信指标（支持参数调整）"""
    df = df.copy()
    
    # 确保日期列是 datetime 类型
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    df = df.dropna(subset=['日期'])
    df = df.sort_values('日期').reset_index(drop=True)
    
    # 1. 短周期 KDJ
    low_short = df['最低'].rolling(window=kdj_short_n, min_periods=1).min()
    high_short = df['最高'].rolling(window=kdj_short_n, min_periods=1).max()
    rsv_short = (df['收盘'] - low_short) / (high_short - low_short) * 100
    rsv_short = rsv_short.fillna(50)
    
    dxd = rsv_short.ewm(alpha=1/kdj_short_m1, adjust=False).mean()
    dxk = dxd.ewm(alpha=1/kdj_short_m2, adjust=False).mean()
    
    # 2. 长周期 KDJ
    low_long = df['最低'].rolling(window=kdj_long_n, min_periods=1).min()
    high_long = df['最高'].rolling(window=kdj_long_n, min_periods=1).max()
    rsv_long = (df['收盘'] - low_long) / (high_long - low_long) * 100
    rsv_long = rsv_long.fillna(50)
    
    zxd = rsv_long.ewm(alpha=1/kdj_long_m1, adjust=False).mean()
    zxk = zxd.ewm(alpha=1/kdj_long_m2, adjust=False).mean()
    
    # 3. ATR 和 ADX
    prev_close = df['收盘'].shift(1)
    tr1 = pd.DataFrame({
        'hl': df['最高'] - df['最低'],
        'hc': abs(prev_close - df['最高']),
        'lc': abs(prev_close - df['最低'])
    }).max(axis=1)
    atr = tr1.rolling(window=adx_n, min_periods=1).mean()
    
    hd = df['最高'] - df['最高'].shift(1)
    ld = df['最低'].shift(1) - df['最低']
    
    dmp = np.where((hd > 0) & (hd > ld), hd, 0)
    dmm = np.where((ld > 0) & (ld > hd), ld, 0)
    
    dmp_series = pd.Series(dmp, index=df.index)
    dmm_series = pd.Series(dmm, index=df.index)
    
    # PDI, MDI
    sma_dmp = dmp_series.rolling(window=adx_n, min_periods=1).mean()
    sma_dmm = dmm_series.rolling(window=adx_n, min_periods=1).mean()
    
    pdi = sma_dmp * 100 / atr
    mdi = sma_dmm * 100 / atr
    
    # ADX
    adx_raw = abs(mdi - pdi) / (mdi + pdi) * 100
    adx_raw = adx_raw.fillna(0)
    adx = adx_raw.rolling(window=adx_smooth, min_periods=1).mean()
    
    # 4. 趋势判断
    trend_market = adx > 25
    range_market = adx <= 25
    
    # 5. 信号生成
    td = ((dxd >= dxk) | (zxd >= zxk)) & trend_market
    tk = ((dxd < dxk) & (zxd < zxk)) & (~td) & trend_market
    
    # 保存指标
    df['RSV'] = rsv_short
    df['DXD'] = dxd
    df['DXK'] = dxk
    df['RSV1'] = rsv_long
    df['ZXD'] = zxd
    df['ZXK'] = zxk
    df['ATR'] = atr
    df['PDI'] = pdi
    df['MDI'] = mdi
    df['ADX'] = adx
    df['趋势市'] = trend_market
    df['震荡市'] = range_market
    df['TD'] = td
    df['TK'] = tk
    
    # 6. 交叉信号
    df['TD_prev'] = df['TD'].shift(1)
    df['TK_prev'] = df['TK'].shift(1)
    df['震荡市_prev'] = df['震荡市'].shift(1)
    
    df['扬帆起航'] = (df['TD'] == True) & (df['TD_prev'] == False)
    df['避风靠岸'] = (df['TK'] == True) & (df['TK_prev'] == False)
    df['波涛汹涌'] = (df['震荡市'] == True) & (df['震荡市_prev'] == False)
    
    return df

def backtest_stock(df, stock_code, stock_name, params):
    """对单只股票进行回测（不带大盘过滤）"""
    df = df.copy()
    df = calculate_indicators(df, **params)
    
    # 定义三个市场阶段
    phases = {
        '牛市': ('2025-05-01', '2025-10-31'),
        '震荡': ('2024-11-01', '2025-04-01'),
        '熊市': ('2024-05-20', '2024-09-12')
    }
    
    results = {}
    
    for phase_name, (start_date, end_date) in phases.items():
        phase_start = pd.to_datetime(start_date)
        phase_end = pd.to_datetime(end_date)
        
        # 筛选阶段数据
        mask = (df['日期'] >= phase_start) & (df['日期'] <= phase_end)
        phase_df = df[mask].copy()
        
        if len(phase_df) < 10:
            results[phase_name] = {
                '股票代码': stock_code,
                '股票名称': stock_name,
                '阶段': phase_name,
                '交易天数': len(phase_df),
                '交易次数': 0,
                '买入次数': 0,
                '卖出次数': 0,
                '总收益': 0,
                '胜率': 0,
                '最大回撤': 0,
                '年化收益': 0,
                '备注': '数据不足'
            }
            continue
        
        # 模拟交易
        position = 0
        entry_price = 0
        entry_date = None
        trades = []
        portfolio_values = []
        initial_cash = 100000
        cash = initial_cash
        shares = 0
        
        for i in range(len(phase_df)):
            current = phase_df.iloc[i]
            current_date = current['日期']
            
            if shares > 0:
                portfolio_value = cash + shares * current['收盘']
            else:
                portfolio_value = cash
            portfolio_values.append({
                '日期': current_date,
                '组合价值': portfolio_value,
                '持仓': shares > 0
            })
            
            if i > 0:
                prev = phase_df.iloc[i-1]
                
                if prev['扬帆起航'] and position == 0:
                    open_price = current['开盘']
                    if pd.notna(open_price) and open_price > 0:
                        shares = int(cash / open_price / 100) * 100
                        if shares > 0:
                            cost = shares * open_price
                            cash -= cost
                            position = 1
                            entry_price = open_price
                            entry_date = current_date
                            trades.append({
                                '日期': current_date,
                                '类型': '买入',
                                '价格': open_price,
                                '数量': shares,
                                '金额': cost
                            })
                
                elif prev['避风靠岸'] and position == 1:
                    open_price = current['开盘']
                    if pd.notna(open_price) and open_price > 0:
                        revenue = shares * open_price
                        cash += revenue
                        profit = revenue - (shares * entry_price)
                        profit_pct = (profit / (shares * entry_price)) * 100
                        position = 0
                        trades.append({
                            '日期': current_date,
                            '类型': '卖出',
                            '价格': open_price,
                            '数量': shares,
                            '金额': revenue,
                            '利润': profit,
                            '利润率': profit_pct,
                            '持仓天数': (current_date - entry_date).days
                        })
                        shares = 0
        
        if position == 1 and len(phase_df) > 0:
            last = phase_df.iloc[-1]
            close_price = last['收盘']
            if pd.notna(close_price) and close_price > 0:
                revenue = shares * close_price
                cash += revenue
                profit = revenue - (shares * entry_price)
                profit_pct = (profit / (shares * entry_price)) * 100
                trades.append({
                    '日期': last['日期'],
                    '类型': '结算',
                    '价格': close_price,
                    '数量': shares,
                    '金额': revenue,
                    '利润': profit,
                    '利润率': profit_pct,
                    '持仓天数': (last['日期'] - entry_date).days
                })
        
        buy_trades = [t for t in trades if t['类型'] == '买入']
        sell_trades = [t for t in trades if t['类型'] in ['卖出', '结算']]
        profitable_trades = [t for t in sell_trades if t.get('利润', 0) > 0]
        
        total_return = (cash - initial_cash) / initial_cash * 100
        
        if len(portfolio_values) > 0:
            pv_df = pd.DataFrame(portfolio_values)
            pv_df['累计最高'] = pv_df['组合价值'].cummax()
            pv_df['回撤'] = (pv_df['累计最高'] - pv_df['组合价值']) / pv_df['累计最高'] * 100
            max_drawdown = pv_df['回撤'].max() if len(pv_df) > 0 else 0
        else:
            max_drawdown = 0
        
        days = (phase_df['日期'].iloc[-1] - phase_df['日期'].iloc[0]).days
        if days > 0:
            annual_return = (1 + total_return / 100) ** (365 / days) - 1
            annual_return = annual_return * 100
        else:
            annual_return = 0
        
        win_rate = len(profitable_trades) / len(sell_trades) * 100 if len(sell_trades) > 0 else 0
        
        results[phase_name] = {
            '股票代码': stock_code,
            '股票名称': stock_name,
            '阶段': phase_name,
            '交易天数': len(phase_df),
            '交易次数': len(trades),
            '买入次数': len(buy_trades),
            '卖出次数': len(sell_trades),
            '盈利次数': len(profitable_trades),
            '胜率': round(win_rate, 2),
            '总收益': round(total_return, 2),
            '最大回撤': round(max_drawdown, 2),
            '年化收益': round(annual_return, 2),
            '初始资金': initial_cash,
            '最终资金': round(cash, 2),
            '交易明细': trades
        }
    
    return results, df

def calculate_buy_and_hold(df, stock_code, stock_name):
    """计算一直持有的收益"""
    df = df.copy()
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    df = df.dropna(subset=['日期'])
    df = df.sort_values('日期').reset_index(drop=True)
    
    phases = {
        '牛市': ('2025-05-01', '2025-10-31'),
        '震荡': ('2024-11-01', '2025-04-01'),
        '熊市': ('2024-05-20', '2024-09-12')
    }
    
    bh_results = {}
    for phase_name, (start_date, end_date) in phases.items():
        phase_start = pd.to_datetime(start_date)
        phase_end = pd.to_datetime(end_date)
        mask = (df['日期'] >= phase_start) & (df['日期'] <= phase_end)
        phase_df = df[mask].copy()
        
        if len(phase_df) < 2:
            bh_results[phase_name] = 0
            continue
        
        first_open = phase_df.iloc[0]['开盘']
        last_close = phase_df.iloc[-1]['收盘']
        if pd.notna(first_open) and pd.notna(last_close) and first_open > 0:
            total_return = (last_close - first_open) / first_open * 100
            bh_results[phase_name] = round(total_return, 2)
        else:
            bh_results[phase_name] = 0
    return bh_results

def main():
    # 读取数据
    df = pd.read_csv('stock_data.csv')
    
    # 股票名称映射
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
    
    # 先计算所有股票的一直持有收益作为基准
    print("Calculating buy-and-hold benchmarks...")
    bh_benchmarks = {}
    stock_groups = df.groupby('股票代码')
    for stock_code, group in stock_groups:
        if stock_code == 999999:
            continue
        stock_code_int = int(stock_code)
        if stock_code_int not in stock_names:
            continue
        bh_benchmarks[stock_code_int] = calculate_buy_and_hold(group, stock_code_int, stock_names[stock_code_int])
    
    # 参数搜索空间
    print("Starting parameter optimization...")
    best_score = -100000
    best_params = None
    best_results = None
    
    # 简单的网格搜索（先试一些关键参数组合）
    param_grid = [
        # 原参数
        {'kdj_short_n':9, 'kdj_short_m1':3, 'kdj_short_m2':3, 'kdj_long_n':21, 'kdj_long_m1':3, 'kdj_long_m2':5, 'adx_n':14, 'adx_smooth':6},
        # 尝试更短的短期KDJ
        {'kdj_short_n':7, 'kdj_short_m1':3, 'kdj_short_m2':3, 'kdj_long_n':21, 'kdj_long_m1':3, 'kdj_long_m2':5, 'adx_n':14, 'adx_smooth':6},
        # 尝试更长的长期KDJ
        {'kdj_short_n':9, 'kdj_short_m1':3, 'kdj_short_m2':3, 'kdj_long_n':34, 'kdj_long_m1':3, 'kdj_long_m2':5, 'adx_n':14, 'adx_smooth':6},
        # 尝试不同的ADX参数
        {'kdj_short_n':9, 'kdj_short_m1':3, 'kdj_short_m2':3, 'kdj_long_n':21, 'kdj_long_m1':3, 'kdj_long_m2':5, 'adx_n':10, 'adx_smooth':6},
        {'kdj_short_n':9, 'kdj_short_m1':3, 'kdj_short_m2':3, 'kdj_long_n':21, 'kdj_long_m1':3, 'kdj_long_m2':5, 'adx_n':20, 'adx_smooth':6},
        # 尝试组合
        {'kdj_short_n':8, 'kdj_short_m1':2, 'kdj_short_m2':3, 'kdj_long_n':28, 'kdj_long_m1':4, 'kdj_long_m2':6, 'adx_n':12, 'adx_smooth':5},
        {'kdj_short_n':10, 'kdj_short_m1':3, 'kdj_short_m2':4, 'kdj_long_n':18, 'kdj_long_m1':3, 'kdj_long_m2':6, 'adx_n':16, 'adx_smooth':7},
    ]
    
    for idx, params in enumerate(param_grid):
        print(f"\nTesting parameter set {idx+1}/{len(param_grid)}: {params}")
        
        all_phase_results = {'牛市': [], '震荡': [], '熊市': []}
        all_bh_results = {'牛市': [], '震荡': [], '熊市': []}
        
        for stock_code, group in stock_groups:
            if stock_code == 999999:
                continue
            stock_code_int = int(stock_code)
            if stock_code_int not in stock_names:
                continue
            
            try:
                results, _ = backtest_stock(group, stock_code_int, stock_names[stock_code_int], params)
                for phase in ['牛市', '震荡', '熊市']:
                    all_phase_results[phase].append(results[phase]['总收益'])
                    all_bh_results[phase].append(bh_benchmarks[stock_code_int][phase])
            except Exception as e:
                continue
        
        # 计算平均指标
        avg_bull_return = np.mean(all_phase_results['牛市']) if len(all_phase_results['牛市']) > 0 else 0
        avg_range_return = np.mean(all_phase_results['震荡']) if len(all_phase_results['震荡']) > 0 else 0
        avg_bear_return = np.mean(all_phase_results['熊市']) if len(all_phase_results['熊市']) > 0 else 0
        avg_bh_bull = np.mean(all_bh_results['牛市']) if len(all_bh_results['牛市']) > 0 else 0
        avg_bh_range = np.mean(all_bh_results['震荡']) if len(all_bh_results['震荡']) > 0 else 0
        avg_bh_bear = np.mean(all_bh_results['熊市']) if len(all_bh_results['熊市']) > 0 else 0
        
        # 计算得分（目标：震荡市大幅跑赢BH，熊市少亏/不亏，牛市收益不错）
        range_edge = avg_range_return - avg_bh_range  # 震荡市超额收益
        bear_loss = avg_bear_return  # 熊市收益（越高越好，最好≥0）
        bull_return = avg_bull_return  # 牛市收益
        
        # 简单的评分函数
        score = (range_edge * 3) + (bear_loss * 2) + (bull_return * 1)
        
        print(f"  平均收益 - 牛市: {avg_bull_return:.2f}%, 震荡: {avg_range_return:.2f}%, 熊市: {avg_bear_return:.2f}%")
        print(f"  对比BH   - 牛市: {avg_bh_bull:.2f}%, 震荡: {avg_bh_range:.2f}%, 熊市: {avg_bh_bear:.2f}%")
        print(f"  得分: {score:.2f}")
        
        if score > best_score:
            best_score = score
            best_params = params
            best_results = {
                'avg_bull': avg_bull_return,
                'avg_range': avg_range_return,
                'avg_bear': avg_bear_return,
                'avg_bh_bull': avg_bh_bull,
                'avg_bh_range': avg_bh_range,
                'avg_bh_bear': avg_bh_bear,
                'score': score
            }
            print(f"  ✨ New best score!")
    
    print("\n" + "="*80)
    print("最优参数找到！")
    print("="*80)
    print(f"参数: {best_params}")
    print(f"得分: {best_results['score']:.2f}")
    print(f"平均收益：")
    print(f"  牛市: {best_results['avg_bull']:.2f}% (BH: {best_results['avg_bh_bull']:.2f}%)")
    print(f"  震荡: {best_results['avg_range']:.2f}% (BH: {best_results['avg_bh_range']:.2f}%), 超额: {best_results['avg_range']-best_results['avg_bh_range']:.2f}%")
    print(f"  熊市: {best_results['avg_bear']:.2f}% (BH: {best_results['avg_bh_bear']:.2f}%)")
    print("="*80)

if __name__ == '__main__':
    main()
