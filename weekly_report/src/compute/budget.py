"""Synchronous computation functions for budget data (reused by CLI and API)."""

import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from loguru import logger
from weekly_report.src.config import load_config
from weekly_report.src.adapters.budget import load_data as load_budget_data
from weekly_report.src.adapters.qlik import load_data as load_qlik_data


def _parse_number(val) -> float:
    """Parse numeric value from string, handling commas, spaces, %, negatives."""
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        if pd.isna(val) or val == float('inf') or val == float('-inf'):
            return 0.0
        return float(val)
    if not isinstance(val, str):
        return 0.0
    s = str(val).strip().replace(' ', '').replace(',', '')
    if s.startswith('(') and s.endswith(')'):
        s = '-' + s[1:-1]
    if s.endswith('%'):
        s = s[:-1]
    try:
        return float(s)
    except:
        return 0.0


def compute_budget_general(base_week: str) -> Dict[str, Any]:
    """Compute Budget General data (sync version of API endpoint)."""
    config = load_config(week=base_week)
    # Note: load_budget_data will check Supabase first, then fallback to local
    # It may raise FileNotFoundError if neither exists
    try:
        df = load_budget_data(config.raw_data_path, base_week=base_week)
    except FileNotFoundError as e:
        # If budget file doesn't exist in Supabase or locally, return error
        return {"error": f"No budget data available: {str(e)}"}
    
    if df.empty:
        return {"error": "Budget file is empty"}
    
    df.columns = df.columns.str.strip()
    if "Month" in df.columns:
        df["Month"] = df["Month"].astype(str).str.strip()
    if "Market" in df.columns:
        df["Market"] = df["Market"].astype(str).str.strip()
    
    # Exclude pre-aggregated totals
    if "Market" in df.columns:
        total_aliases = {"total", "all", "all markets", "grand total", "totals"}
        df = df[~df["Market"].str.lower().isin(total_aliases)]
        df = df[df["Market"].str.len() > 0]
    
    dimension_cols = {"Month", "Market", "_source_file", "_source_type"}
    value_df = df.drop(columns=[c for c in dimension_cols if c in df.columns], errors='ignore').copy()
    for col in value_df.columns:
        value_df[col] = value_df[col].map(_parse_number)
    
    # Derive Gross Revenue
    def derive_gross(df_in: pd.DataFrame, net_col: str, returns_col: str, gross_col: str) -> None:
        if net_col in df_in.columns and returns_col in df_in.columns:
            try:
                df_in[gross_col] = df_in[net_col] - df_in[returns_col]
            except Exception:
                pass
    derive_gross(value_df, 'Returning Net Revenue', 'Returning Returns', 'Returning Gross Revenue')
    derive_gross(value_df, 'New Net Revenue', 'New Returns', 'New Gross Revenue')
    
    if "Month" not in df.columns:
        return {"error": "Budget file missing 'Month' column"}
    
    df_grouped = pd.concat([df[["Month"]], value_df], axis=1).groupby("Month", as_index=False).sum(numeric_only=True)
    
    try:
        df_grouped["__month_dt"] = pd.to_datetime(df_grouped["Month"], format="%B %Y", errors="coerce")
    except Exception:
        df_grouped["__month_dt"] = pd.to_datetime(df_grouped["Month"], errors="coerce")
    df_grouped = df_grouped.sort_values(["__month_dt", "Month"], ascending=[True, True]).drop(columns=["__month_dt"])
    
    months_order = df_grouped["Month"].tolist()
    
    now = datetime.now()
    def parse_month_str(m: str):
        try:
            return datetime.strptime(m, "%B %Y")
        except Exception:
            try:
                return datetime.fromisoformat(m)
            except Exception:
                return None
    month_parsed = {m: parse_month_str(m) for m in months_order}
    
    all_numeric_cols = [c for c in df_grouped.columns if c != "Month"]
    whitelist = [
        'Returning Customers', 'Share of Returning Customers', 'Returning Gross Revenue', 'Returning Returns',
        'Returning Net Revenue', 'Returning Cost of Goods Sold', 'Returning Orders', 'Returning Order Frequency',
        'Returning AOV', 'Returning Revenue per Customer',
        'New Customers', 'Share of New Customers', 'New Gross Revenue', 'New Returns', 'New Net Revenue',
        'New Cost of Goods Sold', 'New Orders', 'New Order Frequency', 'New AOV', 'New Revenue per Customer',
        'Total Customers', 'Total Orders', 'Total AOV', 'Revenue per Customer', 'Order Frequency', 'Total Gross Revenue',
    ]
    metric_cols = [c for c in whitelist if c in all_numeric_cols]
    
    desired_order = [
        "Returning Customers", "Share of Returning Customers", "Returning Gross Revenue", "Returning Returns",
        "Returning Net Revenue", "Returning Cost of Goods Sold", "Returning Orders", "Returning Order Frequency",
        "Returning AOV", "Returning Revenue per Customer",
        "New Customers", "Share of New Customers", "New Gross Revenue", "New Returns", "New Net Revenue",
        "New Cost of Goods Sold", "New Orders", "New Order Frequency", "New AOV", "New Revenue per Customer",
    ]
    priority_index = {name.lower(): i for i, name in enumerate(desired_order)}
    def metric_key(name: str):
        idx = priority_index.get(name.lower())
        return (0, idx) if idx is not None else (1, name.lower())
    metric_cols = sorted(metric_cols, key=metric_key)
    
    table = {}
    totals = {}
    ytd_totals = {}
    customer_by_metric = {}
    display_name_by_metric = {}
    
    for metric in metric_cols:
        metric_lower = metric.lower()
        if metric_lower.startswith('new '):
            customer_by_metric[metric] = 'New'
        elif metric_lower.startswith('returning '):
            customer_by_metric[metric] = 'Returning'
        else:
            customer_by_metric[metric] = ''
        
        if metric_lower.startswith('share of returning customers'):
            display_name_by_metric[metric] = 'Share of total %'
            customer_by_metric[metric] = 'Returning'
        elif metric_lower.startswith('share of new customers'):
            display_name_by_metric[metric] = 'Share of total %'
            customer_by_metric[metric] = 'New'
        else:
            display_name_by_metric[metric] = metric
        
        by_month = {}
        total_val = 0.0
        for _, row in df_grouped.iterrows():
            m = row["Month"]
            val = float(row[metric]) if pd.notna(row[metric]) else 0.0
            if val == float('inf') or val == float('-inf'):
                val = 0.0
            by_month[m] = val
            total_val += val
        table[metric] = by_month
        totals[metric] = total_val
        
        ytd_val = 0.0
        for m, v in by_month.items():
            mp = month_parsed.get(m)
            if mp is not None and (mp.year < now.year or (mp.year == now.year and mp.month <= now.month)):
                ytd_val += v
        ytd_totals[metric] = ytd_val
    
    return {
        "week": base_week,
        "months": months_order,
        "metrics": metric_cols,
        "table": table,
        "totals": totals,
        "ytd_totals": ytd_totals,
        "customer_by_metric": customer_by_metric,
        "display_name_by_metric": display_name_by_metric,
    }


