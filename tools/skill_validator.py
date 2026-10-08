#!/usr/bin/env python3
"""检查 Skill 套件 front matter、中文化和重复 name。"""
from pathlib import Path
import argparse,json,re,sys
FM=re.compile(r'^---\s*\n(.*?)\n---\s*\n',re.S)
CN=re.compile(r'[\u4e00-\u9fff]')
def main():
    ap=argparse.ArgumentParser(description='检查 SKILL.md 结构与中文化'); ap.add_argument('root',nargs='?',default='.'); a=ap.parse_args(); root=Path(a.root)
    files=list(root.rglob('SKILL.md')); errs=[]; names={}
    manifest_path=root/'skills_manifest.json'
    if manifest_path.is_file():
        manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
        if manifest.get('distribution')=='single-entry':
            if sorted(f.relative_to(root).as_posix() for f in files)!=['SKILL.md']:
                errs.append((root,'单入口套件必须且只能有根 SKILL.md'))
            for key in ('module_guides','backend_guides'):
                for relative in manifest.get(key,{}).values():
                    if not (root/relative).is_file(): errs.append((root/relative,'缺少内部模块说明'))
    for f in files:
        txt=f.read_text(encoding='utf-8',errors='ignore'); m=FM.match(txt)
        if not m: errs.append((f,'缺少 YAML front matter')); continue
        fm=m.group(1); nm=re.search(r'^name:\s*(.+)$',fm,re.M); ds=re.search(r'^description:\s*(.+)$',fm,re.M)
        if not nm: errs.append((f,'缺少 name'))
        else:
            name=nm.group(1).strip(); names.setdefault(name,[]).append(f)
        if not ds or len(CN.findall(ds.group(1)))<4: errs.append((f,'description 不是中文或中文过少'))
        body=txt[m.end():]
        if len(CN.findall(body))<30: errs.append((f,'正文中文内容过少'))
    for n,fs in names.items():
        if len(fs)>1: errs.append((fs[0],f'name 重复：{n}'))
    print(f'发现 {len(files)} 个 Skill，问题 {len(errs)} 个')
    for f,msg in errs: print(f'[FAIL] {f}: {msg}')
    raise SystemExit(1 if errs else 0)
if __name__=='__main__': main()
