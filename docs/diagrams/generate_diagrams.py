"""Generate editable SVG and PNG architecture diagrams from module documentation.

Run from any directory: python docs/diagrams/generate_diagrams.py
Pillow is needed only to render PNG; it is not a skill runtime dependency.
"""
from pathlib import Path
from html import escape
import json
import math
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'docs/assets/skills'
COLORS = {
    'blue': ('#edf4ff', '#2463b4'),
    'teal': ('#eaf8f5', '#117a68'),
    'amber': ('#fff5e6', '#a96812'),
    'purple': ('#f2edfc', '#7150a3'),
    'gray': ('#f3f5f8', '#596778'),
}
DIAGRAMS = []


class Diagram:
    def __init__(self, key, title, subtitle, note='', height=1000):
        self.key, self.title, self.subtitle = key, title, subtitle
        self.note, self.height = note, height
        self.nodes, self.edges, self.groups = {}, [], []
        DIAGRAMS.append(self)

    def box(self, key, x, y, w, h, title, lines=(), tone='blue'):
        self.nodes[key] = dict(x=x, y=y, w=w, h=h, title=title,
                               lines=list(lines), tone=tone)
        return key

    def group(self, x, y, w, h, title, tone='gray'):
        self.groups.append(dict(x=x, y=y, w=w, h=h, title=title, tone=tone))

    def edge(self, a, b, axis='v', label='', dashed=False, points=None):
        na, nb = self.nodes[a], self.nodes[b]
        if points is None:
            if axis == 'h':
                left_to_right = nb['x'] > na['x']
                start = (na['x'] + (na['w'] if left_to_right else 0), na['y'] + na['h']/2)
                end = (nb['x'] + (0 if left_to_right else nb['w']), nb['y'] + nb['h']/2)
                mid = (start[0] + end[0])/2
                points = [start, (mid, start[1]), (mid, end[1]), end]
            else:
                down = nb['y'] > na['y']
                start = (na['x']+na['w']/2, na['y']+(na['h'] if down else 0))
                end = (nb['x']+nb['w']/2, nb['y']+(0 if down else nb['h']))
                mid = (start[1]+end[1])/2
                points = [start, (start[0], mid), (end[0], mid), end]
        self.edges.append(dict(a=a, b=b, points=points, label=label, dashed=dashed))


def vertical(key, title, subtitle, rows, side_title, side_lines, note=''):
    d = Diagram(key, title, subtitle, note)
    for i, (name, details, tone) in enumerate(rows):
        d.box(str(i), 90, 190+i*133, 950, 98, name, details, tone)
        if i:
            d.edge(str(i-1), str(i))
    d.box('side', 1120, 245, 390, 410, side_title, side_lines, 'gray')
    return d


def stages(key, title, subtitle, rows, note='', feedback=False):
    d = Diagram(key, title, subtitle, note)
    # Two rows, three stages each; arrows follow a serpentine sequence.
    for i, (name, lines, tone) in enumerate(rows):
        r, c = divmod(i, 3)
        col = c if r == 0 else 2-c
        d.box(str(i), 90+col*500, 235+r*310, 420, 175, name, lines, tone)
        if i:
            d.edge(str(i-1), str(i), 'v' if i == 3 else 'h')
    if feedback:
        d.edge('5', '0', dashed=True, points=[(90,632),(48,632),(48,322),(90,322)])
    return d


# Single external entry, all 14 professional modules and all 12 backends.
d = Diagram('embeddedskills', '嵌入式技能套件 · 单入口架构',
            '任务按需路由到内部 GUIDE.md，再调用对应脚本；外部只注册一个 SKILL.md',
            '实线：专业路由与状态流。虚线：工具选用。专业模块给出方法，工具后端执行命令。', 1360)
d.box('entry', 440, 170, 720, 125, 'embeddedskills / SKILL.md',
      ['用户任务 → 专业模块选择 → 工具后端选择'], 'blue')
d.group(65, 350, 1470, 350, '专业模块层 / 14 个 GUIDE.md', 'blue')
categories = [
    ('设计与平台', ['00 总工作流', '01 五层架构', '02 C99 实现', '03 Cortex-M']),
    ('外设与并发', ['04 STM32 / BSP', '05 Device / Service', '06 FreeRTOS / IPC', '07 通信协议']),
    ('验证与演进', ['08 Bring-up / 调试', '09 评审与测试', '10 可靠性 / 低功耗', '11 渐进重构']),
    ('证据与闭环', ['12 AI 自动调试', '13 固件分析工具箱'])]
for i, (name, lines) in enumerate(categories):
    d.box('p'+str(i), 95+i*360, 425, 330, 225, name, lines)
    center=260+i*360
    d.edge('entry', 'p'+str(i), points=[(800,295),(800,410),(center,410),(center,425)])
