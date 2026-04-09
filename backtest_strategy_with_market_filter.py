
import pandas as pd
import numpy as np
from datetime import datetime

def calculate_indicators(df):
    """计算通达信指标"""
    df = df.copy()
    
    # 确保日期列是 datetime 类型
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    df = df.dropna(subset=['日期'])
    df = df.sort_values('日期').reset_index(drop=True)
    
    # 1. 短周期 KDJ (9,3,3)
    low9 = df['最低'].rolling(window=9, min_periods=1).min()
    high9 = df['最高'].rolling(window=9, min_periods=1).max()
    rsv = (df['收盘'] - low9) / (high9 - low9) * 100
    rsv = rsv.fillna(50)
    
    dxd = rsv.ewm(alpha=1/3, adjust=False).mean()  # SMA(RSV,3,1)
    dxk = dxd.ewm(alpha=1/3, adjust=False).mean()  # SMA(DXD,3,1)
    
    # 2. 长周期 KDJ (21,3,5)
    low21 = df['最低'].rolling(window=21, min_periods=1).min()
    high21 = df['最高'].rolling(window=21, min_periods=1).max()
    rsv1 = (df['收盘'] - low21) / (high21 - low21) * 100
    rsv1 = rsv1.fillna(50)
    
    zxd = rsv1.ewm(alpha=1/3, adjust=False).mean()  # SMA(RSV1,3,1)
    zxk = zxd.ewm(alpha=1/5, adjust=False).mean()  # SMA(ZXD,5,1)
    
    # 3. ATR 和 ADX
    prev_close = df['收盘'].shift(1)
    tr1 = pd.DataFrame({
        'hl': df['最高'] - df['最低'],
        'hc': abs(prev_close - df['最高']),
        'lc': abs(prev_close - df['最低'])
    }).max(axis=1)
    atr = tr1.rolling(window=14, min_periods=1).mean()
    
    hd = df['最高'] - df['最高'].shift(1)
    ld = df['最低'].shift(1) - df['最低']
    
    dmp = np.where((hd > 0) & (hd > ld), hd, 0)
    dmm = np.where((ld > 0) & (ld > hd), ld, 0)
    
    dmp_series = pd.Series(dmp, index=df.index)
    dmm_series = pd.Series(dmm, index=df.index)
    
    # PDI, MDI
    sma_dmp = dmp_series.rolling(window=14, min_periods=1).mean()
    sma_dmm = dmm_series.rolling(window=14, min_periods=1).mean()
    
    pdi = sma_dmp * 100 / atr
    mdi = sma_dmm * 100 / atr
    
    # ADX
    adx_raw = abs(mdi - pdi) / (mdi + pdi) * 100
    adx_raw = adx_raw.fillna(0)
    adx = adx_raw.rolling(window=6, min_periods=1).mean()
    
    # 4. 趋势判断
    trend_market = adx > 25
    range_market = adx <= 25
    
    # 5. 信号生成
    td = ((dxd >= dxk) | (zxd >= zxk)) & trend_market
    tk = ((dxd < dxk) & (zxd < zxk)) & (~td) & trend_market
    
    # 保存指标
    df['RSV'] = rsv
    df['DXD'] = dxd
    df['DXK'] = dxk
    df['RSV1'] = rsv1
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
    
    # 6. 交叉信号 (扬帆起航/避风靠岸)
    df['TD_prev'] = df['TD'].shift(1)
    df['TK_prev'] = df['TK'].shift(1)
    df['震荡市_prev'] = df['震荡市'].shift(1)
    
    df['扬帆起航'] = (df['TD'] == True) & (df['TD_prev'] == False)
    df['避风靠岸'] = (df['TK'] == True) & (df['TK_prev'] == False)
    df['波涛汹涌'] = (df['震荡市'] == True) & (df['震荡市_prev'] == False)
    
    return df

