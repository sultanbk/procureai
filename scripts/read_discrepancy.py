import sqlite3
import json

def main():
    conn = sqlite3.connect("procureai.db")
    cur = conn.cursor()
    
    cur.execute("SELECT rulebook, discrepancies FROM audits WHERE id='aud_ippb_real_pipeline'")
    row = cur.fetchone()
    if row:
        print("--- EXTRACTED RULEBOOK ---")
        if row[0]:
            print(json.dumps(json.loads(row[0]), indent=2))
        else:
            print("No rulebook")
            
        print("\n--- DETECTED DISCREPANCIES ---")
        if row[1]:
            print(json.dumps(json.loads(row[1]), indent=2))
        else:
            print("No discrepancies")
    else:
        print("No audit record found.")
        
    conn.close()

if __name__ == "__main__":
    main()
