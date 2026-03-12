with open('routes/realtime_routes.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
print("Line 185-200:")
for i in range(185, 200):
    line = lines[i]
    # Replace non-ASCII chars
    clean_line = line.encode('ascii', 'replace').decode('ascii')
    print(f"{i+1:3d}: {clean_line}", end='')