d.group(65, 755, 1470, 325, '执行后端层 / 12 个 GUIDE.md + scripts/', 'teal')
backs = [
    ('构建', ['Keil MDK', 'CMake / ARM GCC', 'EIDE']),
    ('下载与调试', ['J-Link', 'OpenOCD', 'probe-rs']),
    ('通信与连接', ['serial / CAN / net', 'SSH / terminal']),
    ('阶段编排', ['workflow', '发现 → 选择 → 串联', '聚合结果与状态'])]
for i, (name, lines) in enumerate(backs):
    d.box('b'+str(i), 95+i*360, 835, 330, 195, name, lines, 'teal')
    # Independent routes from the single entry; no 1:1 module/backend mapping.
    center=260+i*360
    d.edge('entry', 'b'+str(i), dashed=True,
           points=[(440,232),(35,232),(35,720),(800,720),(800,815),(center,815),(center,835)])
d.box('data', 210, 1140, 1180, 105, '工程侧证据与状态',
      ['.embedded-ai/：分析报告      .embeddedskills/：配置 / 状态 / 执行日志'], 'gray')
for i in range(4):
    d.edge('b'+str(i), 'data')

stages('00-embedded-workflow', '嵌入式开发 · 总流程',
       '从工程发现到运行证据，以可验证的纵向切片推进', [
    ('01 工程发现', ['.ioc / MCU / SDK / RTOS', '工程目录与构建系统'], 'blue'),
    ('02 静态证据', ['工程扫描 / 资源审计', '分层归类 / 依赖门禁'], 'blue'),
    ('03 设计契约', ['Task / IPC / 数据所有权', '公共接口 / 错误码'], 'purple'),
    ('04 最小实现', ['先接口后实现', '按纵向链路修改'], 'purple'),
    ('05 构建与分析', ['编译 / 链接', 'ELF / MAP / Flash / RAM'], 'teal'),
    ('06 采证与复核', ['串口 / RTT / GDB', '比较修改前后的证据'], 'teal')],
    '流程按本次任务范围裁剪；需要设备操作时执行已授权的阶段。', True)

vertical('01-embedded-architecture', '嵌入式软件 · 五层架构',
         '箭头表示上层对下层的依赖；职责以实现与资源所有权为依据', [
    ('L5  App + RTOS 任务编排', ['产品流程 / 状态机 / 任务入口'], 'blue'),
    ('L4  Business Service', ['测量 / 存储 / 通信 / 电源 / UI 能力'], 'teal'),
    ('L3  Device / Protocol / BSP Service', ['具体器件 / 协议语义 / 稳定数据通道'], 'purple'),
    ('L2  BSP Driver', ['GPIO / UART / SPI / I2C / ADC / TIM / DMA / CAN'], 'amber'),
    ('L1  Vendor / CubeMX', ['CMSIS / HAL / LL / Startup / IRQ / 生成初始化'], 'gray')],
    '横向公共资源', ['Middlewares/', 'Common/', 'Config/', 'Tests/', '', '复核：include / 调用', 'HAL 泄漏 / 构建目标'],
    'APP 不直接调用 HAL；禁止反向 include；arch-map.json 记录人工确认的语义角色。')

d = Diagram('02-c99-embedded', 'C99 模块 · 接口与状态结构',
            '公共契约与私有实现分开；调用者通过状态码接收结果',
            'volatile 不提供线程安全；并发访问需要明确的 IPC 或同步机制。')
d.box('caller', 90, 280, 360, 175, '调用者 / APP / Service', ['参数 / 长度 / 超时', '明确缓冲区所有权'])
d.box('api', 565, 280, 440, 175, 'module.h · 公共契约', ['固定宽度类型 / 配置结构', 'init / start / process / stop'], 'teal')
d.box('impl', 1120, 280, 390, 175, 'module.c · 实现', ['参数与状态检查', '错误传播 / 可重入约束'], 'purple')
d.box('state', 1120, 610, 390, 175, '文件私有状态', ['static 状态 / 有界缓冲区', '栈预算 / 资源生命周期'], 'gray')
d.box('result', 565, 610, 440, 175, 'mod_status_t', ['OK / EINVAL / EBUSY', 'ETIMEOUT / EIO'], 'amber')
for a,b in [('caller','api'),('api','impl')]: d.edge(a,b,'h')
d.edge('impl','state'); d.edge('impl','result')
d.edge('result','caller', points=[(565,697),(490,697),(490,505),(270,505),(270,455)])

d = Diagram('03-arm-cortexm', 'Cortex-M · 启动与异常结构',
            '启动链路、异常证据与 DMA / Cache 一致性三个关注面',
            'RTOS ISR API 受中断优先级约束；有 Cache 的平台需处理 DMA 缓冲区一致性。')
