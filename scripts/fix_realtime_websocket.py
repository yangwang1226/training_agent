#!/usr/bin/env python
# -*- coding: utf-8 -*-

print("Starting fix for realtime_routes.py...")

# Read original file
with open('routes/realtime_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

original_content = content

# Fix 1: Improve on_status error handling
print("\n[1/3] Fixing on_status error handling...")
old_text_1 = '''          def on_status(status, message):
              try:
                  ws.send(json.dumps({
                      'type': 'status',
                      'status': status,
                      'message': message
                  }))
              except Exception as e:
                  logger.error(f"Send status error: {e}")'''

new_text_1 = '''          def on_status(status, message):
              try:
                  logger.info(f"Qwen status: {status}")
                  if ws and not ws.closed:
                      ws.send(json.dumps({
                          'type': 'status',
                          'status': status,
                          'message': message
                      }))
              except Exception as e:
                  logger.debug(f"Status update failed: {e}")'''

if old_text_1 in content:
    content = content.replace(old_text_1, new_text_1)
    print("  [OK] on_status fixed")
else:
    print("  [SKIP] on_status code block not found")

# Fix 2: Add session_end confirmation
print("\n[2/3] Adding session_end confirmation...")
old_text_2 = '''                          elif msg_type == 'session_end':
                              # ✅ 处理会话结束信号
                              logger.info("收到前端会话结束信号，开始保存和评估...")
                          
                          try:'''

new_text_2 = '''                          elif msg_type == 'session_end':
                              # ✅ 处理会话结束信号
                              logger.info("="*60)
                              logger.info("收到前端会话结束信号，开始保存和评估...")
                              logger.info("="*60)
                              
                              try:
                                  ws.send(json.dumps({
                                      'type': 'session_end_received',
                                      'message': 'Server received end signal'
                                  }))
                                  logger.info("Confirmation sent to frontend")
                              except:
                                  pass
                          
                          try:'''

if old_text_2 in content:
    content = content.replace(old_text_2, new_text_2)
    print("  [OK] session_end fixed")
else:
    print("  [SKIP] session_end code block not found")

# Fix 3: Add assessment_complete logging
print("\n[3/3] Enhancing assessment_complete logging...")
old_text_3 = '''                                      ws.send(json.dumps({
                                          'type': 'assessment_complete',
                                          'session_id': recorder.session_id,
                                          'report': report
                                      }))
                                      logger.info("评估报告生成并保存成功")'''

new_text_3 = '''                                      logger.info(f"Sending assessment_complete: {recorder.session_id}")
                                      ws.send(json.dumps({
                                          'type': 'assessment_complete',
                                          'session_id': recorder.session_id,
                                          'report': report
                                      }))
                                      logger.info("Assessment report generated and saved")
                                      import time
                                      time.sleep(0.2)'''

if old_text_3 in content:
    content = content.replace(old_text_3, new_text_3)
    print("  [OK] assessment_complete fixed")
else:
    print("  [SKIP] assessment_complete code block not found")

# Save file
if content != original_content:
    with open('routes/realtime_routes.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("\n[SUCCESS] realtime_routes.py has been fixed!")
    print("\nChanges made:")
    print("  1. on_status: Check connection before sending")
    print("  2. session_end: Add confirmation message")
    print("  3. assessment_complete: Add detailed logging")
else:
    print("\n[WARNING] No changes made (already fixed or code structure mismatch)")
