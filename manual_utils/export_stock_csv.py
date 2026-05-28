"""
One-time script: export StockDaily table to per-symbol CSV files.

Run from the cda repo root:
    python manual_utils/export_stock_csv.py

Output: assets/data/stocks/{SYMBOL}.csv  (^ removed from filename)
Reads symbol list from config/symbols.json.
"""
import json
import os
import utils as ut


QRY = """
    SELECT
        CAST([Date] AS DATE)          AS date,
        [Open_Price_USD]              AS open_price_usd,
        [Close_Price_USD]             AS close_price_usd,
        [Adj_Close_Price_USD]         AS adj_close_price_usd,
        [Volume]                      AS total_volume_usd
    FROM [cda].[dbo].[StockDaily]
    WHERE [Symbol] = '{symbol}'
    ORDER BY [Date] ASC
"""


def export_symbol_csv(symbol: str, output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)
    df = ut.query_db(QRY.format(symbol=symbol))
    filename = symbol.replace('^', '') + '.csv'
    df.to_csv(os.path.join(output_dir, filename), index=False)
    print(f'Exported: {filename} ({len(df)} rows)')


if __name__ == '__main__':
    with open('config/symbols.json') as f:
        cfg = json.load(f)

    output_dir = cfg.get('csv_output_dir', 'assets/data/stocks')
    for symbol in cfg['stocks']:
        export_symbol_csv(symbol, output_dir)
