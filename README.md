# 安装

## 环境检查

```shell
# 首先，确信你的机器安装了 Python 3.8 及以上版本
$ python --version
Python 3.8.13

# 如果低于这个版本，可使用conda安装环境
$ conda create -p /your_path/env_name python=3.8

# 激活环境
$ source activate /your_path/env_name
$ pip3 install --upgrade pip

# 关闭环境
$ source deactivate /your_path/env_name

# 删除环境
$ conda env remove -p  /your_path/env_name
```

## 项目依赖

```shell
# 拉取仓库
$ git clone https://github.com/sid403577/aifin.git

# 进入目录
$ cd aifin

# 安装依赖
$ pip install -r requirements.txt

# 根据需求运行 `api.py`, `cli_demo.py` 或 `webui.py`。
```