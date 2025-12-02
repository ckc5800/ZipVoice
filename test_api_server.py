"""
FastAPI 서버 테스트 스크립트
"""
import requests
import base64
from pathlib import Path

# 서버 URL
API_URL = "http://localhost:8080"

def test_health():
    """헬스 체크 테스트"""
    print("\n=== 헬스 체크 테스트 ===")
    response = requests.get(f"{API_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_tts_file_upload():
    """파일 업로드 방식 TTS 테스트"""
    print("\n=== TTS 파일 업로드 테스트 ===")
    
    # 테스트용 참조 오디오
    reference_audio_path = Path("assets/SPK066KBSCU021F003.wav")
    
    if not reference_audio_path.exists():
        print(f"참조 오디오 파일이 없습니다: {reference_audio_path}")
        return False
    
    with open(reference_audio_path, "rb") as f:
        files = {"reference_audio": f}
        data = {
            "text": "안녕하세요, FastAPI 테스트입니다.",
            "reference_text": "브란덴부르크 주에서도 서식하며 개체수를 늘려가고 있습니다"
        }
        
        response = requests.post(f"{API_URL}/tts", files=files, data=data)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        # 결과 저장
        output_path = Path("test_output_api.wav")
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"오디오 저장 완료: {output_path}")
        print(f"파일 크기: {len(response.content)} bytes")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_tts_json():
    """JSON 방식 TTS 테스트"""
    print("\n=== TTS JSON 테스트 ===")
    
    reference_audio_path = Path("assets/SPK066KBSCU021F003.wav")
    
    if not reference_audio_path.exists():
        print(f"참조 오디오 파일이 없습니다: {reference_audio_path}")
        return False
    
    # Base64 인코딩
    with open(reference_audio_path, "rb") as f:
        audio_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    data = {
        "text": "JSON 방식 테스트입니다.",
        "reference_text": "브란덴부르크 주에서도 서식하며 개체수를 늘려가고 있습니다",
        "reference_audio_base64": audio_base64
    }
    
    response = requests.post(f"{API_URL}/tts/json", json=data)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Sample Rate: {result['sample_rate']}")
        print(f"Duration: {result['duration_seconds']:.2f}s")
        print(f"Request ID: {result['request_id']}")
        
        # Base64 디코딩 후 저장
        audio_bytes = base64.b64decode(result['audio_base64'])
        output_path = Path("test_output_api_json.wav")
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
        print(f"오디오 저장 완료: {output_path}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def main():
    """메인 테스트 함수"""
    print("FastAPI 서버 테스트 시작")
    print("주의: Triton 서버가 먼저 실행되어 있어야 합니다!")
    
    results = []
    
    # 헬스 체크
    results.append(("Health Check", test_health()))
    
    # TTS 테스트
    results.append(("TTS File Upload", test_tts_file_upload()))
    results.append(("TTS JSON", test_tts_json()))
    
    # 결과 요약
    print("\n" + "="*50)
    print("테스트 결과 요약")
    print("="*50)
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\n총 {total}개 테스트 중 {passed}개 성공")

if __name__ == "__main__":
    main()
