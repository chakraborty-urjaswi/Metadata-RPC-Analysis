import requests
import time
from collections import Counter
from multiprocessing import Pool, cpu_count

BASE_URL = "http://72.60.221.150:8080"
STUDENT_ID = "MDS202539" 

def get_secret_key():
    """Step 1: Geting the dynamic 64-character SHA256 key"""
    while True:
        try:
            r = requests.post(f"{BASE_URL}/login", json={"student_id": STUDENT_ID})
            if r.status_code == 200: return r.json().get("secret_key")
            time.sleep(1) # Handle throttling
        except: time.sleep(1)

def mapper(chunk):
    """Step 2: Map phase - Fetch titles and count first words"""
    key = get_secret_key()
    counts = Counter()
    for filename in chunk:
        while True:
            try:
                res = requests.post(f"{BASE_URL}/lookup", json={"secret_key": key, "filename": filename})
                if res.status_code == 200:
                    title = res.json().get("title", "")
                    if title: counts[title.split()[0]] += 1 # Count first word
                    break
                elif res.status_code == 429: time.sleep(1) # Wait if throttled
                else: break
            except: time.sleep(1)
    return counts

if __name__ == "__main__":
    files = [f"pub_{i}.txt" for i in range(1000)] # Restricted to first 1000
    num_procs = cpu_count()
    chunks = [files[i::num_procs] for i in range(num_procs)]
    
    with Pool(num_procs) as p:
        results = p.map(mapper, chunks)
    
    # Reduce phase: Combine all counters
    final_counts = Counter()
    for c in results: final_counts.update(c)
    
    top_10 = [word for word, count in final_counts.most_common(10)]
    print(f"Computed Top 10: {top_10}")

    # Step 3: Verify results
    key = get_secret_key()
    ver_res = requests.post(f"{BASE_URL}/verify", json={"secret_key": key, "top_10": top_10})
    print(f"Final Score: {ver_res.json()}") 
