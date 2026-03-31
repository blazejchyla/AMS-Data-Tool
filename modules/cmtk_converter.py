# modules/cmtk_converter.py
import pandas as pd
import os
from datetime import datetime

def convert_cmtk_to_d055(pressure_path, flow_path, temp_path=None, output_dir="conversion_output"):
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 1. Load DataFrames
    df_p = pd.read_csv(pressure_path)
    df_f = pd.read_csv(flow_path)
    
    # 2. Clean Units and Headers
    # Strip " kPa", " L/min", etc., and convert to numeric
    def clean_val(val):
        if isinstance(val, str):
            return float(val.split(' ')[0].replace(',', '.'))
        return val

    # Extract raw values from the second column (skipping the "Time" column)
    df_p['pressure'] = df_p.iloc[:, 1].apply(clean_val)
    df_f['flow'] = df_f.iloc[:, 1].apply(clean_val)

    # 3. Merge on Time
    merged = pd.merge(df_p[['Time', 'pressure']], df_f[['Time', 'flow']], on='Time', how='inner')

    if temp_path and os.path.exists(temp_path):
        df_t = pd.read_csv(temp_path)
        df_t['temp'] = df_t.iloc[:, 1].apply(clean_val)
        merged = pd.merge(merged, df_t[['Time', 'temp']], on='Time', how='left')
    else:
        merged['temp'] = None

    # 4. Reformat Timestamps for D055 format [cite: 4]
    # Source: 2026-01-26 12:14:36 -> Target: D#2026-01-26 and TOD#12:14:36.000
    def format_date(ts_str):
        dt = pd.to_datetime(ts_str)
        return f"D#{dt.strftime('%Y-%m-%d')}"

    def format_time(ts_str):
        dt = pd.to_datetime(ts_str)
        return f"TOD#{dt.strftime('%H:%M:%S')}.000"

    merged['Data'] = merged['Time'].apply(format_date)
    merged['Time_Formatted'] = merged['Time'].apply(format_time)

    # 5. Build Final DataFrame matching target.csv columns [cite: 4]
    final_df = pd.DataFrame({
        'Data': merged['Data'],
        'Time': merged['Time_Formatted'],
        'Pressure Base [kPa]': merged['pressure'],
        'Flow Base [Nl/min]': merged['flow'],
        'Fluid Temperature [°C]': merged['temp'], # New dynamic column
        'ITV Pressure [kPa]': 0,
        'Pressure Remote [kPa]': 0,
        'Flow Remote [Nl/min]': 0,
        'Accumulated flow Base [l]': 0,
        'Accumulated flow Remote [l]': 0,
        'AMS Mode': 'Operating'
    })

    # 6. Save to CSV with semicolon delimiter [cite: 4]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"CMTK_Unified_{timestamp}.csv")
    final_df.to_csv(output_path, sep=';', index=False)
    
    return output_path