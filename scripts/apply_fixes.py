#!/usr/bin/env python
# -*- coding: utf-8 -*-

print("Applying fixes to realtime_routes.py...")

with open('routes/realtime_routes.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

modified = False

# Fix 1: Add confirmation message after session_end detection
for i in range(len(lines)):
    if "elif msg_type == 'session_end':" in lines[i]:
        # Check if confirmation is already added
        if i + 10 < len(lines) and "session_end_received" not in ''.join(lines[i:i+10]):
            print(f"Adding session_end confirmation at line {i+1}")
            # Insert lines after the logger.info line
            insert_pos = i + 2  # After the logger.info line
            indent = "                                "
            new_lines = [
                indent + "logger.info(\"=\"*60)\n",
                indent + "\n",
                indent + "# Send confirmation\n",
                indent + "try:\n",
                indent + "    ws.send(json.dumps({\n",
                indent + "        'type': 'session_end_received',\n",
                indent + "        'message': 'Server received'\n",
                indent + "    }))\n",
                indent + "    logger.info(\"Confirmation sent\")\n",
                indent + "except:\n",
                indent + "    pass\n",
                indent + "\n",
            ]
            lines[insert_pos:insert_pos] = new_lines
            modified = True
            print("  [OK] Confirmation added")
        break

# Fix 2: Improve on_status error handling  
for i in range(len(lines)):
    if 'def on_status(status, message):' in lines[i]:
        # Look for the error logging line
        for j in range(i, min(i+10, len(lines))):
            if 'logger.error(f"Send status error:' in lines[j]:
                # Replace with debug
                lines[j] = lines[j].replace('logger.error', 'logger.debug')
                lines[j] = lines[j].replace('Send status error', 'Status update failed')
                modified = True
                print(f"Fixed on_status error logging at line {j+1}")
                break
        break

# Fix 3: Add logging before assessment_complete
for i in range(len(lines)):
    if "'type': 'assessment_complete'" in lines[i]:
        # Check if logging already exists
        if i > 0 and 'Sending assessment_complete' not in lines[i-1]:
            indent = "                                      "
            lines.insert(i, indent + "logger.info(f\"Sending assessment_complete: {recorder.session_id}\")\n")
            modified = True
            print(f"Added assessment_complete logging at line {i+1}")
        break

if modified:
    with open('routes/realtime_routes.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("\n[SUCCESS] Fixes applied!")
else:
    print("\n[INFO] No changes needed (already fixed)")
