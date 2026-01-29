"""
Simple Data Update Script
Upload your CSV to Supabase in 30 seconds
"""

import pandas as pd
from supabase import create_client
import os

# ===== CONFIGURATION =====
# Update these with your actual values
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-service-role-key-here"
CSV_FILE = "data.csv"  # Your CSV file name
# =========================

def update_data():
    print("\n" + "="*50)
    print("📊 SUPABASE DATA UPDATE")
    print("="*50 + "\n")
    
    # Step 1: Connect
    print("1️⃣  Connecting to Supabase...")
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("   ✅ Connected!\n")
    except Exception as e:
        print(f"   ❌ Failed: {e}\n")
        return
    
    # Step 2: Read CSV
    print(f"2️⃣  Reading {CSV_FILE}...")
    try:
        df = pd.read_csv(CSV_FILE)
        print(f"   ✅ Found {len(df)} rows\n")
    except FileNotFoundError:
        print(f"   ❌ File '{CSV_FILE}' not found!\n")
        return
    
    # Step 3: Clear old data
    print("3️⃣  Clearing old data...")
    try:
        supabase.table("data").delete().neq("id", 0).execute()
        print("   ✅ Cleared!\n")
    except:
        print("   ⚠️  Skipping (table might be empty)\n")
    
    # Step 4: Upload new data
    print("4️⃣  Uploading new data...")
    try:
        data = df.to_dict('records')
        
        # Upload in batches of 1000
        for i in range(0, len(data), 1000):
            batch = data[i:i+1000]
            supabase.table("data").insert(batch).execute()
            print(f"   📤 {min(i+1000, len(data))}/{len(data)} rows")
        
        print(f"\n   ✅ All {len(data)} rows uploaded!\n")
    except Exception as e:
        print(f"   ❌ Upload failed: {e}\n")
        return
    
    print("="*50)
    print("✅ SUCCESS! Your API now serves fresh data!")
    print("="*50 + "\n")

if __name__ == "__main__":
    update_data()
