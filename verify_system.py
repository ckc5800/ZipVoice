"""
전체 시스템 검증 스크립트

추론 코드, API 서버, 의존성 등을 종합적으로 검증합니다.
"""
import sys
import importlib.util
from pathlib import Path

def test_imports():
    """핵심 모듈 import 테스트"""
    print("\n=== 핵심 모듈 Import 테스트 ===")
    
    modules = [
        ("zipvoice.models.zipvoice_dialog", "ZipVoiceDialog"),
        ("zipvoice.tokenizer.tokenizer", "EspeakTokenizer"),
        ("zipvoice.utils.checkpoint", "load_checkpoint"),
        ("zipvoice.utils.feature", "VocosFbank"),
        ("zipvoice.utils.infer", "rms_norm"),
    ]
    
    passed = 0
    for module_name, class_name in modules:
        try:
            module = importlib.import_module(module_name)
            getattr(module, class_name)
            print(f"✓ {module_name}.{class_name}")
            passed += 1
        except Exception as e:
            print(f"✗ {module_name}.{class_name}: {e}")
    
    print(f"\n결과: {passed}/{len(modules)} 성공")
    return passed == len(modules)


def test_api_server_imports():
    """API 서버 관련 import 테스트"""
    print("\n=== API 서버 Import 테스트 ===")
    
    modules = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "run"),
        ("soundfile", "read"),
    ]
    
    passed = 0
    for module_name, attr_name in modules:
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, attr_name):
                print(f"✓ {module_name}.{attr_name}")
                passed += 1
            else:
                print(f"✗ {module_name}.{attr_name}: 속성 없음")
        except ImportError as e:
            print(f"✗ {module_name}: 설치 필요 - {e}")
    
    print(f"\n결과: {passed}/{len(modules)} 성공")
    return passed == len(modules)


def test_file_structure():
    """파일 구조 검증"""
    print("\n=== 파일 구조 검증 ===")
    
    required_files = [
        "zipvoice/models/zipvoice_dialog.py",
        "zipvoice/tokenizer/tokenizer.py",
        "zipvoice/utils/checkpoint.py",
        "zipvoice/utils/feature.py",
        "zipvoice/bin/infer_zipvoice_dialog.py",
        "runtime/nvidia_triton/pytriton_server.py",
        "runtime/api_server.py",
        "runtime/logging_config.py",
        "requirements_inference.txt",
        "espeak/model.json",
        "espeak/tokens.txt",
    ]
    
    base_dir = Path("D:/12-02")
    passed = 0
    
    for file_path in required_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"✓ {file_path}")
            passed += 1
        else:
            print(f"✗ {file_path}: 파일 없음")
    
    print(f"\n결과: {passed}/{len(required_files)} 파일 존재")
    return passed == len(required_files)


def test_deleted_training_files():
    """학습 파일이 제대로 삭제되었는지 확인"""
    print("\n=== 학습 파일 삭제 확인 ===")
    
    should_not_exist = [
        "zipvoice/dataset",
        "zipvoice/eval",
        "egs",
        "zipvoice/bin/train_zipvoice.py",
        "zipvoice/bin/train_zipvoice_dialog.py",
        "zipvoice/bin/prepare_dataset.py",
    ]
    
    base_dir = Path("D:/12-02")
    passed = 0
    
    for file_path in should_not_exist:
        full_path = base_dir / file_path
        if not full_path.exists():
            print(f"✓ {file_path} 삭제됨")
            passed += 1
        else:
            print(f"✗ {file_path} 아직 존재함")
    
    print(f"\n결과: {passed}/{len(should_not_exist)} 파일 정리 완료")
    return passed == len(should_not_exist)


def test_api_server_syntax():
    """API 서버 파일 문법 검증"""
    print("\n=== API 서버 문법 검증 ===")
    
    files = [
        "runtime/api_server.py",
        "runtime/logging_config.py",
    ]
    
    base_dir = Path("D:/12-02")
    passed = 0
    
    for file_path in files:
        full_path = base_dir / file_path
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                compile(f.read(), full_path, 'exec')
            print(f"✓ {file_path}")
            passed += 1
        except SyntaxError as e:
            print(f"✗ {file_path}: 문법 오류 - {e}")
        except Exception as e:
            print(f"✗ {file_path}: {e}")
    
    print(f"\n결과: {passed}/{len(files)} 파일 문법 정상")
    return passed == len(files)


def main():
    """메인 검증 함수"""
    print("="*60)
    print("ZipVoice 전체 시스템 검증")
    print("="*60)
    
    results = []
    
    # 1. 파일 구조
    results.append(("파일 구조", test_file_structure()))
    
    # 2. 학습 파일 삭제 확인
    results.append(("학습 파일 정리", test_deleted_training_files()))
    
    # 3. 핵심 모듈 import
    results.append(("추론 모듈 Import", test_imports()))
    
    # 4. API 서버 import
    results.append(("API 서버 Import", test_api_server_imports()))
    
    # 5. API 서버 문법
    results.append(("API 서버 문법", test_api_server_syntax()))
    
    # 결과 요약
    print("\n" + "="*60)
    print("검증 결과 요약")
    print("="*60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {name}")
    
    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    
    print(f"\n총 {total}개 검증 항목 중 {passed_count}개 성공")
    
    if passed_count == total:
        print("\n✓ 모든 검증 통과! 시스템 정상입니다.")
        return 0
    else:
        print("\n✗ 일부 검증 실패. 위 결과를 확인하세요.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
