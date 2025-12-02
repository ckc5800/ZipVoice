"""
설정 시스템 테스트
"""
from runtime.config_loader import load_config, get_api_config, get_triton_config, get_logging_config

def test_config_load():
    """설정 파일 로드 테스트"""
    print("\n=== 설정 파일 로드 테스트 ===")
    
    try:
        config = load_config()
        print("✓ 설정 파일 로드 성공")
        
        # API 설정
        api_config = get_api_config(config)
        print(f"\n[API 설정]")
        for key, value in api_config.items():
            print(f"  {key}: {value}")
        
        # Triton 설정
        triton_config = get_triton_config(config)
        print(f"\n[Triton 설정]")
        for key, value in triton_config.items():
            print(f"  {key}: {value}")
        
        # 로깅 설정
        logging_config = get_logging_config(config)
        print(f"\n[로깅 설정]")
        for key, value in logging_config.items():
            print(f"  {key}: {value}")
        
        # 추론 설정
        print(f"\n[추론 설정]")
        print(f"  model_dir: {config.get('inference.model_dir')}")
        print(f"  checkpoint_name: {config.get('inference.checkpoint_name')}")
        print(f"  num_steps: {config.get('inference.num_steps')}")
        
        return True
        
    except Exception as e:
        print(f"✗ 설정 로드 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_env_override():
    """환경 변수 오버라이드 테스트"""
    print("\n=== 환경 변수 오버라이드 테스트 ===")
    
    import os
    
    # 환경 변수 설정
    os.environ['ZIPVOICE_API_PORT'] = '9000'
    os.environ['ZIPVOICE_LOGGING_LEVEL'] = 'DEBUG'
    
    try:
        config = load_config()
        api_config = get_api_config(config)
        logging_config = get_logging_config(config)
        
        assert api_config['port'] == 9000, f"Expected 9000, got {api_config['port']}"
        assert logging_config['level'] == 'DEBUG', f"Expected DEBUG, got {logging_config['level']}"
        
        print(f"✓ 환경 변수 오버라이드 성공")
        print(f"  API port: {api_config['port']} (from env)")
        print(f"  Log level: {logging_config['level']} (from env)")
        
        # 환경 변수 정리
        del os.environ['ZIPVOICE_API_PORT']
        del os.environ['ZIPVOICE_LOGGING_LEVEL']
        
        return True
        
    except Exception as e:
        print(f"✗ 환경 변수 오버라이드 실패: {e}")
        return False

if __name__ == "__main__":
    results = []
    
    results.append(("설정 로드", test_config_load()))
    results.append(("환경 변수 오버라이드", test_env_override()))
    
    print("\n" + "="*50)
    print("테스트 결과 요약")
    print("="*50)
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\n총 {total}개 테스트 중 {passed}개 성공")
