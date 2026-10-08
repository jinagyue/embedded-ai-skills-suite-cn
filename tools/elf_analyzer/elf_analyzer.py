#!/usr/bin/env python3
"""中文 ELF 固件分析工具。

依赖 pyelftools。输出段、符号、Flash/RAM 估算、最大函数/对象和 JSON 报告。
设计参考 shangliny10-lab/embedded-skills 的 elf_analyzer（MIT），本文件重新实现并强化 JSON/CI 使用。
"""
from __future__ import annotations
import argparse, json, os, sys
from pathlib import Path
ELFFile = None
SymbolTableSection = None

def require_pyelftools():
    global ELFFile, SymbolTableSection
    if ELFFile is not None:
        return
    try:
        from elftools.elf.elffile import ELFFile as _ELFFile
        from elftools.elf.sections import SymbolTableSection as _SymbolTableSection
    except ImportError:
        print('错误：缺少 pyelftools，请执行：pip install pyelftools', file=sys.stderr)
        raise SystemExit(2)
    ELFFile = _ELFFile
    SymbolTableSection = _SymbolTableSection

FLASH_RANGES=[(0x00000000,0x20000000)]
RAM_RANGES=[(0x20000000,0x40000000)]

def human(n):
    return f'{n/1024:.1f} KiB' if n>=1024 else f'{n} B'

class Analyzer:
    def __init__(self,path):
        require_pyelftools()
        self.path=Path(path); self.fp=self.path.open('rb'); self.elf=ELFFile(self.fp)
    def close(self): self.fp.close()
    def sections(self):
        rows=[]
        for s in self.elf.iter_sections():
            flags=int(s['sh_flags']); addr=int(s['sh_addr']); size=int(s['sh_size'])
            rows.append({'name':s.name,'type':str(s['sh_type']),'address':addr,'size':size,'alloc':bool(flags&2),'write':bool(flags&1),'exec':bool(flags&4)})
        return rows
    def symbols(self):
        rows=[]; seen=set()
        for sec in self.elf.iter_sections():
            if not isinstance(sec,SymbolTableSection): continue
            for sym in sec.iter_symbols():
                name=sym.name
                if not name or name.startswith(('.', '$')): continue
                typ=str(sym['st_info']['type']); size=int(sym['st_size']); addr=int(sym['st_value']); bind=str(sym['st_info']['bind'])
                key=(name,addr,size,typ)
                if key in seen: continue
                seen.add(key); rows.append({'name':name,'type':typ,'size':size,'address':addr,'bind':bind,'section_index':str(sym['st_shndx'])})
        return rows
    def memory(self,secs):
        flash=ram=0; flash_load=0
        for s in secs:
            if not s['alloc']: continue
            a=s['address']; z=s['size']
            if 0<=a<0x20000000: flash+=z
            elif 0x20000000<=a<0x40000000: ram+=z
            # initialized RAM occupies load image in Flash approximately
            if s['write'] and s['alloc'] and s['type']!='SHT_NOBITS' and a>=0x20000000: flash_load+=z
        return {'flash_alloc_bytes':flash,'ram_alloc_bytes':ram,'initialized_ram_load_bytes':flash_load,'estimated_flash_image_bytes':flash+flash_load}
    def report(self,top=30):
        secs=self.sections(); syms=self.symbols(); mem=self.memory(secs)
        funcs=sorted((s for s in syms if s['type']=='STT_FUNC'),key=lambda x:x['size'],reverse=True)
        objs=sorted((s for s in syms if s['type']=='STT_OBJECT'),key=lambda x:x['size'],reverse=True)
        h=self.elf.header
        return {
          'file':str(self.path),'file_size':self.path.stat().st_size,
          'elf':{'class':str(h['e_ident']['EI_CLASS']),'data':str(h['e_ident']['EI_DATA']),'machine':str(h['e_machine']),'entry':int(h['e_entry']),'sections':int(h['e_shnum']),'segments':int(h['e_phnum'])},
          'memory':mem,'sections':secs,'symbol_count':len(syms),'function_count':len(funcs),'object_count':len(objs),
          'largest_functions':funcs[:top],'largest_objects':objs[:top]
        }

def print_report(r,show_sections=False,show_symbols=False):
    e=r['elf']; m=r['memory']
    print('='*72); print('ELF 固件分析'); print('='*72)
    print('文件：',r['file']); print('架构：',e['machine'],'  入口：0x%08X'%e['entry'])
    print('文件大小：',human(r['file_size']))
    print('估算 Flash：',human(m['estimated_flash_image_bytes']),'（ALLOC代码/常量 + 初始化RAM装载）')
    print('估算 RAM：  ',human(m['ram_alloc_bytes']))
    print('符号：',r['symbol_count'],'函数：',r['function_count'],'对象：',r['object_count'])
    print('\n最大函数：')
    for s in r['largest_functions'][:20]: print(f"  {s['size']:8d} 0x{s['address']:08X} {s['name']}")
    print('\n最大对象：')
    for s in r['largest_objects'][:20]: print(f"  {s['size']:8d} 0x{s['address']:08X} {s['name']}")
    if show_sections:
        print('\nSection：')
        for s in sorted(r['sections'],key=lambda x:x['address']):
            if s['size']: print(f"  {s['name']:<24} 0x{s['address']:08X} {s['size']:10d} {'A' if s['alloc'] else '-'}{'W' if s['write'] else '-'}{'X' if s['exec'] else '-'}")
    if show_symbols:
        print('\n提示：完整符号已包含在 --json-out 输出；终端仅显示最大函数/对象。')

def main():
    p=argparse.ArgumentParser(description='中文 ELF 固件分析工具')
    p.add_argument('elf_file'); p.add_argument('--sections',action='store_true'); p.add_argument('--symbols',action='store_true'); p.add_argument('--all',action='store_true')
    p.add_argument('--top',type=int,default=30); p.add_argument('--json-out'); p.add_argument('--report')
    a=p.parse_args(); path=Path(a.elf_file)
    if not path.exists(): p.error(f'ELF 文件不存在：{path}')
    an=Analyzer(path)
    try: r=an.report(a.top)
    finally: an.close()
    print_report(r,a.sections or a.all,a.symbols or a.all)
    if a.json_out:
        Path(a.json_out).parent.mkdir(parents=True,exist_ok=True); Path(a.json_out).write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8'); print('JSON 报告：',a.json_out)
    if a.report:
        lines=['# ELF 固件分析报告','',f"- 文件：`{r['file']}`",f"- 架构：`{r['elf']['machine']}`",f"- Flash 估算：**{human(r['memory']['estimated_flash_image_bytes'])}**",f"- RAM 估算：**{human(r['memory']['ram_alloc_bytes'])}**",'', '## 最大函数','']
        lines += [f"- `{x['name']}`：{x['size']} B" for x in r['largest_functions']]
        lines += ['', '## 最大对象','']+[f"- `{x['name']}`：{x['size']} B" for x in r['largest_objects']]
        Path(a.report).write_text('\n'.join(lines)+'\n',encoding='utf-8'); print('Markdown 报告：',a.report)
if __name__=='__main__': main()
