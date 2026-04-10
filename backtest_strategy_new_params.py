
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
    
    # 1. 短周期 KDJ (8,2,3)
    low8 = df['最低'].rolling(window=8, min_periods=1).min()
    high8 = df['最高'].rolling(window=8, min_periods=1).max()
    rsv = (df['收盘'] - low8) / (high8 - low8) * 100
    rsv = rsv.fillna(50)
    
    dxd = rsv.ewm(alpha=1/2, adjust=False).mean()  # SMA(RSV,2,1)
    dxk = dxd.ewm(alpha=1/3, adjust=False).mean()  # SMA(DXD,3,1)
    
    # 2. 长周期 KDJ (18,2,4)
    low18 = df['最低'].rolling(window=18, min_periods=1).min()
    high18 = df['最高'].rolling(window=18, min_periods=1).max()
    rsv1 = (df['收盘'] - low18) / (high18 - low18) * 100
    rsv1 = rsv1.fillna(50)
    
    zxd = rsv1.ewm(alpha=1/2, adjust=False).mean()  # SMA(RSV1,2,1)
    zxk = zxd.ewm(alpha=1/4, adjust=False).mean()  # SMA(ZXD,4,1)
    
    # 3. ATR 和 ADX (10,5)
    prev_close = df['收盘'].shift(1)
    tr1 = pd.DataFrame({
        'hl': df['最高'] - df['最低'],
        'hc': abs(prev_close - df['最高']),
        'lc': abs(prev_close - df['最低'])
    }).max(axis=1)
    atr = tr1.rolling(window=10, min_periods=1).mean()
    
    hd = df['最高'] - df['最高'].shift(1)
    ld = df['最低'].shift(1) - df['最低']
    
    dmp = np.where((hd > 0) & (hd > ld), hd, 0)
    dmm = np.where((ld > 0) & (ld > hd), ld, 0)
    
    dmp_series = pd.Series(dmp, index=df.index)
    dmm_series = pd.Series(dmm, index=df.index)
    
    # PDI, MDI
    sma_dmp = dmp_series.rolling(window=10, min_periods=1).mean()
    sma_dmm = dmm_series.rolling(window=10, min_periods=1).mean()
    
    pdi = sma_dmp * 100 / atr
    mdi = sma_dmm * 100 / atr
    
    # ADX
    adx_raw = abs(mdi - pdi) / (mdi + pdi) * 100
    adx_raw = adx_raw.fillna(0)
    adx = adx_raw.rolling(window=5, min_periods=1).mean()
    
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

def backtest_stock(df, stock_code, stock_name):
    """对单只股票进行回测（不带大盘过滤）"""
    df = df.copy()
    df = calculate_indicators(df)
    
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
        
        # 模拟交易（每次买入独立，卖出时结算所有未结算的买入）
        trades = []
        portfolio_values = []
        initial_cash = 100000  # 每只股票独立初始资金10万
        cash = initial_cash
        entry_trades = []  # 记录每次买入的信息（未结算的买入
        
        for i in range(len(phase_df)):
            current = phase_df.iloc[i]
            current_date = current['日期']
            
            # 不记录组合价值，只跟踪买入-卖出配对
            
            # 检查前一天的信号，第二天开盘交易
            if i > 0:
                prev = phase_df.iloc[i-1]
                
                # 买入信号：前一天收盘出现扬帆起航，今天开盘买入（不带大盘过滤，每次固定买100股）
                if prev['扬帆起航']:
                    open_price = current['开盘']
                    if pd.notna(open_price) and open_price > 0:
                        # 每次固定买100股
                        buy_shares = 100
                        
                        cost = buy_shares * open_price
                        cash -= cost
                        entry_trades.append({
                            '价格': open_price,
                            '数量': buy_shares,
                            '日期': current_date
                        })
                        trades.append({
                            '日期': current_date,
                            '类型': '买入',
                            '价格': open_price,
                            '数量': buy_shares,
                            '金额': cost
                        })
                
                # 卖出信号：前一天收盘出现避风靠岸（个股信号），今天开盘结算所有未结算的买入
                sell_signal = False
                if prev['避风靠岸'] and len(entry_trades) > 0:
                    sell_signal = True
                    
                if sell_signal and len(entry_trades) > 0:
                    open_price = current['开盘']
                    if pd.notna(open_price) and open_price > 0:
                        # 把每个未结算的买入都单独结算
                        for entry in entry_trades:
                            revenue = entry['数量'] * open_price
                            cash += revenue
                            profit = revenue - (entry['价格'] * entry['数量'])
                            profit_pct = (profit / (entry['价格'] * entry['数量'])) * 100 if (entry['价格'] * entry['数量']) > 0 else 0
                            
                            trades.append({
                                '日期': current_date,
                                '类型': '卖出',
                                '价格': open_price,
                                '数量': entry['数量'],
                                '金额': revenue,
                                '利润': profit,
                                '利润率': profit_pct,
                                '持仓天数': (current_date - entry['日期']).days,
                                '对应买入日期': entry['日期'].strftime('%Y-%m-%d')
                            })
                        
                        # 清空未结算的买入
                        entry_trades = []
        
        # 最后如果还有未结算的买入，按最后收盘价单独结算
        if len(entry_trades) > 0 and len(phase_df) > 0:
            last = phase_df.iloc[-1]
            close_price = last['收盘']
            if pd.notna(close_price) and close_price > 0:
                # 把每个未结算的买入都单独结算
                for entry in entry_trades:
                    revenue = entry['数量'] * close_price
                    cash += revenue
                    profit = revenue - (entry['价格'] * entry['数量'])
                    profit_pct = (profit / (entry['价格'] * entry['数量'])) * 100 if (entry['价格'] * entry['数量']) > 0 else 0
                    
                    trades.append({
                        '日期': last['日期'],
                        '类型': '结算',
                        '价格': close_price,
                        '数量': entry['数量'],
                        '金额': revenue,
                        '利润': profit,
                        '利润率': profit_pct,
                        '持仓天数': (last['日期'] - entry['日期']).days,
                        '对应买入日期': entry['日期'].strftime('%Y-%m-%d')
                    })
        
        # 计算统计指标（每次买入-卖出配对独立）
        buy_trades = [t for t in trades if t['类型'] == '买入']
        sell_trades = [t for t in trades if t['类型'] in ['卖出', '结算']]
        profitable_trades = [t for t in sell_trades if t.get('利润率', 0) > 0]
        
        # 计算所有配对的平均收益率
        if len(sell_trades) > 0:
            avg_return = np.mean([t.get('利润率', 0) for t in sell_trades])
        else:
            avg_return = 0
        
        # 计算最大回撤（暂时简化，用0，因为每次配对独立）
        max_drawdown = 0
        
        # 计算年化收益（暂时简化，用平均收益率）
        annual_return = avg_return
        
        # 胜率 = 盈利配对数 / 总配对数
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
            '总收益': round(avg_return, 2),
            '最大回撤': round(max_drawdown, 2),
            '年化收益': round(annual_return, 2),
            '初始资金': initial_cash,
            '最终资金': round(cash, 2),
            '交易明细': trades
        }
    
    return results, df

