# Docker 성능 최적화 가이드

## 주요 성능 설정

### 1. 공유 메모리 (Shared Memory)

**현재 설정**: `ipc: host`
- 호스트의 `/dev/shm` 사용 (가장 큰 크기)
- PyTorch DataLoader, 멀티프로세싱에 필수

**대안**:
```yaml
shm_size: '16gb'  # 특정 크기 지정
```

### 2. ulimit 설정

**메모리 잠금 (memlock)**:
```yaml
memlock:
  soft: -1   # 무제한
  hard: -1
```
- GPU 메모리 고정에 필요
- CUDA 성능 향상

**파일 디스크립터 (nofile)**:
```yaml
nofile:
  soft: 65536
  hard: 65536
```
- 동시 연결 처리 증가

### 3. 환경 변수 최적화

**PyTorch 스레드**:
```bash
OMP_NUM_THREADS=8      # CPU 코어 수에 맞게 조정
MKL_NUM_THREADS=8
```

**CUDA 최적화**:
```bash
CUDA_LAUNCH_BLOCKING=0  # 비동기 실행
```

### 4. 리소스 제한

**CPU & 메모리**:
```yaml
deploy:
  resources:
    limits:
      cpus: '8'
      memory: 32G
    reservations:
      cpus: '4'
      memory: 16G
```

**권장 설정** (하드웨어별):
- **RTX 5080 (16GB)**: CPU 8 cores, RAM 32GB
- **A100 (40GB)**: CPU 16 cores, RAM 64GB

### 5. 로깅 로테이션

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "100m"
    max-file: "5"
```
- 디스크 공간 절약
- 로그 파일 자동 정리

## 하드웨어별 권장 설정

### 소형 서버 (RTX 3090, 24GB)
```yaml
ipc: host
deploy:
  resources:
    limits:
      cpus: '8'
      memory: 24G
environment:
  - OMP_NUM_THREADS=4
```

### 중형 서버 (RTX 5080, 16GB)
```yaml
ipc: host
deploy:
  resources:
    limits:
      cpus: '8'
      memory: 32G
environment:
  - OMP_NUM_THREADS=8
```

### 대형 서버 (A100, 40GB+)
```yaml
ipc: host
deploy:
  resources:
    limits:
      cpus: '16'
      memory: 64G
environment:
  - OMP_NUM_THREADS=16
```

## 추가 최적화 팁

### 1. NVIDIA Persistence Mode
```bash
nvidia-smi -pm 1
```
- GPU 초기화 시간 단축

### 2. Docker 빌드 캐시
```bash
# 빌드 캐시 활용
docker build --cache-from zipvoice-triton:latest .
```

### 3. 멀티 스테이지 빌드
현재 Dockerfile은 단일 스테이지. 프로덕션 최적화를 위해 멀티 스테이지 고려.

### 4. 모니터링
- Prometheus: `http://localhost:7002/metrics`
- Docker stats: `docker stats zipvoice-triton`
- GPU 모니터링: `nvidia-smi -l 1`
