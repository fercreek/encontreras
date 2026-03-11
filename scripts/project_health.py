import os
import datetime
from pathlib import Path

def get_dir_health(path):
    """Calculates the health of a directory based on last mod time."""
    try:
        files = list(Path(path).rglob('*'))
        if not files:
            return os.path.getmtime(path), 0
        
        last_mod = max(os.path.getmtime(f) for f in files if os.path.isfile(f))
        return last_mod, len(files)
    except Exception:
        return os.path.getmtime(path), 0

def main():
    base_dir = "/Users/fernandocastaneda/Documents"
    print(f"# Orchestrator Audit Tree: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"| Project Folder | Last Activity | Files | Type | Status |")
    print(f"| :--- | :--- | :--- | :--- | :--- |")
    
    dirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and not d.startswith('.')]
    
    results = []
    for d in sorted(dirs):
        full_path = os.path.join(base_dir, d)
        last_mod, count = get_dir_health(full_path)
        last_mod_dt = datetime.datetime.fromtimestamp(last_mod)
        
        # Determine Type
        p_type = "Project"
        if "landing" in d.lower():
            p_type = "Landing 🚀"
        elif "asset" in d.lower():
            p_type = "Assets 📦"
        
        # Determine Status (based on recency)
        days_ago = (datetime.datetime.now() - last_mod_dt).days
        status = "Active ✅"
        if days_ago > 30:
            status = "Stale 🧊"
        if days_ago > 90:
            status = "Archived 📁"
            
        results.append({
            "name": d,
            "mod": last_mod_dt.strftime('%Y-%m-%d'),
            "count": count,
            "type": p_type,
            "status": status,
            "raw_mod": last_mod
        })

    # Sort by most recent
    results.sort(key=lambda x: x['raw_mod'], reverse=True)
    
    for r in results:
        print(f"| {r['name']} | {r['mod']} | {r['count']} | {r['type']} | {r['status']} |")

if __name__ == "__main__":
    main()