for i,(name,lines) in enumerate([
    ('Reset / 向量表',['Reset_Handler 入口']),
    ('运行环境初始化',['.data / .bss / SystemInit']),
    ('main / Task / ISR',['NVIC 优先级 / 延后处理'])]):
    d.box('s'+str(i),90+i*500,205,420,135,name,lines)
    if i:d.edge('s'+str(i-1),'s'+str(i),'h')
d.box('fault',1090,510,420,180,'Fault 现场',['PC / LR / xPSR / MSP / PSP','CFSR / HFSR / BFAR / MMFAR'],'amber')
d.box('decode',590,510,420,180,'解码与符号定位',['HardFault Decoder','addr2line + ELF → 源码行'],'teal')
d.box('memory',90,510,420,180,'内存与外设一致性',['栈边界 / MPU / Cache','DMA：对齐 / clean / invalidate'],'purple')
d.edge('s2','fault');d.edge('fault','decode','h')

d=Diagram('04-stm32-platform','STM32 · 配置与 BSP 结构',
          'CubeMX 管理硬件配置；BSP 对上提供稳定板级 API',
          '.ioc 与源码双向复核 GPIO / NVIC / DMA / RTOS，检查配置漂移。')
d.box('ioc',90,200,420,155,'.ioc / CubeMX',['时钟 / PinMux / NVIC','DMA / 外设 / RTOS 配置'])
d.box('vendor',590,200,420,155,'生成初始化 / HAL / LL',['USER CODE 扩展点','MCU 句柄与厂商接口'],'gray')
d.box('bsp',1090,200,420,155,'BSP Driver',['GPIO / UART / SPI / I2C','ADC / TIM / DMA / CAN'],'teal')
d.edge('ioc','vendor','h',label='生成');d.edge('bsp','vendor','h',label='封装')
d.box('service',1090,555,420,155,'Device / Service / APP',['使用稳定 BSP API','隐藏 HAL_* 与 MCU 句柄'],'purple')
d.edge('service','bsp')
d.box('audit',90,555,920,155,'配置与源码一致性检查',['parse_ioc / stm32_resource_audit','ioc_source_consistency：资源与配置漂移'],'amber')
d.edge('ioc','audit'); d.edge('vendor','audit')

d=Diagram('05-device-service','Device / Protocol / Service · 职责结构',
          '业务能力、器件控制、字节语义与数据通道分开',
          'Protocol 负责字节与语义转换；APP 使用业务能力接口，不感知具体 HAL 句柄。')
d.box('app',520,175,560,95,'APP / 产品流程',[], 'blue')
d.box('business',520,340,560,110,'Business Service',['measurement_start / get_result'],'teal')
d.edge('app','business')
for i,(key,title,lines) in enumerate([
    ('device','Device · 具体器件',['传感器 / Flash / 显示屏','寄存器与器件行为']),
    ('protocol','Protocol · 语义转换',['帧格式 / CRC / 命令码','编码 / 解码 / 边界检查']),
    ('stream','BSP Service · 数据通道',['UART + DMA + IDLE','ringbuffer + notification'])]):
    d.box(key,90+i*500,525,420,165,title,lines,'purple'); d.edge('business',key)
d.box('bsp',340,780,920,100,'BSP Driver',['稳定板级 API → HAL / LL → MCU 外设'],'amber')
d.edge('device','bsp');d.edge('stream','bsp')

d=Diagram('06-freertos-design','FreeRTOS · Task 与 IPC 结构',
          '按独立并发活动划分 Task；每条连线标明交互机制',
          '示例关系用于任务设计；具体 Task 数量、优先级与栈预算由目标工程确定。')
d.box('isr',90,195,420,140,'ISR / 外设事件',['采样 / 清标志 / 时间戳','非阻塞投递事件'],'amber')
d.box('comm',90,475,420,155,'CommTask',['接收 / 协议解析','命令分发'])
d.edge('isr','comm',label='Notification')
d.box('measure',590,475,420,155,'MeasureTask',['采集与计算','测量结果'],'teal')
d.box('storage',1090,475,420,155,'StorageTask / UITask',['存储 / 显示','结果消费'],'purple')
d.edge('comm','measure','h',label='Queue');d.edge('measure','storage','h',label='Queue')
d.box('timer',590,195,420,140,'Software Timer',['周期事件','通知 Task'],'amber');d.edge('timer','measure',label='Notification')
d.box('shared',590,755,420,130,'共享 SPI / UART 资源',['以 Mutex 串行化访问'],'gray')
d.edge('measure','shared');d.edge('storage','shared')
d.box('health',1090,195,420,140,'HealthTask / 运行探针',['活性 / Stack HWM / Heap','运行时记录 → 分析报告'],'teal')
for key in ['comm','measure','storage']:
    n=d.nodes[key]
    d.edge(key,'health',dashed=True,points=[(n['x']+210,475),(n['x']+210,410),(1300,410),(1300,335)])