def main():
    # 读取数据
    df = pd.read_csv('stock_data_adjusted.csv')
    
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
            results, df_with_indicators = backtest_stock(group, stock_code, stock_name)
            
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
    results_df.to_csv('backtest_results_new_params.csv', index=False, encoding='utf-8-sig')
    
    trades_df = pd.DataFrame(all_trades)
    trades_df.to_csv('backtest_trades_new_params.csv', index=False, encoding='utf-8-sig')
    
    print("\n" + "="*80)
    print("回测完成（不带大盘过滤，新参数）！")
    print(f"共回测 {len(stock_groups)-1} 只股票")
    print(f"结果已保存到: backtest_results_new_params.csv 和 backtest_trades_new_params.csv")
    print("="*80)
    
    # 打印汇总结果（按用户要求的口径：每只股票总收益率=所有配对利润率之和，然后平均）
    print("\n" + "="*100)
    print("回测结果汇总（不带大盘过滤，新参数）")
    print("="*100)
    print("\n计算口径：")
    print("  1. 每只股票总收益率 = 该股票所有买入-卖出配对利润率之和")
    print("  2. 阶段平均收益率 = 该阶段所有股票总收益率之和 ÷ 股票数量")
    print("="*100)
    
    for phase in ['牛市', '震荡', '熊市']:
        print(f"\n\n【{phase}】")
        print("-"*100)
        
        # 获取该阶段的所有交易
        phase_trades = [t for t in all_trades if t['阶段'] == phase]
        
        # 按股票分组
        stock_phase_returns = {}
        for trade in phase_trades:
            if trade['类型'] in ['卖出', '结算']:
                stock_code = trade['股票代码']
                if stock_code not in stock_phase_returns:
                    stock_phase_returns[stock_code] = {
                        '名称': trade['股票名称'],
                        '配对次数': 0,
                        '总收益率': 0
                    }
                stock_phase_returns[stock_code]['配对次数'] += 1
                stock_phase_returns[stock_code]['总收益率'] += trade.get('利润率', 0)
        
        if len(stock_phase_returns) > 0:
            # 打印该阶段的股票结果
            print(f'\n该阶段共 {len(stock_phase_returns)} 只股票:')
            sorted_stocks = sorted(stock_phase_returns.items(), key=lambda x: -x[1]['总收益率'])
            for stock_code, r in sorted_stocks:
                print('  {}({}): {}次配对, 总收益率 = {:.2f}%'.format(
                    r['名称'], stock_code, r['配对次数'], r['总收益率']))
            
            # 计算该阶段的平均收益率
            all_returns = [r['总收益率'] for r in stock_phase_returns.values()]
            avg_return = pd.Series(all_returns).mean()
            
            print('\n' + '-'*100)
            print(f'【{phase}平均收益率】')
            print('所有股票总收益率之和 = {:.2f}%'.format(sum(all_returns)))
            print('股票数量 = {}'.format(len(all_returns)))
            print('平均收益率 = {:.2f}% ÷ {} = {:.2f}%'.format(
                sum(all_returns), len(all_returns), avg_return))
        else:
            print('该阶段没有数据')

if __name__ == '__main__':
    main()
