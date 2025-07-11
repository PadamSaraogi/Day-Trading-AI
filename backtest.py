import pandas as pd
import numpy as np

def run_backtest_simulation(df, trail_mult=2.0, time_limit=16, adx_target_mult=2.5):
    trades = []
    in_trade = False
    cooldown = 0
    COOLDOWN_BARS = 2
    STOP_MULT = 1.0
    entry_sig = 0

    for i in range(1, len(df)):
        if cooldown > 0:
            cooldown -= 1
            continue

        sig = df['signal'].iat[i]
        price = df['close'].iat[i]
        atr = df['ATR'].iat[i]
        adx = df['ADX14'].iat[i]

        if not in_trade and sig != 0:
            entry_price = price
            entry_sig = sig
            stop_price = entry_price - STOP_MULT * atr * entry_sig
            tp_half = entry_price + 1.0 * atr * entry_sig

            if adx < 20:
                target_mult = 2.0
            elif adx < 30:
                target_mult = 2.5
            else:
                target_mult = adx_target_mult

            tp_full = entry_price + target_mult * atr * entry_sig
            trail_price = entry_price
            in_trade = True
            entry_idx = i
            half_closed = False
            continue

        if in_trade:
            duration = i - entry_idx
            price_now = price
            atr_now = atr

            if entry_sig > 0:
                trail_price = max(trail_price, price_now)
                trailing_stop = trail_price - trail_mult * atr_now
            else:
                trail_price = min(trail_price, price_now)
                trailing_stop = trail_price + trail_mult * atr_now

            if not half_closed:
                if (entry_sig > 0 and price_now >= tp_half) or (entry_sig < 0 and price_now <= tp_half):
                    pnl_half = 0.5 * (price_now - entry_price) * entry_sig
                    trades.append({
                        'entry_time': df.index[entry_idx],
                        'exit_time': df.index[i],
                        'entry_price': entry_price,
                        'exit_price': price_now,
                        'pnl': pnl_half
                    })
                    half_closed = True
                    continue

            should_exit = (
                (entry_sig > 0 and (price_now <= stop_price or price_now >= tp_full or price_now <= trailing_stop)) or
                (entry_sig < 0 and (price_now >= stop_price or price_now <= tp_full or price_now >= trailing_stop)) or
                duration >= time_limit
            )

            if should_exit:
                pnl_full = 0.5 * (price_now - entry_price) * entry_sig
                trades.append({
                    'entry_time': df.index[entry_idx],
                    'exit_time': df.index[i],
                    'entry_price': entry_price,
                    'exit_price': price_now,
                    'pnl': pnl_full
                })
                in_trade = False
                cooldown = COOLDOWN_BARS

    return trades