vertical('07-embedded-protocols','嵌入式通信 · 分层链路',
         '发送方向自上而下；接收方向自下而上，Protocol 完成字节与语义转换',[
    ('APP / Service',['语义命令 / 业务结果'],'blue'),
    ('Protocol',['帧界定 / 长度 / CRC / 字节序 / 重同步'],'purple'),
    ('BSP Service / Link',['字节流 / 消息 / 环形缓冲区'],'teal'),
    ('BSP Driver',['驱动 API / HAL 封装'],'amber'),
    ('UART / CAN / SPI / I2C / USB',['MCU 通信外设'],'gray')],
    'UART 接收示例',['DMA + IDLE','↓','环形 / 双缓冲','↓','Task 通知','↓','Protocol parser'],
    '接收回调仅记录数据段并通知 Task；协议必须处理超时、缓存上限和异常输入。')

stages('08-debugging-bringup','Bring-up · 逐层验证结构',
       '一次增加一个复杂因素，以基础硬件为起点',[
    ('01 基础硬件',['电源 / 复位 / SWD','连接与复位原因'],'gray'),
    ('02 最小运行',['时钟 / GPIO 心跳','调试串口 / Tick'],'blue'),
    ('03 外设与中断',['单个外设','DMA / IRQ'],'blue'),
    ('04 并发与中间件',['RTOS / Middleware','完整业务'],'purple'),
    ('05 运行证据',['日志 / 栈水位 / Queue','IRQ / DMA / 波形'],'teal'),
    ('06 Fault 定位',['寄存器 → PC / LR','ELF + addr2line → 源码'],'amber')],
       '异常定位后保全证据，再做最小修复与重现验证。',True)

vertical('09-quality-review-testing','质量验证 · 测试层级结构',
         '测试范围从纯逻辑扩展到真实外设与系统环境',[
    ('Host Unit Test',['Protocol / 算法 / 状态机 / Common'],'blue'),
    ('Integration',['Service + Fake Device / BSP'],'blue'),
    ('Target Test',['真实 MCU 外设'],'teal'),
    ('HIL',['实际板卡与仪器'],'teal'),
    ('Regression',['保存复现用例，持续比较修复前后行为'],'purple')],
    '跨阶段评审与门禁',['功能与边界 / 并发','内存 / 栈 / 硬件资源','错误处理 / 架构依赖','','构建后：ELF / MAP','Flash / RAM / 段增长','最大函数 / 最大对象'],
    '层级之间表示验证范围扩展；图中并不声明已完成目标工程的各级测试。')

d=Diagram('10-reliability-lowpower','可靠性与低功耗 · 状态结构',
          '将失败显式建模；由健康任务统一管理看门狗',
          '唤醒后恢复时钟并复核外设；超时、降级与恢复条件由目标系统明确规定。')
for i,(name,tone) in enumerate([('INIT','gray'),('ONLINE','teal'),('DEGRADED','amber'),('OFFLINE','gray'),('RECOVERING','purple')]):
    d.box(str(i),90+i*300,205,220,100,name,[],tone)
    if i:d.edge(str(i-1),str(i),'h')
d.edge('4','1',dashed=True,points=[(1400,305),(1400,370),(500,370),(500,305)])
d.box('tasks',90,460,420,155,'关键 Task 活性证明',['计数 / 时间戳 / 完成信号'],'blue')
d.box('health',590,460,420,155,'HealthTask',['汇总关键任务状态','符合健康条件才喂狗'],'teal')
d.box('watch',1090,460,420,155,'Watchdog',['系统停滞 → 复位','记录复位原因'],'amber')
d.edge('tasks','health','h');d.edge('health','watch','h')
d.box('power',220,735,1160,135,'电源状态与恢复路径',['RUN / SLEEP / STOP / OFF','资源状态 + 唤醒源 → 时钟恢复 → 外设重新校验'],'purple')

stages('11-refactor-existing','存量工程 · 渐进重构路径',
       '每次迁移一条可验证纵向链路，保留旧路径与回退点',[
    ('01 现状盘点',['职责 / 调用 / HAL / RTOS','共享状态与目标层'],'gray'),
    ('02 抽出 Protocol',['纯 parser / 帧与语义','保留协议复现用例'],'purple'),
    ('03 抽出 Service',['业务能力与错误路径','Task 调用能力接口'],'teal'),
    ('04 封装 BSP / Device',['板级资源 / 具体器件','稳定 API 隔离句柄'],'amber'),
    ('05 整理 Task 与状态',['等待事件 / 调用 APP','消除可写 extern'],'blue'),
    ('06 门禁与回归',['扫描 / 构建 / 测试','验证后调整目录'],'teal')],
       '循环箭头：每个迁移步骤都复核行为与依赖，再进入下一条链路。',True)

