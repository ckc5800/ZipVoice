# WindowsPath 패치 수정 가이드

## 문제
Docker 컨테이너(Linux)에서 추론 실행 시 `NotImplementedError: cannot instantiate 'WindowsPath' on your system` 에러 발생.

## 원인
`zipvoice/bin/infer_zipvoice_dialog.py`의 47-51번째 줄에 있는 Windows 전용 pathlib 패치가 모든 OS에서 실행되고 있음.

## 수정 방법

### 파일 위치
`D:\12-02\zipvoice\bin\infer_zipvoice_dialog.py`

### 현재 코드 (47-51번째 줄)
```python
# Patch for pathlib on Windows
import pathlib
pathlib.PosixPath = pathlib.WindowsPath
```

### 수정 후
```python
# Patch for pathlib on Windows only  
import sys
import pathlib
if sys.platform == 'win32':
    pathlib.PosixPath = pathlib.WindowsPath
```

## 수정 후 다음 단계
1. 파일 저장
2. Docker 이미지 재빌드
3. 컨테이너 내부 추론 테스트