def compute_actuals_general(base_week: str) -> Dict[str, Any]:
    """Compute Actuals General data from Qlik (sync version of API endpoint)."""
    config = load_config(week=base_week)
    
    # config.raw_data_path is data/raw/{week} - adapter expects this and adds /qlik itself
    week_data_path = config.raw_data_path  # data/raw/{week}
    df = load_qlik_data(week_data_path)
    if df is None or len(df) == 0:
        return {"error": "No actuals data available"}
    
    df.columns = df.columns.str.strip()
    
    # Check if this is raw transaction data (needs aggregation) or pre-aggregated
    is_raw_data = "Date" in df.columns and "Customer E-mail" in df.columns
    
    if is_raw_data:
        # This is raw Qlik transaction data - need to aggregate per month
        logger.info("Aggregating raw Qlik transaction data per month")
        
        # Filter for Online sales only
        if "Sales Channel" in df.columns:
            df = df[df["Sales Channel"] == "Online"].copy()
            logger.info(f"Filtered to Online sales: {len(df)} rows")
        
        # Transform Date to Month
        if "Date" not in df.columns:
            return {"error": "Raw Qlik data missing 'Date' column"}
        
        try:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df = df[df["Date"].notna()]  # Remove rows where date parsing failed
            
            # Create Month column in format "Month Year" (e.g., "October 2025")
            df["Month"] = df["Date"].dt.strftime("%B %Y")
            logger.info(f"Transformed Date to Month: {df['Month'].unique()[:5]}")
        except Exception as e:
            logger.error(f"Failed to transform Date to Month: {e}")
            return {"error": f"Failed to transform Date column to Month format: {str(e)}"}
        
        # Map Country to Market (if Market column doesn't exist)
        if "Market" not in df.columns and "Country" in df.columns:
            df["Market"] = df["Country"]
            logger.info(f"Mapped Country to Market")
        
        # Ensure numeric columns
        numeric_cols = ["Gross Revenue", "Net Revenue", "Returns", "Sales Qty"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        
        # Aggregate by Month and Customer Type
        agg_dict = {
            "Gross Revenue": "sum",
            "Net Revenue": "sum",
            "Returns": "sum",
        }
        
        # Count unique customers and orders
        if "Customer E-mail" in df.columns:
            agg_dict["Customer E-mail"] = "nunique"
        if "Order No" in df.columns:
            agg_dict["Order No"] = "nunique"
        
        # Separate New and Returning customers
        new_df = df[df["New/Returning Customer"] == "New"].copy() if "New/Returning Customer" in df.columns else pd.DataFrame()
        returning_df = df[df["New/Returning Customer"] == "Returning"].copy() if "New/Returning Customer" in df.columns else pd.DataFrame()
        
        # Aggregate New customers
        new_agg = {}
        if not new_df.empty and len(new_df) > 0:
            new_grouped = new_df.groupby("Month", as_index=False).agg(agg_dict)
            for _, row in new_grouped.iterrows():
                month = row["Month"]
                new_agg[month] = {
                    "New Gross Revenue": float(row.get("Gross Revenue", 0)),
                    "New Net Revenue": float(row.get("Net Revenue", 0)),
                    "New Returns": float(row.get("Returns", 0)),
                    "New Customers": int(row.get("Customer E-mail", 0)),
                    "New Orders": int(row.get("Order No", 0)),
                }
        
        # Aggregate Returning customers
        returning_agg = {}
        if not returning_df.empty and len(returning_df) > 0:
            returning_grouped = returning_df.groupby("Month", as_index=False).agg(agg_dict)
            for _, row in returning_grouped.iterrows():
                month = row["Month"]
                returning_agg[month] = {
                    "Returning Gross Revenue": float(row.get("Gross Revenue", 0)),
                    "Returning Net Revenue": float(row.get("Net Revenue", 0)),
                    "Returning Returns": float(row.get("Returns", 0)),
                    "Returning Customers": int(row.get("Customer E-mail", 0)),
                    "Returning Orders": int(row.get("Order No", 0)),
                }
        
        # Combine into a single aggregated dataframe
        all_months = sorted(set(list(new_agg.keys()) + list(returning_agg.keys())))
        
        rows = []
        for month in all_months:
            row = {"Month": month}
            if month in new_agg:
                row.update(new_agg[month])
            else:
                row.update({
                    "New Gross Revenue": 0, "New Net Revenue": 0, "New Returns": 0,
                    "New Customers": 0, "New Orders": 0
                })
            
            if month in returning_agg:
                row.update(returning_agg[month])
            else:
                row.update({
                    "Returning Gross Revenue": 0, "Returning Net Revenue": 0, "Returning Returns": 0,
                    "Returning Customers": 0, "Returning Orders": 0
                })
            rows.append(row)
        
        df = pd.DataFrame(rows)
        logger.info(f"Aggregated to {len(df)} months: {df['Month'].tolist()[:5]}")
    
    else:
        # Pre-aggregated data - check for Month column
        if "Month" not in df.columns:
            return {"error": "Actuals missing 'Month' column and not raw transaction data"}
        
        df["Month"] = df["Month"].astype(str).str.strip()
        if "Market" in df.columns:
            df["Market"] = df["Market"].astype(str).str.strip()
        
        # Exclude pre-aggregated totals
        if "Market" in df.columns:
            total_aliases = {"total", "all", "all markets", "grand total", "totals"}
            df = df[~df["Market"].str.lower().isin(total_aliases)]
            df = df[df["Market"].str.len() > 0]
    
    df["Month"] = df["Month"].astype(str).str.strip()
    
    # Ensure all required columns exist (set to 0 if missing)
    required_cols = [
        "New Gross Revenue", "New Net Revenue", "New Returns", "New Customers", "New Orders",
        "Returning Gross Revenue", "Returning Net Revenue", "Returning Returns", "Returning Customers", "Returning Orders"
    ]
    for col in required_cols:
        if col not in df.columns:
            df[col] = 0
    
    # Numeric coercion
    dimension_cols = {"Month", "Market", "_source_file", "_source_type"}
    keep_cols = [c for c in df.columns if c not in dimension_cols]
    value_df = df[keep_cols].copy()
    for col in value_df.columns:
        if col in df.columns:
            value_df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    
    # Derive gross and other metrics (same as API)
    def derive_gross(df_in: pd.DataFrame, net_col: str, returns_col: str, gross_col: str) -> None:
        if net_col in df_in.columns and returns_col in df_in.columns:
            try:
                df_in[gross_col] = df_in[net_col] - df_in[returns_col]
            except Exception:
                pass
    derive_gross(value_df, 'Returning Net Revenue', 'Returning Returns', 'Returning Gross Revenue')
    derive_gross(value_df, 'New Net Revenue', 'New Returns', 'New Gross Revenue')
    if 'Total Net Revenue' in value_df.columns and ('Returns' in value_df.columns or 'Total Returns' in value_df.columns):
        ret_col = 'Returns' if 'Returns' in value_df.columns else 'Total Returns'
        try:
            value_df['Total Gross Revenue'] = value_df['Total Net Revenue'] - value_df[ret_col]
        except Exception:
            pass
    
    # Fill totals
    if 'Total Customers' not in value_df.columns and {'Returning Customers','New Customers'}.issubset(set(value_df.columns)):
        value_df['Total Customers'] = (value_df['Returning Customers'].fillna(0) + value_df['New Customers'].fillna(0))
    if 'Total Orders' not in value_df.columns and {'Returning Orders','New Orders'}.issubset(set(value_df.columns)):
        value_df['Total Orders'] = (value_df['Returning Orders'].fillna(0) + value_df['New Orders'].fillna(0))
    if 'Total Net Revenue' not in value_df.columns and {'Returning Net Revenue','New Net Revenue'}.issubset(set(value_df.columns)):
        value_df['Total Net Revenue'] = (value_df['Returning Net Revenue'].fillna(0) + value_df['New Net Revenue'].fillna(0))
    if 'Total Gross Revenue' not in value_df.columns and {'Returning Gross Revenue','New Gross Revenue'}.issubset(set(value_df.columns)):
        value_df['Total Gross Revenue'] = (value_df['Returning Gross Revenue'].fillna(0) + value_df['New Gross Revenue'].fillna(0))
    
    # Ratios
    def safe_div(a, b):
        try:
            res = a / b
            if res == float('inf') or res == float('-inf'):
                return 0.0
            return res
        except Exception:
            return 0.0
    
    if {'Returning Gross Revenue','Returning Orders'}.issubset(set(value_df.columns)):
        value_df['Returning AOV'] = value_df.apply(lambda r: safe_div(r.get('Returning Gross Revenue', 0.0), r.get('Returning Orders', 0.0)), axis=1)
    if {'New Gross Revenue','New Orders'}.issubset(set(value_df.columns)):
        value_df['New AOV'] = value_df.apply(lambda r: safe_div(r.get('New Gross Revenue', 0.0), r.get('New Orders', 0.0)), axis=1)
    if {'Total Gross Revenue','Total Orders'}.issubset(set(value_df.columns)):
        value_df['Total AOV'] = value_df.apply(lambda r: safe_div(r.get('Total Gross Revenue', 0.0), r.get('Total Orders', 0.0)), axis=1)
    
    if {'Returning Net Revenue','Returning Customers'}.issubset(set(value_df.columns)):
        value_df['Returning Revenue per Customer'] = value_df.apply(lambda r: safe_div(r.get('Returning Net Revenue', 0.0), r.get('Returning Customers', 0.0)), axis=1)
    if {'New Net Revenue','New Customers'}.issubset(set(value_df.columns)):
        value_df['New Revenue per Customer'] = value_df.apply(lambda r: safe_div(r.get('New Net Revenue', 0.0), r.get('New Customers', 0.0)), axis=1)
    if {'Total Net Revenue','Total Customers'}.issubset(set(value_df.columns)):
        value_df['Revenue per Customer'] = value_df.apply(lambda r: safe_div(r.get('Total Net Revenue', 0.0), r.get('Total Customers', 0.0)), axis=1)
    
    if {'Returning Orders','Returning Customers'}.issubset(set(value_df.columns)):
        value_df['Returning Order Frequency'] = value_df.apply(lambda r: safe_div(r.get('Returning Orders', 0.0), r.get('Returning Customers', 0.0)), axis=1)
    if {'New Orders','New Customers'}.issubset(set(value_df.columns)):
        value_df['New Order Frequency'] = value_df.apply(lambda r: safe_div(r.get('New Orders', 0.0), r.get('New Customers', 0.0)), axis=1)
    if {'Total Orders','Total Customers'}.issubset(set(value_df.columns)):
        value_df['Order Frequency'] = value_df.apply(lambda r: safe_div(r.get('Total Orders', 0.0), r.get('Total Customers', 0.0)), axis=1)
    
    if {'New Customers','Total Customers'}.issubset(set(value_df.columns)):
        value_df['Share of New Customers'] = value_df.apply(lambda r: safe_div(r.get('New Customers', 0.0), r.get('Total Customers', 0.0)) * 100.0, axis=1)
    if {'Returning Customers','Total Customers'}.issubset(set(value_df.columns)):
        value_df['Share of Returning Customers'] = value_df.apply(lambda r: safe_div(r.get('Returning Customers', 0.0), r.get('Total Customers', 0.0)) * 100.0, axis=1)
    
    grouped = pd.concat([df[["Month"]], value_df], axis=1).groupby("Month", as_index=False).sum(numeric_only=True)
    try:
        grouped["__dt"] = pd.to_datetime(grouped["Month"], format="%B %Y", errors="coerce")
    except Exception:
        grouped["__dt"] = pd.to_datetime(grouped["Month"], errors="coerce")
    grouped = grouped.sort_values(["__dt", "Month"]).drop(columns=["__dt"])
    months_order = grouped["Month"].tolist()
    
    all_numeric = [c for c in grouped.columns if c != "Month"]
    whitelist = [
        'Returning Customers', 'Share of Returning Customers', 'Returning Gross Revenue', 'Returning Returns',
        'Returning Net Revenue', 'Returning Cost of Goods Sold', 'Returning Orders', 'Returning Order Frequency',
        'Returning AOV', 'Returning Revenue per Customer',
        'New Customers', 'Share of New Customers', 'New Gross Revenue', 'New Returns', 'New Net Revenue',
        'New Cost of Goods Sold', 'New Orders', 'New Order Frequency', 'New AOV', 'New Revenue per Customer',
        'Total Customers', 'Total Orders', 'Total AOV', 'Revenue per Customer', 'Order Frequency', 'Total Gross Revenue',
        'Total Net Revenue', 'Returns', 'Total Returns', 'GMV', 'Online Marketing Spend', 'Unique visitors',
        'Conversion', 'Payment Fees', 'Pick Pack', 'Freight', 'Distribution Costs', 'VAT Factor%', 'Shipping Revenue',
        'CONTRIBUTION', 'COS %'
    ]
    metric_cols = [c for c in whitelist if c in all_numeric]
    
    desired_order = [
        "Returning Customers","Share of Returning Customers","Returning Gross Revenue","Returning Returns","Returning Net Revenue","Returning Cost of Goods Sold","Returning Orders","Returning Order Frequency","Returning AOV","Returning Revenue per Customer",
        "New Customers","Share of New Customers","New Gross Revenue","New Returns","New Net Revenue","New Cost of Goods Sold","New Orders","New Order Frequency","New AOV","New Revenue per Customer",
    ]
    priority_index = {name.lower(): i for i, name in enumerate(desired_order)}
    metric_cols = sorted(metric_cols, key=lambda n: (0, priority_index.get(n.lower())) if n.lower() in priority_index else (1, n.lower()))
    
    table, totals, ytd_totals = {}, {}, {}
    now = datetime.now()
    def parse_month(m: str):
        try:
            return datetime.strptime(m, "%B %Y")
        except Exception:
            return None
    
    customer_by_metric = {}
    display_name_by_metric = {}
    for metric in metric_cols:
        metric_lower = metric.lower()
        if metric_lower.startswith('new '):
            customer_by_metric[metric] = 'New'
        elif metric_lower.startswith('returning '):
            customer_by_metric[metric] = 'Returning'
        else:
            customer_by_metric[metric] = ''
        
        if metric_lower.startswith('share of returning customers'):
            display_name_by_metric[metric] = 'Share of total %'
            customer_by_metric[metric] = 'Returning'
        elif metric_lower.startswith('share of new customers'):
            display_name_by_metric[metric] = 'Share of total %'
            customer_by_metric[metric] = 'New'
        else:
            display_name_by_metric[metric] = metric
        
        by_month = {}
        total_val = 0.0
        for _, row in grouped.iterrows():
            m = row["Month"]
            v = float(row[metric]) if pd.notna(row[metric]) else 0.0
            if v == float('inf') or v == float('-inf'):
                v = 0.0
            by_month[m] = v
            total_val += v
        table[metric] = by_month
        totals[metric] = total_val
        
        month_parsed_local = {m: parse_month(m) for m in by_month.keys()}
        ytd_val = 0.0
        for m, v in by_month.items():
            mp = month_parsed_local.get(m)
            if mp is not None and (mp.year < now.year or (mp.year == now.year and mp.month <= now.month)):
                ytd_val += v
        ytd_totals[metric] = ytd_val
    
    return {
        "week": base_week,
        "months": months_order,
        "metrics": metric_cols,
        "table": table,
        "totals": totals,
        "ytd_totals": ytd_totals,
        "customer_by_metric": customer_by_metric,
        "display_name_by_metric": display_name_by_metric,
    }



def compute_actuals_markets_detailed(base_week: str) -> Dict[str, Any]:
    """Compute Actuals Markets Detailed data per Market and Month (sync version)."""
    config = load_config(week=base_week)
    df = load_qlik_data(config.raw_data_path)
    if df is None or len(df) == 0:
        return {"week": base_week, "months": [], "markets": [], "metrics": [], "table": {}, "totals": {}, "ytd_totals": {}}
    
    df.columns = df.columns.str.strip()
    
    # Check if this is raw transaction data (needs aggregation) or pre-aggregated
    is_raw_data = "Date" in df.columns and "Customer E-mail" in df.columns
    
    if is_raw_data:
        # This is raw Qlik transaction data - need to aggregate per month and market
        logger.info("Aggregating raw Qlik transaction data per month and market")
        
        # Filter for Online sales only
        if "Sales Channel" in df.columns:
            df = df[df["Sales Channel"] == "Online"].copy()
            logger.info(f"Filtered to Online sales: {len(df)} rows")
        
        # Transform Date to Month
        if "Date" not in df.columns:
            return {"error": "Raw Qlik data missing 'Date' column"}
        
        try:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df = df[df["Date"].notna()]  # Remove rows where date parsing failed
            
            # Create Month column in format "Month Year" (e.g., "October 2025")
            df["Month"] = df["Date"].dt.strftime("%B %Y")
            logger.info(f"Transformed Date to Month: {df['Month'].unique()[:5]}")
        except Exception as e:
            logger.error(f"Failed to transform Date to Month: {e}")
            return {"error": f"Failed to transform Date column to Month format: {str(e)}"}
        
        # Map Country to Market (if Market column doesn't exist)
        if "Market" not in df.columns and "Country" in df.columns:
            df["Market"] = df["Country"]
            logger.info(f"Mapped Country to Market")
        
        if "Market" not in df.columns:
            return {"error": "Actuals missing 'Market' column"}
        
        # Ensure numeric columns
        numeric_cols = ["Gross Revenue", "Net Revenue", "Returns", "Sales Qty"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        
        # Aggregate by Month, Market, and Customer Type
        agg_dict = {
            "Gross Revenue": "sum",
            "Net Revenue": "sum",
            "Returns": "sum",
        }
        
        # Count unique customers and orders
        if "Customer E-mail" in df.columns:
            agg_dict["Customer E-mail"] = "nunique"
        if "Order No" in df.columns:
            agg_dict["Order No"] = "nunique"
        
        # Separate New and Returning customers
        new_df = df[df["New/Returning Customer"] == "New"].copy() if "New/Returning Customer" in df.columns else pd.DataFrame()
        returning_df = df[df["New/Returning Customer"] == "Returning"].copy() if "New/Returning Customer" in df.columns else pd.DataFrame()
        
        # Aggregate New customers by Month and Market
        rows = []
        if not new_df.empty and len(new_df) > 0:
            new_grouped = new_df.groupby(["Month", "Market"], as_index=False).agg(agg_dict)
            for _, row in new_grouped.iterrows():
                rows.append({
                    "Month": row["Month"],
                    "Market": row["Market"],
                    "New Gross Revenue": float(row.get("Gross Revenue", 0)),
                    "New Net Revenue": float(row.get("Net Revenue", 0)),
                    "New Returns": float(row.get("Returns", 0)),
                    "New Customers": int(row.get("Customer E-mail", 0)),
                    "New Orders": int(row.get("Order No", 0)),
                })
        
        # Aggregate Returning customers by Month and Market
        if not returning_df.empty and len(returning_df) > 0:
            returning_grouped = returning_df.groupby(["Month", "Market"], as_index=False).agg(agg_dict)
            for _, row in returning_grouped.iterrows():
                month = row["Month"]
                market = row["Market"]
                # Find or create row for this month+market
                existing = next((r for r in rows if r["Month"] == month and r["Market"] == market), None)
                if existing:
                    existing["Returning Gross Revenue"] = float(row.get("Gross Revenue", 0))
                    existing["Returning Net Revenue"] = float(row.get("Net Revenue", 0))
                    existing["Returning Returns"] = float(row.get("Returns", 0))
                    existing["Returning Customers"] = int(row.get("Customer E-mail", 0))
                    existing["Returning Orders"] = int(row.get("Order No", 0))
                else:
                    rows.append({
                        "Month": month,
                        "Market": market,
                        "New Gross Revenue": 0,
                        "New Net Revenue": 0,
                        "New Returns": 0,
                        "New Customers": 0,
                        "New Orders": 0,
                        "Returning Gross Revenue": float(row.get("Gross Revenue", 0)),
                        "Returning Net Revenue": float(row.get("Net Revenue", 0)),
                        "Returning Returns": float(row.get("Returns", 0)),
                        "Returning Customers": int(row.get("Customer E-mail", 0)),
                        "Returning Orders": int(row.get("Order No", 0)),
                    })
        
        # Fill missing values
        for row in rows:
            if "New Gross Revenue" not in row:
                row.update({"New Gross Revenue": 0, "New Net Revenue": 0, "New Returns": 0, "New Customers": 0, "New Orders": 0})
            if "Returning Gross Revenue" not in row:
                row.update({"Returning Gross Revenue": 0, "Returning Net Revenue": 0, "Returning Returns": 0, "Returning Customers": 0, "Returning Orders": 0})
        
        df = pd.DataFrame(rows)
        logger.info(f"Aggregated to {len(df)} month+market combinations: {df.groupby(['Month', 'Market']).size().sum()}")
    
    # Now check if we have Month and Market columns (after aggregation or if already present)
    if "Month" not in df.columns or "Market" not in df.columns:
        return {"error": "Actuals missing 'Month' or 'Market' column"}
    
    df["Month"] = df["Month"].astype(str).str.strip()
    df["Market"] = df["Market"].astype(str).str.strip()
    
    # Exclude pre-aggregated totals
    total_aliases = {"total", "all", "all markets", "grand total", "totals"}
    df = df[~df["Market"].str.lower().isin(total_aliases)]
    df = df[df["Market"].str.len() > 0]
    
    # Parse numbers
    dimension_cols = {"Month", "Market", "_source_file", "_source_type"}
    keep_cols = [c for c in df.columns if c not in dimension_cols]
    value_df = df[keep_cols].copy()
    for col in value_df.columns:
        value_df[col] = value_df[col].map(_parse_number)
    
    # Derivations (same as general)
    def derive_gross(df_in: pd.DataFrame, net_col: str, returns_col: str, gross_col: str) -> None:
        if net_col in df_in.columns and returns_col in df_in.columns:
            try:
                df_in[gross_col] = df_in[net_col] - df_in[returns_col]
            except Exception:
                pass
    derive_gross(value_df, 'Returning Net Revenue', 'Returning Returns', 'Returning Gross Revenue')
    derive_gross(value_df, 'New Net Revenue', 'New Returns', 'New Gross Revenue')
    if 'Total Net Revenue' in value_df.columns and ('Returns' in value_df.columns or 'Total Returns' in value_df.columns):
        ret_col = 'Returns' if 'Returns' in value_df.columns else 'Total Returns'
        try:
            value_df['Total Gross Revenue'] = value_df['Total Net Revenue'] - value_df[ret_col]
        except Exception:
            pass
    if 'Total Customers' not in value_df.columns and {'Returning Customers','New Customers'}.issubset(set(value_df.columns)):
        value_df['Total Customers'] = (value_df['Returning Customers'].fillna(0) + value_df['New Customers'].fillna(0))
    if 'Total Orders' not in value_df.columns and {'Returning Orders','New Orders'}.issubset(set(value_df.columns)):
        value_df['Total Orders'] = (value_df['Returning Orders'].fillna(0) + value_df['New Orders'].fillna(0))
    if 'Total Net Revenue' not in value_df.columns and {'Returning Net Revenue','New Net Revenue'}.issubset(set(value_df.columns)):
        value_df['Total Net Revenue'] = (value_df['Returning Net Revenue'].fillna(0) + value_df['New Net Revenue'].fillna(0))
    if 'Total Gross Revenue' not in value_df.columns and {'Returning Gross Revenue','New Gross Revenue'}.issubset(set(value_df.columns)):
        value_df['Total Gross Revenue'] = (value_df['Returning Gross Revenue'].fillna(0) + value_df['New Gross Revenue'].fillna(0))
    
    def safe_div(a, b):
        try:
            res = a / b
            if res == float('inf') or res == float('-inf'):
                return 0.0
            return res
        except Exception:
            return 0.0
    
    if {'Returning Gross Revenue','Returning Orders'}.issubset(set(value_df.columns)):
        value_df['Returning AOV'] = value_df.apply(lambda r: safe_div(r.get('Returning Gross Revenue', 0.0), r.get('Returning Orders', 0.0)), axis=1)
    if {'New Gross Revenue','New Orders'}.issubset(set(value_df.columns)):
        value_df['New AOV'] = value_df.apply(lambda r: safe_div(r.get('New Gross Revenue', 0.0), r.get('New Orders', 0.0)), axis=1)
    if {'Total Gross Revenue','Total Orders'}.issubset(set(value_df.columns)):
        value_df['Total AOV'] = value_df.apply(lambda r: safe_div(r.get('Total Gross Revenue', 0.0), r.get('Total Orders', 0.0)), axis=1)
    if {'Returning Net Revenue','Returning Customers'}.issubset(set(value_df.columns)):
        value_df['Returning Revenue per Customer'] = value_df.apply(lambda r: safe_div(r.get('Returning Net Revenue', 0.0), r.get('Returning Customers', 0.0)), axis=1)
    if {'New Net Revenue','New Customers'}.issubset(set(value_df.columns)):
        value_df['New Revenue per Customer'] = value_df.apply(lambda r: safe_div(r.get('New Net Revenue', 0.0), r.get('New Customers', 0.0)), axis=1)
    if {'Total Net Revenue','Total Customers'}.issubset(set(value_df.columns)):
        value_df['Revenue per Customer'] = value_df.apply(lambda r: safe_div(r.get('Total Net Revenue', 0.0), r.get('Total Customers', 0.0)), axis=1)
    if {'Returning Orders','Returning Customers'}.issubset(set(value_df.columns)):
        value_df['Returning Order Frequency'] = value_df.apply(lambda r: safe_div(r.get('Returning Orders', 0.0), r.get('Returning Customers', 0.0)), axis=1)
    if {'New Orders','New Customers'}.issubset(set(value_df.columns)):
        value_df['New Order Frequency'] = value_df.apply(lambda r: safe_div(r.get('New Orders', 0.0), r.get('New Customers', 0.0)), axis=1)
    if {'Total Orders','Total Customers'}.issubset(set(value_df.columns)):
        value_df['Order Frequency'] = value_df.apply(lambda r: safe_div(r.get('Total Orders', 0.0), r.get('Total Customers', 0.0)), axis=1)
    if {'New Customers','Total Customers'}.issubset(set(value_df.columns)):
        value_df['Share of New Customers'] = value_df.apply(lambda r: safe_div(r.get('New Customers', 0.0), r.get('Total Customers', 0.0)) * 100.0, axis=1)
    if {'Returning Customers','Total Customers'}.issubset(set(value_df.columns)):
        value_df['Share of Returning Customers'] = value_df.apply(lambda r: safe_div(r.get('Returning Customers', 0.0), r.get('Total Customers', 0.0)) * 100.0, axis=1)
    
    # Group by Market and Month
    grouped = pd.concat([df[["Market","Month"]], value_df], axis=1).groupby(["Market","Month"], as_index=False).sum(numeric_only=True)
    try:
        grouped["__dt"] = pd.to_datetime(grouped["Month"], format="%B %Y", errors="coerce")
    except Exception:
        grouped["__dt"] = pd.to_datetime(grouped["Month"], errors="coerce")
    grouped = grouped.sort_values(["Market","__dt","Month"]).drop(columns=["__dt"])
    
    markets = sorted(grouped["Market"].unique().tolist())
    months_order = sorted(grouped["Month"].unique().tolist())
    
    all_numeric = [c for c in grouped.columns if c not in {"Market","Month"}]
    whitelist = [
        'Returning Customers', 'Share of Returning Customers', 'Returning Gross Revenue', 'Returning Returns',
        'Returning Net Revenue', 'Returning Cost of Goods Sold', 'Returning Orders', 'Returning Order Frequency',
        'Returning AOV', 'Returning Revenue per Customer',
        'New Customers', 'Share of New Customers', 'New Gross Revenue', 'New Returns', 'New Net Revenue',
        'New Cost of Goods Sold', 'New Orders', 'New Order Frequency', 'New AOV', 'New Revenue per Customer',
        'Total Customers', 'Total Orders', 'Total AOV', 'Revenue per Customer', 'Order Frequency', 'Total Gross Revenue',
        'Total Net Revenue', 'Returns', 'Total Returns', 'GMV', 'Online Marketing Spend', 'Unique visitors',
        'Conversion', 'Payment Fees', 'Pick Pack', 'Freight', 'Distribution Costs', 'VAT Factor%', 'Shipping Revenue',
        'CONTRIBUTION', 'COS %'
    ]
    metrics = [c for c in whitelist if c in all_numeric]
    
    table = {}
    totals = {}
    ytd_totals = {}
    now = datetime.now()
    def parse_month(m: str):
        try:
            return datetime.strptime(m, "%B %Y")
        except Exception:
            return None
    
    for market in markets:
        mkt_df = grouped[grouped["Market"] == market]
        table_mkt = {}
        totals_mkt = {}
        ytd_mkt = {}
        month_parsed = {m: parse_month(m) for m in mkt_df["Month"].unique()}
        for metric in metrics:
            by_month = {}
            total_val = 0.0
            for _, row in mkt_df.iterrows():
                m = row["Month"]
                v = float(row[metric]) if pd.notna(row[metric]) else 0.0
                if v == float('inf') or v == float('-inf'):
                    v = 0.0
                by_month[m] = v
                total_val += v
            table_mkt[metric] = by_month
            totals_mkt[metric] = total_val
            ytd_val = 0.0
            for m, v in by_month.items():
                mp = month_parsed.get(m)
                if mp is not None and (mp.year < now.year or (mp.year == now.year and mp.month <= now.month)):
                    ytd_val += v
            ytd_mkt[metric] = ytd_val
        table[market] = table_mkt
        totals[market] = totals_mkt
        ytd_totals[market] = ytd_mkt
    
    return {
        "week": base_week,
        "months": months_order,
        "markets": markets,
        "metrics": metrics,
        "table": table,
        "totals": totals,
        "ytd_totals": ytd_totals,
    }
