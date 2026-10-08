#!/usr/bin/env python3
"""中文嵌入式串口监控工具。

特性：端口枚举、ASCII/HEX/BOTH 显示、毫秒时间戳、日志、发送、自动重连、
有限时长采集和 JSON Lines 证据输出。

设计参考：shangliny10-lab/embedded-skills 的 serial_monitor 工具（MIT）。
本文件为重新实现版本，增加了 --mode、--duration、--jsonl 等适合 AI 调试的能力。
"""
from __future__ import annotations
import argparse, json, sys, threading, time
from datetime import datetime
from pathlib import Path
serial = None
list_ports = None

def require_pyserial():
    global serial, list_ports
    if serial is not None:
        return
    try:
        import serial as _serial
        from serial.tools import list_ports as _list_ports
    except ImportError:
        print('错误：缺少 pyserial，请执行：pip install pyserial', file=sys.stderr)
        raise SystemExit(2)
    serial = _serial
    list_ports = _list_ports

def now_text(): return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

def list_ports_cn(as_json=False):
    require_pyserial()
    rows=[{'port':p.device,'description':p.description,'hwid':p.hwid} for p in list_ports.comports()]
    if as_json: print(json.dumps(rows, ensure_ascii=False, indent=2)); return
    if not rows: print('未发现串口'); return
    print(f"{'端口':<16} {'描述':<40} 硬件ID")
    print('-'*90)
    for r in rows: print(f"{r['port']:<16} {r['description']:<40} {r['hwid']}")

class Monitor:
    def __init__(self,args):
        self.a=args; self.ser=None; self.running=True; self.log=None; self.jsonl=None
        if args.log:
            Path(args.log).parent.mkdir(parents=True,exist_ok=True); self.log=open(args.log,'a',encoding='utf-8')
        if args.jsonl:
            Path(args.jsonl).parent.mkdir(parents=True,exist_ok=True); self.jsonl=open(args.jsonl,'a',encoding='utf-8')
    def connect(self):
        require_pyserial()
        try:
            self.ser=serial.Serial(self.a.port,self.a.baudrate,timeout=self.a.timeout)
            print(f'已连接 {self.a.port} @ {self.a.baudrate} bps')
            return True
        except serial.SerialException as e:
            print(f'连接失败：{e}',file=sys.stderr); return False
    def reconnect(self):
        while self.running:
            try:
                if self.ser: self.ser.close()
            except Exception: pass
            if self.connect(): return True
            if not self.a.reconnect: return False
            time.sleep(self.a.reconnect_interval)
        return False
    def format(self,data):
        ts=f'[{now_text()}] ' if self.a.timestamp else ''
        ascii_s=''.join(chr(b) if 32<=b<127 or b in (9,10,13) else '.' for b in data)
        hex_s=' '.join(f'{b:02X}' for b in data)
        if self.a.mode=='hex': return ts+hex_s
        if self.a.mode=='both': return f'{ts}HEX: {hex_s} | ASCII: {ascii_s}'
        try: text=data.decode(self.a.encoding,errors='replace')
        except LookupError: text=data.decode('utf-8',errors='replace')
        return ts+text
    def emit(self,data):
        text=self.format(data)
        end='\n' if self.a.mode!='ascii' or not text.endswith(('\n','\r')) else ''
        print(text,end=end,flush=True)
        if self.log: self.log.write(text + ('' if text.endswith('\n') else '\n')); self.log.flush()
        if self.jsonl:
            obj={'time':now_text(),'port':self.a.port,'bytes':len(data),'hex':data.hex(' ').upper(),'ascii':data.decode(self.a.encoding,errors='replace')}
            self.jsonl.write(json.dumps(obj,ensure_ascii=False)+'\n'); self.jsonl.flush()
    def reader(self):
        while self.running:
            try:
                if not self.ser or not self.ser.is_open:
                    if not self.reconnect(): break
                data=self.ser.read(self.a.chunk)
                if data: self.emit(data)
            except serial.SerialException as e:
                print(f'\n串口异常：{e}',file=sys.stderr)
                if not self.a.reconnect: break
                time.sleep(self.a.reconnect_interval)
            except Exception as e:
                print(f'\n读取异常：{e}',file=sys.stderr); time.sleep(.1)
    def send(self,text):
        if not self.ser or not self.ser.is_open: return
        if text.startswith('hex:'):
            data=bytes.fromhex(text[4:].replace('0x',''))
        else:
            data=text.encode(self.a.encoding)+(b'\r\n' if self.a.append_crlf else b'')
        self.ser.write(data)
    def run(self):
        if not self.connect() and not self.a.reconnect: return 2
        t=threading.Thread(target=self.reader,daemon=True); t.start(); start=time.monotonic()
        try:
            if self.a.duration>0:
                while time.monotonic()-start<self.a.duration and self.running: time.sleep(.1)
            elif self.a.no_input:
                while self.running: time.sleep(.2)
            else:
                print("输入文字发送；'hex:AA BB' 发送 HEX；Ctrl+C 退出")
                while self.running:
                    try: s=input()
                    except EOFError: break
                    if s.strip().lower() in ('q','quit','exit'): break
                    if s: self.send(s)
        except KeyboardInterrupt: pass
        finally:
            self.running=False; t.join(timeout=1)
            try:
                if self.ser: self.ser.close()
            except Exception: pass
            if self.log: self.log.close()
            if self.jsonl: self.jsonl.close()
        return 0

def main():
    p=argparse.ArgumentParser(description='中文嵌入式串口监控工具')
    p.add_argument('-p','--port'); p.add_argument('-b','--baudrate',type=int,default=115200)
    p.add_argument('--list',action='store_true'); p.add_argument('--list-json',action='store_true')
    p.add_argument('--mode',choices=['ascii','hex','both'],default='ascii')
    p.add_argument('--hex',action='store_true',help='兼容参数：等价 --mode hex')
    p.add_argument('--timestamp',action=argparse.BooleanOptionalAction,default=True)
    p.add_argument('--log'); p.add_argument('--jsonl',help='将每个接收块保存为 JSON Lines')
    p.add_argument('--duration',type=float,default=0,help='采集秒数；0 表示持续运行')
    p.add_argument('--timeout',type=float,default=.2); p.add_argument('--chunk',type=int,default=512)
    p.add_argument('--reconnect',action=argparse.BooleanOptionalAction,default=True)
    p.add_argument('--reconnect-interval',type=float,default=1.5)
    p.add_argument('--encoding',default='utf-8'); p.add_argument('--append-crlf',action='store_true')
    p.add_argument('--no-input',action='store_true',help='不读取键盘，只监控')
    a=p.parse_args();
    if a.list or a.list_json: list_ports_cn(a.list_json); return
    if a.hex: a.mode='hex'
    if not a.port: p.error('请使用 -p/--port 指定串口，或 --list 查看端口')
    raise SystemExit(Monitor(a).run())
if __name__=='__main__': main()