stages('12-auto-debug','AI 自动调试 · 证据闭环',
       '先建立证据，再定位与最小修改；每次修复返回构建与采证',[
    ('01 静态工程模型',['源码 / .ioc / 分层 / RTOS','GPIO / IRQ / DMA 一致性'],'blue'),
    ('02 构建与固件分析',['Build → MAP / ELF','Flash / RAM / 符号'],'teal'),
    ('03 可选设备阶段',['按任务选择 Flash / Debug','串口 / RTT / GDB 采证'],'amber'),
    ('04 运行时分析',['Task / Stack HWM / Heap','日志与异常记录'],'purple'),
    ('05 故障定位',['Fault 寄存器 / PC / LR','addr2line + ELF → 源码'],'purple'),
    ('06 最小修改与复核',['AI 修改 → 重新构建','重新采证 / 比较差异'],'teal')],
       '默认不自动烧录；循环中的设备阶段仅按任务授权与可用证据执行。',True)

d=Diagram('13-firmware-tools','固件工具箱 · 输入与分析结构',
          '工具围绕三类证据工作：静态工程、构建产物、运行记录',
          '分析结果供架构与故障判断使用；硬件结论仍需对应的运行或测量证据。')
columns=[
    ('工程源码 / .ioc',['目录 / include / 外设配置'],
     '静态扫描与门禁',['工程 / 架构 / HAL 泄漏','Pin / DMA / IRQ / RTOS','配置与源码一致性'],
     '工程模型 / 架构报告',['资源映射 / 依赖关系']),
    ('MAP / ELF',['段 / region / 符号 / 地址'],
     '固件产物分析',['Keil MAP Analyzer','ELF Analyzer','addr2line Resolver'],
     '资源与源码定位',['Flash / RAM / 最大符号']),
    ('串口 / RTT / Fault 日志',['运行快照 / 寄存器 / PC'],
     '运行记录分析',['Serial Monitor','FreeRTOS Runtime Analyzer','HardFault Decoder'],
     '运行与异常报告',['Task / 栈堆 / Fault / 源码行'])]
for i,(a,al,b,bl,c,cl) in enumerate(columns):
    x=90+i*500
    d.box('in'+str(i),x,200,420,140,a,al,'gray')
    d.box('tool'+str(i),x,430,420,210,b,bl,'blue')
    d.box('out'+str(i),x,745,420,130,c,cl,'teal')
    d.edge('in'+str(i),'tool'+str(i));d.edge('tool'+str(i),'out'+str(i))


def build_backend(key,title,source,selection,engine,engine_lines,outputs):
    d=Diagram(key,title,'工程发现、配置选择、构建执行与产物记录的调用结构',
              '图示为后端能力结构；图中工具路径与构建产物由本机环境和目标工程确定。')
    d.box('source',90,225,420,155,source,selection,'gray')
    d.box('select',590,225,420,155,'工程与目标选择',['CLI / config / state','scan + 目标枚举'],'blue')
    d.box('exec',1090,225,420,155,engine,engine_lines,'purple')
    d.edge('source','select','h');d.edge('select','exec','h')
    d.box('result',1090,605,420,170,'构建结果与日志',outputs,'teal')
    d.box('state',590,605,420,170,'.embeddedskills/',['config.json：已选参数','state.json：产物与执行状态'],'gray')
    d.box('next',90,605,420,170,'后续分析 / 工具调用',['ELF / MAP / size','由 workflow 选择后续阶段'],'amber')
    d.edge('exec','result');d.edge('result','state','h');d.edge('state','next','h')
    return d

build_backend('keil','Keil MDK · 构建后端结构','.uvprojx / .uvproj / .uvmpw',
              ['工程文件 / Target'], 'UV4.exe / Keil 工具链',['build / rebuild / clean'],
              ['错误 / 警告 / 日志','AXF / HEX / BIN 等产物路径'])
build_backend('gcc','CMake / ARM GCC · 构建结构','CMake 工程',
              ['CMakeLists / Presets','当前支持 CMake 型工程'], 'CMake + arm-none-eabi-gcc',
              ['configure → build','rebuild / clean / size'],['ELF / 构建日志','text / data / bss'])
build_backend('eide','EIDE · 构建后端结构','.eide/eide.yml',
              ['工程发现 / 配置枚举','ConfigName / builder.params'], 'unify_builder',
              ['ARM CC (AC5 / AC6) 或 GCC','build / rebuild / clean / size'],['ELF / HEX / 日志','结构化结果与产物路径'])


