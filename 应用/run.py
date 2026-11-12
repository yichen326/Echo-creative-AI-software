# -*- coding: utf-8 -*-
"""回声 Echo 启动入口。

    python run.py            # 默认 8771
    set ECHO_PORT=9000 && python run.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "vendor"))
sys.path.insert(0, HERE)

MISSING_HINT = """
缺少依赖：{mod}

本项目只把 Web 框架与分词做成外部依赖，诊断引擎本身纯标准库。
安装方式（国内建议走镜像）：

    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

装好后重新运行 python run.py
"""

for mod in ("fastapi", "uvicorn"):
    try:
        __import__(mod)
    except ImportError:
        print(MISSING_HINT.format(mod=mod))
        sys.exit(1)

from server import app  # noqa: E402

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("ECHO_PORT", "8771"))
    print("\n  回声 Echo  ->  http://127.0.0.1:%d\n" % port)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
