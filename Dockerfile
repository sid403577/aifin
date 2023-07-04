FROM python:3.8

MAINTAINER "chatGLM"

COPY . /chatGLM/

WORKDIR /chatGLM

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo "Asia/Shanghai" > /etc/timezone

RUN pip3 install -r requirements.txt -i https://pypi.mirrors.ustc.edu.cn/simple/ && rm -rf `pip3 cache dir`

CMD ["python","-u", "webui.py"]