def probe_backend(key,title,engine,protocol,observe,formats):
    d=Diagram(key,title,'主机包装脚本通过调试后端访问目标 MCU，聚合执行结果与观测数据',
              '下载、复位、写内存等设备动作按本次任务选择；图中不表示已连接或验证设备。')
    d.box('input',90,210,420,160,'目标与输入',['芯片 / 探针 / 接口 / 地址',formats],'gray')
    d.box('wrap',590,210,420,160,'Python 后端脚本',['参数解析 / 子进程调用','统一 JSON 与日志'],'blue')
    d.box('engine',1090,210,420,160,engine,['下载 / 读内存 / 执行控制'],'purple')
    d.edge('input','wrap','h');d.edge('wrap','engine','h')
    d.box('target',1090,590,420,185,'探针 → 目标 MCU',[protocol,'Flash / RAM / CPU 寄存器'],'amber')
    d.edge('engine','target')
    d.box('observe',590,590,420,185,'观测与源码调试',observe,'teal')
    d.edge('target','observe','h')
    d.box('report',90,590,420,185,'诊断结果',['寄存器 / 内存 / backtrace','运行日志与阶段状态'],'teal')
    d.edge('observe','report','h')

probe_backend('jlink','J-Link · 下载与调试结构','J-Link Commander / Server','SWD / JTAG',
              ['GDB：backtrace / locals','RTT / 外部 SWO viewer'],'HEX / BIN / ELF')
probe_backend('openocd','OpenOCD · 下载与调试结构','OpenOCD / GDB Server','调试适配器 / 目标配置',
              ['GDB / 寄存器 / 断点','semihosting / ITM'],'固件文件 / interface + target')
probe_backend('probe-rs','probe-rs · 探针与调试结构','probe-rs CLI / GDB','支持的调试探针 / 目标芯片',
              ['attach / run / GDB','RTT 日志'],'ELF / HEX / BIN / UF2')

d=Diagram('serial','串口后端 · 收发与日志结构',
          'pyserial 接入 UART；读取、发送、日志和可选多路复用分开',
          '串口采集后端用于数据与证据收集；持续命令会话可使用 terminal 后端。')
d.box('config',90,205,420,140,'端口与链路配置',['scan / COM / 波特率','数据位 / 校验位 / 超时'],'gray')
d.box('serial',590,205,420,140,'pyserial / 串口连接',['主机串口句柄','端口读写与生命周期'],'blue')
d.box('board',1090,205,420,140,'USB-UART ↔ MCU',['UART TX / RX','文本与二进制字节'],'amber')
d.edge('config','serial','h');d.edge('serial','board','h')
d.box('read',90,550,420,175,'接收与监控',['monitor / hex','文本或 HEX 输出'],'teal')
d.box('log',590,550,420,175,'日志与可选多路复用',['log → 文件','mux → 多客户端读取'],'teal')
d.box('send',1090,550,420,175,'发送入口',['send：文本 / Hex','返回实际发送结果'],'purple')
d.edge('serial','read');d.edge('serial','log');d.edge('send','board')

d=Diagram('can','CAN / CAN-FD · 总线工具结构',
          '适配器接入总线；收帧、发送、解码与统计构成独立能力',
          '仲裁域与数据域速率、通道及 FD 模式由目标网络配置确定。')
d.box('config',90,205,420,145,'接口 / 通道 / 比特率',['scan → 可用接口','PCAN / Vector / slcan 等'],'gray')
d.box('pythoncan',590,205,420,145,'python-can / 设备驱动',['统一 CAN 帧接口','适配器连接'],'blue')
d.box('bus',1090,205,420,145,'CAN / CAN-FD 总线',['ID / DLC / Data / Flags','标准 / 扩展 / FD 帧'],'amber')
d.edge('config','pythoncan','h');d.edge('pythoncan','bus','h')
d.box('recv',90,555,420,175,'monitor / log / stats',['报文监控 / ASC / BLF / CSV','负载 / ID 分布 / 帧率'],'teal')
d.box('decode',590,555,420,175,'decode + 数据库',['DBC / ARXML 等','cantools → 信号值'],'teal')
d.box('send',1090,555,420,175,'send',['标准 / 扩展 / 远程 / FD 帧','单次 / 周期发送'],'purple')
d.edge('pythoncan','recv');d.edge('recv','decode','h');d.edge('send','bus')

d=Diagram('net','网络后端 · 抓包与分析结构',
          '在线抓包与离线分析分开；连通性检测是并行诊断能力',
          '抓包依赖接口选择与抓包驱动；统计结果由实际采集的 PCAP / PCAPNG 产生。')
d.box('iface',90,210,420,155,'iface / 网络接口',['目标 / 过滤器 / 时长','主机 ↔ 嵌入式设备'],'gray')
d.box('capture',590,210,420,155,'capture / tshark / dumpcap',['抓包接口 / Npcap 等','采集网络帧'],'blue')
d.box('pcap',1090,210,420,155,'PCAP / PCAPNG',['保存采集文件','也可输入已有抓包文件'],'amber')
d.edge('iface','capture','h');d.edge('capture','pcap','h')
d.box('analyze',1090,590,420,170,'离线分析与统计',['tshark / capinfos','协议 / 会话 / 流量'],'teal')
d.box('summary',590,590,420,170,'结构化网络证据',['JSON / 日志','定位链路与协议问题'],'teal')
d.box('connect',90,590,420,170,'并行连通性诊断',['ping / traceroute / 端口','系统网络工具'],'purple')
d.edge('pcap','analyze');d.edge('analyze','summary','h');d.edge('connect','summary','h')

