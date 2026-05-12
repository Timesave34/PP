import pandas as pd
# ------------------------------------------------
# LOAD INPUT file values
# if running on pc "C:\Users\ianbe\PyPen1\pension_inputs.xlsm"
# if running via github "./pension_inputs.xlsm"
# ------------------------------------------------
#EXCEL_PATH=r"C:\Users\ianbe\PyPen1\pension_inputs.xlsm"
EXCEL_PATH = "./inputs.xlsm"

def load_inputs():
    df = pd.read_excel(
        EXCEL_PATH,
        sheet_name="Inputs"
    )
    vals = {}
    for _, row in df.iterrows():

        label = str(row["Label"]).strip()
        vals[label] = row["Data"]
    return vals
