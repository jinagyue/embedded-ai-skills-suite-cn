# addr2line 自动源码定位

```bash
python tools/addr2line_resolver/addr2line_resolver.py \
  --elf build/app.elf 0x08013A62 0x08002F11
```

也可以直接从日志提取地址：

```bash
python tools/addr2line_resolver/addr2line_resolver.py \
  --elf build/app.elf \
  --log .embedded-ai/debug/hardfault.log \
  --json-out .embedded-ai/debug/addr2line.json
```

默认寻找 `arm-none-eabi-addr2line`。如果工具链不在 PATH：

```bash
python tools/addr2line_resolver/addr2line_resolver.py \
  --tool "C:/Program Files/Arm GNU Toolchain arm-none-eabi/.../bin/arm-none-eabi-addr2line.exe" \
  --elf build/app.elf 0x08013A62
```