d=Diagram('ssh','SSH · 远程操作网关结构',
          '标准 OpenSSH 配置提供 Host 别名、认证与跳板信息',
          '持续交互 Shell 使用 terminal；本后端提供命令、传输、探测与隧道入口。')
d.box('host',90,210,420,155,'Host 别名 / SSH config',['HostName / User / Port','密钥 / ProxyJump'],'gray')
d.box('resolve',590,210,420,155,'ssh_config / 目标解析',['list / find / resolve / show','确定唯一远端'],'blue')
d.box('remote',1090,210,420,155,'OpenSSH ↔ 远程设备',['身份认证 / 连接','Linux 开发板或服务器'],'amber')
d.edge('host','resolve','h');d.edge('resolve','remote','h')
for i,(key,title,lines) in enumerate([
    ('exec','ssh_exec / ssh_probe',['远程命令 / 固定只读探测','标准输出 / 退出码']),
    ('transfer','ssh_transfer',['SCP 上传 / 下载','本地与远端文件路径']),
    ('tunnel','ssh_tunnel',['本地端口转发','本地端口 ↔ 远端服务'])]):
    d.box(key,90+i*500,590,420,180,title,lines,'teal');d.edge('remote',key)

d=Diagram('terminal','交互终端 · 会话结构',
          '后台会话保存连接状态；send 与 read 组成持续的命令 / 响应交互',
          'read 读取并清空输出缓冲；stop 停止会话并清理状态。')
d.box('cli',90,205,420,160,'terminal_session.py',['start / send / read / attach','list / status / stop'],'blue')
d.box('session',590,205,420,160,'后台会话与输出缓冲',['会话 ID / 名称 / 连接状态','持续读取远端输出'],'purple')
d.box('state',1090,205,420,160,'.embeddedskills/state.json',['会话状态记录','状态查询 / 生命周期'],'gray')
d.edge('cli','session','h',label='命令 / 数据');d.edge('session','state','h')
for i,(key,title,lines) in enumerate([
    ('serial','serial 后端',['pyserial → MCU UART','AT / 控制台 / Bootloader']),
    ('ssh','ssh 后端',['OpenSSH → 远端 Shell','持续命令与响应']),
    ('local','local 后端',['Python 标准库','本机 Shell / REPL / CLI'])]):
    d.box(key,90+i*500,590,420,180,title,lines,'teal');d.edge('session',key)

d=Diagram('workflow','Workflow · 后端编排结构',
          '发现、选择、串联与聚合；通过子进程复用已有后端',
          'observe 生成推荐观测命令；编排器内部不长时间占用观测通道。')
d.box('config',90,180,420,150,'配置与阶段请求',['CLI → preferred_* → 自动发现','.embeddedskills/config.json'],'gray')
d.box('plan',590,180,420,160,'workflow_plan / workflow_run',['plan / build / build-flash','build-debug / observe','diagnose'],'blue')
d.box('state',1090,180,420,150,'执行结果与 state.json',['阶段状态 / 产物路径','聚合底层结构化错误'],'teal')
d.edge('config','plan','h');d.edge('plan','state','h')
d.box('build',90,455,420,165,'构建后端',['Keil / GCC / EIDE','成功后产生固件路径'],'purple')
d.box('probe',590,455,420,165,'下载 / 调试后端',['J-Link / OpenOCD / probe-rs','按阶段请求选择'],'amber')
d.box('observe',1090,455,420,165,'观测候选',['J-Link RTT / SWO','OpenOCD semihosting / ITM','probe-rs RTT'],'teal')
d.edge('plan','build');d.edge('plan','probe');d.edge('plan','observe')
d.edge('build','probe','h',label='固件路径')
d.box('result',290,760,1020,110,'阶段串联边界',['构建失败停止后续设备阶段；单次构建直接使用对应后端即可。'],'gray')


def font(size, bold=False):
    override = os.environ.get('DIAGRAM_FONT_BOLD' if bold else 'DIAGRAM_FONT')
    candidates = [override] if override else []
    candidates += [str(Path(os.environ.get('WINDIR','C:/Windows')) / 'Fonts' / ('msyhbd.ttc' if bold else 'msyh.ttc')),
                   '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
                   '/System/Library/Fonts/PingFang.ttc']
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate,size=size)
    raise RuntimeError('Set DIAGRAM_FONT to a Chinese-capable TTF/TTC font path.')


