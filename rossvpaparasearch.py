import yfinance as yf

import pandas as pd

import numpy as np

from itertools import product

import warnings

import time

import os



warnings.simplefilter(action='ignore', category=FutureWarning)



def get_max_data(ticker, interval):

    limit_map = {"15m": "60d", "60m": "730d"}

    period = limit_map.get(interval, "60d")

    print(f"[{ticker}] {interval}足 取得中...")

    data = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)

    if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)

    return data



def backtest_hybrid(df, rsi_up, rsi_lo, vol_m, lb, switch_th):

    u_wick = (df['High'] - df[['Close', 'Open']].max(axis=1)).values

    l_wick = (df[['Close', 'Open']].min(axis=1) - df['Low']).values

    body = (df['Close'] - df['Open']).abs().values

    close_pct = df['Close'].pct_change().values

    v_spike = (df['Volume'] > (df['Volume'].rolling(20).mean() * vol_m)).values

    rsi = df['RSI'].values

    b_up = df['High'].rolling(lb).max().values

    b_lo = df['Low'].rolling(lb).min().values

    

    sig = np.zeros(len(df))

    upper_touch = (df['High'].values >= b_up) & v_spike

    sig[(upper_touch) & (u_wick > body * switch_th) & (rsi > rsi_up)] = -1 

    sig[(upper_touch) & (u_wick <= body * switch_th)] = 1                

    

    lower_touch = (df['Low'].values <= b_lo) & v_spike

    sig[(lower_touch) & (l_wick > body * switch_th) & (rsi < rsi_lo)] = 1  

    sig[(lower_touch) & (l_wick <= body * switch_th)] = -1               



    pos = pd.Series(sig).replace(0, np.nan).ffill().fillna(0).values

    ret = pos[:-1] * close_pct[1:]

    cum_ret = np.cumprod(1 + np.nan_to_num(ret))

    if len(cum_ret) == 0: return -1, 0, 0

    

    final_ret = cum_ret[-1] - 1

    max_dd = (cum_ret / np.maximum.accumulate(cum_ret) - 1).min()

    trades = np.sum(np.abs(np.diff(sig))) / 2

    return final_ret, max_dd, trades



def run_ultra_resumable(interval):

    backup_file = f"progress_backup_{interval}.csv"

    df_raw = get_max_data("1570.T", interval)

    if df_raw is None: return

    

    delta = df_raw['Close'].diff()

    df_raw['RSI'] = 100 - (100 / (1 + (delta.where(delta > 0, 0).rolling(14).mean() / -delta.where(delta < 0, 0).rolling(14).mean())))



    params = {

        'rsi_up': range(70, 91, 1),

        'rsi_lo': range(10, 31, 1),

        'vol_m': [1.2, 1.5, 1.8, 2.0, 2.3, 2.5, 3.0],

        'lookback': range(3, 101, 2),

        'switch_th': [0.3, 0.5, 0.8, 1.0, 1.2, 1.5, 2.0]

    }

    

    combos = list(product(*params.values()))

    total = len(combos)

    

    # 暫定ベスト記録用

    best_ret = -999.0

    best_info = {"ret": 0, "dd": 0, "trd": 0, "params": ""}



    if os.path.exists(backup_file):

        results_df = pd.read_csv(backup_file)

        processed_count = len(results_df)

        results = results_df.values.tolist()

        if not results_df.empty:

            top = results_df.sort_values('return', ascending=False).iloc[0]

            best_ret = top['return']

            best_info = {

                "ret": top['return'], "dd": top['max_dd'], "trd": top['trades'],

                "params": f"UP:{int(top['rsi_up'])} LO:{int(top['rsi_lo'])} V:{top['vol_m']} Lb:{int(top['lookback'])} SW:{top['switch_th']}"

            }

        print(f"--- 再開: {processed_count:,}件完了済み ---")

    else:

        results = []

        processed_count = 0



    print(f"全 {total:,} 通りの検証を開始...")

    start_time = time.time()



    for i in range(processed_count, total):

        c = combos[i]

        ret, dd, trd = backtest_hybrid(df_raw, c[0], c[1], c[2], c[3], c[4])

        results.append((*c, ret, dd, trd))



        # 暫定ベストの更新 (取引回数10回以上を条件)

        if ret > best_ret and trd >= 10:

            best_ret = ret

            best_info = {

                "ret": ret, "dd": dd, "trd": trd,

                "params": f"UP:{c[0]} LO:{c[1]} V:{c[2]} Lb:{c[3]} SW:{c[4]}"

            }



        # 100件ごとに表示を「上書き」更新

        if (i + 1) % 100 == 0 or (i + 1) == total:

            elapsed = time.time() - start_time

            # 1行で全ての主要指標を表示

            print(f"[{interval}] {(i+1)/total*100:5.2f}% | "

                  f"最高益:{best_info['ret']*100:6.1f}% | "

                  f"DD:{best_info['dd']*100:5.1f}% | "

                  f"取引:{int(best_info['trd']):3d}回 | "

                  f"設定:{best_info['params']}", end="\r")

            

        # 2000件ごとにバックアップ保存

        if (i + 1) % 2000 == 0:

            pd.DataFrame(results, columns=list(params.keys()) + ['return', 'max_dd', 'trades']).to_csv(backup_file, index=False)



    print(f"\n--- 【{interval}】完了。結果を保存しました。 ---")



if __name__ == "__main__":

    for tf in ["15m", "60m"]:

        run_ultra_resumable(tf)