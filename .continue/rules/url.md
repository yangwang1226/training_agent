---
globs: |-
  front_end/**/*.js
  routes/**/*.py
description: 用于规范场景相关页面的URL参数格式，确保URL简洁且支持模型选择
alwaysApply: false
---

在场景配置和对练页面之间的跳转中，统一使用简短的scene_id参数而不是传递完整的JSON数据。同时添加provider参数用于选择模型（如qwen、volc）。

URL格式规范：
- 场景配置页面：`/manage_system/scene-config?scene_id={scene_id}&provider={provider}`
- 对练页面：`/realtime/{scene_id}?provider={provider}`

前端跳转时必须包含provider参数，默认值为'qwen'。