def render(d):
    W,H=1600,d.height
    im=Image.new('RGB',(W,H),'white'); draw=ImageDraw.Draw(im)
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">',
         f'<title id="title">{escape(d.title)}</title><desc id="desc">{escape(d.subtitle)}</desc>',
         '<rect width="100%" height="100%" fill="white"/>']
    def rect(x,y,w,h,fill,stroke=None,r=12,width=2):
        draw.rounded_rectangle((x,y,x+w,y+h),radius=r,fill=fill,outline=stroke,width=width)
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke or "none"}" stroke-width="{width}"/>')
    def text(x,y,value,size=26,bold=False,color='#243247',max_width=None):
        f=font(size,bold)
        if max_width is not None and draw.textlength(value,font=f)>max_width:
            raise ValueError(f'{d.key}: text exceeds box width: {value}')
        draw.text((x,y),value,font=f,fill=color,anchor='lt')
        svg.append(f'<text x="{x}" y="{y+size*.9}" font-family="Microsoft YaHei, Noto Sans CJK SC, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{escape(value)}</text>')
    text(70,43,d.title,44,True,max_width=1460)
    text(70,113,d.subtitle,25,color='#526175',max_width=1460)
    for g in d.groups:
        fill,color=COLORS[g['tone']]
        rect(g['x'],g['y'],g['w'],g['h'],'#fafbfd','#dbe2eb',16)
        text(g['x']+25,g['y']+22,g['title'],26,True,color,max_width=g['w']-50)
    for e in d.edges:
        pts=e['points']; color='#718197'
        if e['dashed']:
            for p,q in zip(pts,pts[1:]):
                dist=math.dist(p,q)
                if not dist:continue
                for t in range(0,int(dist),16):
                    a=t/dist;b=min(t+9,dist)/dist
                    draw.line([(p[0]+(q[0]-p[0])*a,p[1]+(q[1]-p[1])*a),
                               (p[0]+(q[0]-p[0])*b,p[1]+(q[1]-p[1])*b)],fill=color,width=3)
        else: draw.line(pts,fill=color,width=3)
        # Last distinct segment sets arrow orientation.
        end=pts[-1];prev=next(p for p in reversed(pts[:-1]) if p!=end)
        a=math.atan2(end[1]-prev[1],end[0]-prev[0])
        arrow=[end,(end[0]-13*math.cos(a)+6*math.sin(a),end[1]-13*math.sin(a)-6*math.cos(a)),
                    (end[0]-13*math.cos(a)-6*math.sin(a),end[1]-13*math.sin(a)+6*math.cos(a))]
        draw.polygon(arrow,fill=color)
        svg.append(f'<polyline points="{" ".join(f"{x},{y}" for x,y in pts)}" fill="none" stroke="{color}" stroke-width="3"'+(' stroke-dasharray="9 7"' if e['dashed'] else '')+'/>')
        svg.append(f'<polygon points="{" ".join(f"{x},{y}" for x,y in arrow)}" fill="{color}"/>')
        if e['label']:
            p,q=pts[0],pts[-1]
            label=e['label'];tw=draw.textlength(label,font=font(21))
            x=(p[0]+q[0])/2-tw/2;y=(p[1]+q[1])/2-15
            if p[1]==q[1] and tw+10>abs(p[0]-q[0]):
                y=min(d.nodes[e['a']]['y'],d.nodes[e['b']]['y'])-32
            rect(x-5,y-3,tw+10,29,'white',None,3)
            text(x,y,label,21,color='#526175')
    for n in d.nodes.values():
        fill,color=COLORS[n['tone']]
        x,y,w,h=n['x'],n['y'],n['w'],n['h']
        rect(x,y,w,h,fill,color)
        title_size=28 if w>400 else 26
        while title_size>22 and draw.textlength(n['title'],font=font(title_size,True))>w-44:
            title_size-=1
        text(x+22,y+20,n['title'],title_size,True,color,max_width=w-44)
        for j,line in enumerate(n['lines']):
            ty=y+58+j*34
            if ty+24>y+h-8:
                raise ValueError(f'{d.key}: text exceeds box height: {n["title"]}')
            text(x+22,ty,line,24,max_width=w-44)
    if d.note:
        rect(65,H-77,1470,50,'#f4f6f9',None,7)
        text(82,H-64,d.note,22,color='#526175',max_width=1436)
    svg.append('</svg>')
    ASSETS.mkdir(parents=True,exist_ok=True)
    (ASSETS/(d.key+'.svg')).write_text('\n'.join(svg)+'\n',encoding='utf-8',newline='\n')
    im.save(ASSETS/(d.key+'.png'),optimize=True)


if __name__=='__main__':
    for d in DIAGRAMS:
        render(d)
        print(d.key)
    specs=[dict(id=d.key,title=d.title,subtitle=d.subtitle,note=d.note,height=d.height,
                source='SKILL.md' if d.key=='embeddedskills' else d.key+'/GUIDE.md',
                nodes=d.nodes,edges=d.edges,groups=d.groups) for d in DIAGRAMS]
    (Path(__file__).parent/'specs.json').write_text(json.dumps(specs,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
