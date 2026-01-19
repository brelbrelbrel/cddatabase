
import sqlite3
import pandas as pd

DB_PATH = r"C:\Users\kawamura\Desktop\music_database.db"

def analyze_potential():
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Total Estimated Value (based on Median Price of identified items)
    # We only count items with a reasonably high match score or valid Discogs ID
    query_value = """
    SELECT 
        COUNT(*) as count,
        SUM(median_price) as total_median,
        AVG(median_price) as avg_price
    FROM releases 
    WHERE median_price > 0
    """
    row_val = conn.execute(query_value).fetchone()
    print(f"💰 **Inventory Potential**")
    print(f"  - Total items with price data: {row_val[0]}")
    print(f"  - Total Median Value: ${row_val[1]:,.2f}")
    print(f"  - Average Item Price: ${row_val[2]:,.2f}")
    
    # 2. eBay Sales Velocity (Items that have actually sold recently)
    query_ebay = """
    SELECT 
        COUNT(*) as sold_items,
        SUM(ebay_sold_count) as total_sales_recorded,
        AVG(ebay_sold_price) as avg_sold_price
    FROM releases 
    WHERE ebay_sold_count > 0 AND ebay_match_score >= 80
    """
    row_ebay = conn.execute(query_ebay).fetchone()
    print(f"\n📉 **eBay Sales Performance (Proven Sellers)**")
    print(f"  - Items with confirmed recent sales: {row_ebay[0]}")
    print(f"  - Average Sold Price: ${row_ebay[2]:,.2f}")

    # 3. High Demand Items (Discogs Want)
    print(f"\n🔥 **Top High Demand Items (by 'Want' count)**")
    query_want = """
    SELECT title, community_want, median_price, ebay_sold_price
    FROM releases 
    ORDER BY community_want DESC 
    LIMIT 5
    """
    for r in conn.execute(query_want):
        print(f"  - {r[0][:40]}... (Want: {r[1]}, Median: ${r[2]})")

    # 4. High Value Items (Median Price > $50)
    print(f"\n💎 **Top High Value Candidates (Median > $50)**")
    query_high = """
    SELECT title, median_price, ebay_sold_price
    FROM releases 
    WHERE median_price > 50
    ORDER BY median_price DESC 
    LIMIT 5
    """
    for r in conn.execute(query_high):
        print(f"  - {r[0][:40]}... (Median: ${r[1]})")

    conn.close()

if __name__ == "__main__":
    analyze_potential()
