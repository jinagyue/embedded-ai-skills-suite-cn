from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
if len(sys.argv) > 1 and sys.argv[1] == 'build':
    print('build ok')
else:
    print((HERE / 'hardfault.log').read_text(encoding='utf-8'))
    print((HERE / 'freertos.log').read_text(encoding='utf-8'))
