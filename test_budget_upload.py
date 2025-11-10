"""Test script to verify budget file upload to Supabase"""
import sys
from pathlib import Path

sys.path.insert(0, '.')

from weekly_report.src.adapters.supabase_client import get_supabase_client

def test_budget_upload():
    """Test uploading a budget file to Supabase"""
    client = get_supabase_client()
    if not client:
        print("❌ Could not initialize Supabase client")
        return
    
    # Find a budget file
    budget_path = Path("data/raw/2025-42/budget")
    if not budget_path.exists():
        budget_path = Path("data/raw/budget")
    
    csv_files = list(budget_path.glob("*.csv")) if budget_path.exists() else []
    if not csv_files:
        print(f"⚠️ No budget CSV files found in {budget_path}")
        print("   Please upload a budget file first via the frontend")
        return
    
    budget_file = csv_files[0]
    print(f"📁 Found budget file: {budget_file}")
    
    # Read file content
    with open(budget_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    year = 2025  # Extract from filename or use default
    week = "2025-42"
    
    print(f"📦 Saving to Supabase: year={year}, week={week}, size={len(content)} chars")
    
    # Save to Supabase
    try:
        budget_data = {
            "year": year,
            "week": week,
            "filename": budget_file.name,
            "content": content
        }
        
        # Check if exists
        existing = client.table("budget_files").select("id").eq("year", year).limit(1).execute()
        
        if existing.data and len(existing.data) > 0:
            budget_id = existing.data[0]["id"]
            result = client.table("budget_files").update(budget_data).eq("id", budget_id).execute()
            print(f"✅ Updated existing budget file (id: {budget_id})")
        else:
            result = client.table("budget_files").insert(budget_data).execute()
            print(f"✅ Inserted new budget file")
        
        print(f"✅ Success! Result: {result.data}")
        
        # Verify
        verify = client.table("budget_files").select("*").eq("year", year).execute()
        if verify.data:
            row = verify.data[0]
            print(f"✅ Verification: Found budget file for year {row['year']}")
            print(f"   Filename: {row['filename']}")
            print(f"   Size: {len(row['content'])} chars")
        else:
            print("⚠️ Verification failed - no data found")
            
    except Exception as e:
        import traceback
        print(f"❌ Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_budget_upload()





