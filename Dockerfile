FROM nvcr.io/nvidia/pytorch:24.11-py3

# 작업 디렉토리
WORKDIR /workspace

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    git \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 복사 및 설치
COPY requirements_docker.txt /workspace/
# piper_phonemize는 별도 인덱스에서 설치
RUN pip install --no-cache-dir piper_phonemize -f https://k2-fsa.github.io/icefall/piper_phonemize.html
RUN pip install --no-cache-dir -r requirements_docker.txt

# nvidia-pytriton 설치
RUN pip install --no-cache-dir nvidia-pytriton==0.5.11

# 소스 코드만 복사 (볼륨 마운트할 파일 제외)
COPY zipvoice/ /workspace/zipvoice/
COPY runtime/ /workspace/runtime/

# NOTE: 다음 파일들은 볼륨 마운트로 제공됨
# - config/ (설정 파일)
# - espeak/ (모델 & 토크나이저)
# - logs/ (로그 파일)
# - assets/ (참조 오디오)

# 환경 변수
ENV PYTHONPATH=/workspace
ENV PYTHONIOENCODING=utf-8

# 포트 노출
EXPOSE 8000 8001 8002 8080

# 기본 실행 명령 (docker-compose에서 오버라이드)
CMD ["python", "runtime/nvidia_triton/pytriton_server.py", \
    "--model_dir", "/workspace/espeak", \
    "--model_name", "zipvoice_dialog"]