def backtest_stock(df, stock_code, stock_name, market_df):
    """对单只股票进行回测（带大盘过滤）"""
    df = df.copy()
    df = calculate_indicators(df)
    
    # Merge with market signals (on date)
    market_df_reindexed = market_df.set_index('日期')[['TK', '避风靠岸']].add_prefix('market_').reset_index()
    df = pd.merge(df, market_df_reindexed, on='日期', how='left')
    df['market_TK'] = df['market_TK'].fillna(False)
    df['market_避风靠岸'] = df['market_避风靠岸'].fillna(False)
    
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
        position = 0  # 0: 空仓, 1: 持仓
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
            
            # 记录组合价值
            if shares > 0:
                portfolio_value = cash + shares * current['收盘']
            else:
                portfolio_value = cash
            portfolio_values.append({
                '日期': current_date,
                '组合价值': portfolio_value,
                '持仓': shares > 0
            })
            
            # 检查前一天的信号，第二天开盘交易
            if i > 0:
                prev = phase_df.iloc[i-1]
                
                # 计算当前持仓的利润（如果有）
                current_profit = 0
                if position == 1:
                    current_profit = (current['收盘'] - entry_price) * shares
                
                # 买入信号：前一天收盘出现扬帆起航，今天开盘买入，且大盘不在避风靠岸状态
                if prev['扬帆起航'] and position == 0 and not prev['market_避风靠岸']:
                    open_price = current['开盘']
                    if pd.notna(open_price) and open_price > 0:
                        shares = int(cash / open_price / 100) * 100  # 买整手
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
                
                # 卖出信号：
                # 1. 前一天收盘出现避风靠岸（个股信号），今天开盘卖出
                # OR
                # 2. 前一天大盘出现避风靠岸信号，且当前有盈利，今天开盘卖出
                sell_signal = False
                if prev['避风靠岸'] and position == 1:
                    sell_signal = True
                elif prev['market_避风靠岸'] and position == 1 and current_profit > 0:
                    sell_signal = True
                    
                if sell_signal:
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
        
        # 最后如果还有持仓，按最后收盘价结算
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
        
        # 计算统计指标
        buy_trades = [t for t in trades if t['类型'] == '买入']
        sell_trades = [t for t in trades if t['类型'] in ['卖出', '结算']]
        profitable_trades = [t for t in sell_trades if t.get('利润', 0) > 0]
        
        total_return = (cash - initial_cash) / initial_cash * 100
        
        # 计算最大回撤
        if len(portfolio_values) > 0:
            pv_df = pd.DataFrame(portfolio_values)
            pv_df['累计最高'] = pv_df['组合价值'].cummax()
            pv_df['回撤'] = (pv_df['累计最高'] - pv_df['组合价值']) / pv_df['累计最高'] * 100
            max_drawdown = pv_df['回撤'].max() if len(pv_df) > 0 else 0
        else:
            max_drawdown = 0
        
        # 计算年化收益
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

def main():
    # 读取数据
    df = pd.read_csv('stock_data.csv')
    
    # First calculate market (SH#999999) indicators
    print("Calculating market (SH#999999) indicators...")
    sh_df = df[df['股票代码'] == 999999].copy()
    market_df = calculate_indicators(sh_df)
    
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
    
    all_results = []
    all_trades = []
    
    # 按股票分组回测（跳过 SH#999999 itself）
    stock_groups = df.groupby('股票代码')
    
    for stock_code, group in stock_groups:
        if stock_code == 999999:
            continue  # Skip market index itself
        stock_name = stock_names.get(stock_code, f'股票{stock_code}')
        print(f"正在回测: {stock_code} - {stock_name}")
        
        try:
            results, df_with_indicators = backtest_stock(group, stock_code, stock_name, market_df)
            
            for phase_name, result in results.items():
                all_results.append(result)
                
                # 保存交易明细
                for trade in result.get('交易明细', []):
                    trade['股票代码'] = stock_code
                    trade['股票名称'] = stock_name
                    trade['阶段'] = phase_name
                    all_trades.append(trade)
                    
        except Exception as e:
            print(f"回测 {stock_code} 出错: {e}")
            import traceback
            traceback.print_exc()
    
    # 保存结果
    results_df = pd.DataFrame(all_results)
    results_df.to_csv('backtest_results_with_market_filter.csv', index=False, encoding='utf-8-sig')
    
    trades_df = pd.DataFrame(all_trades)
    trades_df.to_csv('backtest_trades_with_market_filter.csv', index=False, encoding='utf-8-sig')
    
    print("\n" + "="*80)
    print("带大盘过滤的回测完成！")
    print(f"共回测 {len(stock_groups)-1} 只股票")
    print(f"结果已保存到: backtest_results_with_market_filter.csv 和 backtest_trades_with_market_filter.csv")
    print("="*80)
    
    # 打印汇总结果
    print("\n" + "="*80)
    print("带大盘过滤的回测结果汇总")
    print("="*80)
    
    for phase in ['牛市', '震荡', '熊市']:
        print(f"\n【{phase}】")
        phase_results = results_df[results_df['阶段'] == phase]
        
        if len(phase_results) > 0:
            print(f"平均胜率: {phase_results['胜率'].mean():.2f}%")
            print(f"平均总收益: {phase_results['总收益'].mean():.2f}%")
            print(f"平均最大回撤: {phase_results['最大回撤'].mean():.2f}%")
            print(f"平均年化收益: {phase_results['年化收益'].mean():.2f}%")
            
            # 收益最好的3只股票
            top3 = phase_results.nlargest(3, '总收益')
            print("\n收益 TOP 3:")
            for _, row in top3.iterrows():
                print(f"  {row['股票名称']}({row['股票代码']}): {row['总收益']:.2f}%, 胜率{row['胜率']:.2f}%")

if __name__ == '__main__':
    main()
