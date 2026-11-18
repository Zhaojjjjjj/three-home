# Blender 精模路线（真人电影机甲感）

网页版擎天柱被否（动漫/玩具感）后改走的路线：Blender 参数化建模 → Cycles 渲染验证形态 → 后续绑骨/动画 → 导出 GLB 接回 Three.js 查看器。

## 文件

- `build_optimus.py` — 全部建模 + 材质 + 灯光 + 渲染脚本（约 250 个部件：真实倒角/梯形成型件、分层装甲、暗色内骨架、液压活塞、程序化做旧污渍）
- `optimus.blend` — 脚本生成的工程文件
- `hero_still.png` — 全身主形图（深挖轮，2026-11-18）
- `head_closeup.png` — 头部特写（同轮）

## 构建

```bash
blender --background --python build_optimus.py
```

脚本会重建模型、保存 `optimus.blend`，并渲染全身图与头部特写两张静帧。

环境备注：无头 Linux 缺 libEGL 时 EEVEE 不可用，脚本使用 Cycles CPU（单张约 5–8 分钟）。

## 状态

形态评审中：材质/光照/倒角/内骨架已成立；整体比例仍偏 G1 玩具向，待定夺是继续重塑比例，还是先进入绑骨 + 5 动作 + 变形、导出 GLB。
