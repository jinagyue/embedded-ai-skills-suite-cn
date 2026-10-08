#!/usr/bin/env python3
"""中文嵌入式架构分层复核器。

思想参考 JiaxI2/Codex-Skills architecture skill 的“先模型分析/人工确认 arch-map，再工具复核”流程（Apache-2.0）。
本工具为 Python 重新实现，不复制其 PowerShell 实现。
"""
from __future__ import annotations
import argparse, fnmatch, json, re, sys
from pathlib import Path
ROLE_LEVEL={'L1_VENDOR':1,'L2_BSP_DRIVER':2,'L3_PLATFORM':3,'L3_DEVICE':3,'L3_PROTOCOL':3,'L4_SERVICE':4,'L5_APP':5,'L5_RTOS':5,'COMMON':0,'CONFIG':0,'TEST':6,'THIRD_PARTY':-1}
INC=re.compile(r'^\s*#\s*include\s*["<]([^">]+)[">]',re.M)
HAL_HDR=re.compile(r'(^|/)(stm32\w*_(hal|ll)\w*\.h|core_cm\w*\.h|cmsis_gcc\.h|cmsis_compiler\.h)$',re.I)

def load_map(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def sources(root):
    skip={'.git','build','Debug','Release','.embedded-ai','Drivers','Middlewares'}
    for p in root.rglob('*'):
        if p.is_file() and p.suffix.lower() in ('.c','.h','.cpp','.hpp') and not any(x in skip for x in p.parts): yield p

def classify(rel,m):
    for rule in m.get('modules',[]):
        pats=rule.get('patterns') or [rule.get('pattern','')]
        if any(fnmatch.fnmatch(rel,pat) for pat in pats if pat): return rule.get('role')
    return None

def include_target(src,inc,all_rel):
    s=inc.replace('\\','/')
    exact=[r for r in all_rel if r==s or r.endswith('/'+s)]
    if len(exact)==1:return exact[0]
    base=Path(s).name; cand=[r for r in all_rel if Path(r).name==base]
    return cand[0] if len(cand)==1 else None

def main():
    ap=argparse.ArgumentParser(description='中文嵌入式架构分层复核器')
    ap.add_argument('root',nargs='?',default='.'); ap.add_argument('--map'); ap.add_argument('--evidence',action='store_true'); ap.add_argument('--strict',action='store_true'); ap.add_argument('--json-out')
    a=ap.parse_args(); root=Path(a.root).resolve(); files=list(sources(root)); rels=[p.relative_to(root).as_posix() for p in files]
    if a.evidence or not a.map:
        ev={'root':str(root),'files':len(rels),'directories':sorted({str(Path(r).parent) for r in rels}),'hal_includes':[]}
        for p,r in zip(files,rels):
            txt=p.read_text(encoding='utf-8',errors='ignore')
            hs=[x for x in INC.findall(txt) if HAL_HDR.search(x.replace('\\','/'))]
            if hs: ev['hal_includes'].append({'file':r,'headers':hs})
        print(json.dumps(ev,ensure_ascii=False,indent=2)); return
    m=load_map(a.map); roles={r:classify(r,m) for r in rels}; findings=[]
    for r,role in roles.items():
        if role is None: findings.append({'severity':'high','type':'unclassified','file':r,'message':'模块未在 arch-map.json 中分类'})
    for p,r in zip(files,rels):
        role=roles.get(r); txt=p.read_text(encoding='utf-8',errors='ignore')
        for inc in INC.findall(txt):
            target=include_target(r,inc,rels)
            if not target: continue
            tr=roles.get(target)
            if role in ROLE_LEVEL and tr in ROLE_LEVEL:
                sl,tl=ROLE_LEVEL[role],ROLE_LEVEL[tr]
                if sl>0 and tl>sl and tr not in ('TEST',):
                    findings.append({'severity':'high','type':'reverse_dependency','file':r,'target':target,'message':f'{role} 反向依赖更高层 {tr}'})
        if role in ('L4_SERVICE','L5_APP','L3_PROTOCOL'):
            for inc in INC.findall(txt):
                if HAL_HDR.search(inc.replace('\\','/')):
                    findings.append({'severity':'high','type':'hal_header_leak','file':r,'header':inc,'message':f'{role} 直接包含 STM32 HAL/LL/CMSIS 头'})
            if re.search(r'\b(?:HAL|LL)_[A-Za-z0-9_]+\s*\(', txt):
                findings.append({'severity':'high','type':'hal_api_leak','file':r,'message':f'{role} 直接调用 HAL/LL API'})
            if re.search(r'\b(?:GPIO[A-K]|GPIO_PIN_\d+|h(?:uart|spi|i2c|adc|tim|can|fdcan|dma)\w*)\b', txt):
                findings.append({'severity':'medium','type':'hardware_symbol_leak','file':r,'message':f'{role} 出现具体 MCU 句柄/GPIO 符号，需确认是否跨层泄漏'})
    out={'root':str(root),'classified':sum(1 for x in roles.values() if x),'unclassified':sum(1 for x in roles.values() if not x),'findings':findings,'roles':roles}
    if a.json_out: Path(a.json_out).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f"已扫描 {len(rels)} 个源码/头文件；未分类 {out['unclassified']}；问题 {len(findings)}")
    for f in findings[:100]: print(f"[{f['severity'].upper()}] {f['type']}: {f['file']} - {f['message']}")
    if a.strict and findings: raise SystemExit(1)
if __name__=='__main__': main()
