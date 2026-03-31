# modules/cmtk_converter.py
import pandas as pd
import os
from modules.utils import get_app_data_path
from datetime import datetime

def convert_cmtk_to_d055(pressure_path, flow_path, temp_path=None):
    # FIX: Use AppData instead of a local directory
    output_dir = os.path.join(get_app_data_path(), "conversions")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    df_p = pd.read_csv(pressure_path)
    df_f = pd.read_csv(flow_path)
    
    df_p['pressure'] = df_p.iloc[:, 1].astype(str).str.extract(r'([-]?\d+[\.,]?\d*)')[0].str.replace(',', '.').astype(float)
    df_f['flow'] = df_f.iloc[:, 1].astype(str).str.extract(r'([-]?\d+[\.,]?\d*)')[0].str.replace(',', '.').astype(float)

    merged = pd.merge(df_p[['Time', 'pressure']], df_f[['Time', 'flow']], on='Time', how='inner')

    # Base columns
    final_cols = {
        'Data': 'D#' + pd.to_datetime(merged['Time']).dt.strftime('%Y-%m-%d'),
        'Time': 'TOD#' + pd.to_datetime(merged['Time']).dt.strftime('%H:%M:%S') + '.000',
        'Pressure Base [kPa]': merged['pressure'],
        'Flow Base [Nl/min]': merged['flow']
    }

    # Add optional temperature column
    if temp_path and os.path.exists(temp_path):
        df_t = pd.read_csv(temp_path)
        df_t['temp'] = df_t.iloc[:, 1].astype(str).str.extract(r'([-]?\d+[\.,]?\d*)')[0].str.replace(',', '.').astype(float)
        merged = pd.merge(merged, df_t[['Time', 'temp']], on='Time', how='left')
        final_cols['Fluid Temperature [°C]'] = merged['temp']

    final_df = pd.DataFrame(final_cols)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"CMTK_Unified_{timestamp}.csv")
    final_df.to_csv(output_path, sep=';', index=False)
    
    return output_path