"""
추론 코드의 import를 검증하는 스크립트
"""
import sys
import importlib.util
from pathlib import Path

def check_imports(file_path):
    """파일의 import가 정상인지 확인"""
    try:
        spec = importlib.util.spec_from_file_location("module", file_path)
        if spec is None:
            return False, f"Failed to load spec for {file_path}"
        
        module = importlib.util.module_from_spec(spec)
        sys.modules["module"] = module
        spec.loader.exec_module(module)
        return True, f"✓ {file_path.name}"
    except Exception as e:
        return False, f"✗ {file_path.name}: {str(e)}"

def main():
    base_dir = Path("D:/12-02")
    
    # 검증할 추론 파일들
    inference_files = [
        # 모델 정의
        base_dir / "zipvoice/models/zipvoice_dialog.py",
        base_dir / "zipvoice/models/zipvoice.py",
        base_dir / "zipvoice/models/zipvoice_distill.py",
        
        # 토크나이저
        base_dir / "zipvoice/tokenizer/tokenizer.py",
        
        # 유틸리티
        base_dir / "zipvoice/utils/checkpoint.py",
        base_dir / "zipvoice/utils/feature.py",
        base_dir / "zipvoice/utils/infer.py",
        
        # 추론 스크립트
        base_dir / "zipvoice/bin/infer_zipvoice_dialog.py",
        base_dir / "zipvoice/bin/infer_zipvoice.py",
        
        # 서빙
        base_dir / "runtime/nvidia_triton/pytriton_server.py",
    ]
    
    results = []
    for file_path in inference_files:
        if not file_path.exists():
            results.append((False, f"✗ {file_path.name}: 파일이 존재하지 않습니다"))
            continue
        
        success, message = check_imports(file_path)
        results.append((success, message))
    
    # 결과 출력
    print("\n=== 추론 코드 Import 검증 결과 ===\n")
    success_count = 0
    for success, message in results:
        print(message)
        if success:
            success_count += 1
    
    print(f"\n총 {len(results)}개 파일 중 {success_count}개 성공")
    
    if success_count == len(results):
        print("\n✓ 모든 추론 코드가 정상적으로 import됩니다!")
        return 0
    else:
        print("\n✗ 일부 파일에서 import 에러가 발생했습니다.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
