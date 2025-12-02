"""
FastAPI 기반 TTS REST API 서버

Triton 서버를 백엔드로 사용하는 사용자 친화적인 REST API를 제공합니다.
"""
import base64
import io
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf
import tritonclient.http as httpclient
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Request
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel, Field

from runtime.logging_config import setup_logging, get_logger
from runtime.config_loader import load_config, get_api_config, get_logging_config

# 설정 로드
config = load_config()
api_config = get_api_config(config)
logging_config = get_logging_config(config)

# 로깅 설정
setup_logging(
    log_dir=logging_config['log_dir'],
    log_level=logging_config['level']
)
logger = get_logger(__name__)


# Triton 클라이언트 전역 변수
triton_client: Optional[httpclient.InferenceServerClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 이벤트"""
    global triton_client
    
    # 시작 시
    logger.info("FastAPI 서버 시작 중...")
    try:
        triton_url = api_config['triton_url']
        triton_client = httpclient.InferenceServerClient(url=triton_url)
        model_name = config.get('triton.model_name')
        if triton_client.is_server_live() and triton_client.is_model_ready(model_name):
            logger.info("Triton 서버 연결 성공")
        else:
            logger.error("Triton 서버 또는 모델이 준비되지 않음")
    except Exception as e:
        logger.error(f"Triton 서버 연결 실패: {e}")
        triton_client = None
    
    yield
    
    # 종료 시
    logger.info("FastAPI 서버 종료")


app = FastAPI(
    title="ZipVoice TTS API",
    description="Text-to-Speech API using ZipVoice model",
    version="1.0.0",
    lifespan=lifespan
)


class TTSRequest(BaseModel):
    """TTS 요청 모델"""
    text: str = Field(..., description="생성할 텍스트")
    reference_text: str = Field(..., description="참조 오디오의 텍스트")
    reference_audio_base64: Optional[str] = Field(None, description="참조 오디오 (base64 인코딩)")


class HealthResponse(BaseModel):
    """헬스 체크 응답"""
    status: str
    triton_connected: bool
    model_ready: bool


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """모든 요청/응답 로깅 미들웨어"""
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    # 요청 로깅
    logger.info(
        f"요청 시작: {request.method} {request.url.path}",
        extra={"request_id": request_id}
    )
    
    # 요청 처리
    try:
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        
        # 응답 로깅
        logger.info(
            f"요청 완료: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "request_id": request_id,
                "duration_ms": round(duration_ms, 2),
                "status_code": response.status_code
            }
        )
        
        # 응답 헤더에 요청 ID 추가
        response.headers["X-Request-ID"] = request_id
        return response
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(
            f"요청 실패: {request.method} {request.url.path} - {str(e)}",
            extra={
                "request_id": request_id,
                "duration_ms": round(duration_ms, 2)
            },
            exc_info=True
        )
        raise


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스 체크 엔드포인트"""
    triton_connected = False
    model_ready = False
    
    if triton_client:
        try:
            triton_connected = triton_client.is_server_live()
            model_ready = triton_client.is_model_ready(config.get('triton.model_name'))
        except Exception as e:
            logger.warning(f"헬스 체크 실패: {e}")
    
    status = "healthy" if (triton_connected and model_ready) else "unhealthy"
    
    return HealthResponse(
        status=status,
        triton_connected=triton_connected,
        model_ready=model_ready
    )


@app.post("/tts")
async def text_to_speech(
    text: str = Form(..., description="생성할 텍스트"),
    reference_text: str = Form(..., description="참조 오디오의 텍스트"),
    reference_audio: UploadFile = File(..., description="참조 오디오 파일 (WAV)")
):
    """
    Text-to-Speech 생성
    
    Args:
        text: 생성할 텍스트
        reference_text: 참조 오디오의 텍스트
        reference_audio: 참조 오디오 파일 (WAV, 16kHz 권장)
    
    Returns:
        생성된 오디오 파일 (WAV)
    """
    request_id = str(uuid.uuid4())[:8]
    logger.info(f"TTS 요청: text='{text[:50]}...', ref_text='{reference_text[:50]}...'", extra={"request_id": request_id})
    
    if not triton_client:
        logger.error("Triton 클라이언트가 초기화되지 않음", extra={"request_id": request_id})
        raise HTTPException(status_code=503, detail="Triton 서버에 연결할 수 없습니다")
    
    try:
        # 참조 오디오 로드
        audio_bytes = await reference_audio.read()
        audio_data, sample_rate = sf.read(io.BytesIO(audio_bytes))
        
        logger.info(
            f"참조 오디오 로드 완료: {len(audio_data)} samples, {sample_rate}Hz",
            extra={"request_id": request_id}
        )
        
        # Triton 입력 준비
        inputs = []
        inputs.append(httpclient.InferInput("reference_text", [1], "BYTES"))
        inputs.append(httpclient.InferInput("target_text", [1], "BYTES"))
        inputs.append(httpclient.InferInput("reference_wav", [1, len(audio_data)], "FP32"))
        inputs.append(httpclient.InferInput("reference_wav_len", [1, 1], "INT32"))
        
        inputs[0].set_data_from_numpy(np.array([reference_text.encode("utf-8")], dtype=np.object_))
        inputs[1].set_data_from_numpy(np.array([text.encode("utf-8")], dtype=np.object_))
        inputs[2].set_data_from_numpy(audio_data.astype(np.float32).reshape(1, -1))
        inputs[3].set_data_from_numpy(np.array([[len(audio_data)]], dtype=np.int32))
        
        # 출력 설정
        outputs = []
        outputs.append(httpclient.InferRequestedOutput("waveform"))
        
        # Triton 추론
        logger.info("Triton 추론 시작", extra={"request_id": request_id})
        start_inference = time.time()
        
        response = triton_client.infer(config.get('triton.model_name'), inputs, outputs=outputs)
        
        inference_time = (time.time() - start_inference) * 1000
        logger.info(
            f"Triton 추론 완료: {inference_time:.2f}ms",
            extra={"request_id": request_id, "duration_ms": inference_time}
        )
        
        # 결과 추출
        waveform = response.as_numpy("waveform").squeeze()
        
        # 패딩 제거 (-1.0은 패딩값)
        valid_idx = np.where(waveform != -1.0)[0]
        if len(valid_idx) > 0:
            waveform = waveform[:valid_idx[-1] + 1]
        
        logger.info(
            f"오디오 생성 완료: {len(waveform)} samples",
            extra={"request_id": request_id}
        )
        
        # WAV 파일로 변환
        output_buffer = io.BytesIO()
        sf.write(output_buffer, waveform, 24000, format='WAV')
        output_buffer.seek(0)
        
        return Response(
            content=output_buffer.read(),
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename=generated_{request_id}.wav",
                "X-Request-ID": request_id
            }
        )
        
    except Exception as e:
        logger.error(f"TTS 생성 실패: {e}", extra={"request_id": request_id}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"TTS 생성 중 오류 발생: {str(e)}")


@app.post("/tts/json")
async def text_to_speech_json(request: TTSRequest):
    """
    JSON 기반 TTS 생성 (base64 인코딩된 오디오 사용)
    
    Args:
        request: TTS 요청 (JSON)
    
    Returns:
        생성된 오디오 (base64 인코딩)
    """
    request_id = str(uuid.uuid4())[:8]
    logger.info(f"TTS JSON 요청: text='{request.text[:50]}...'", extra={"request_id": request_id})
    
    if not triton_client:
        raise HTTPException(status_code=503, detail="Triton 서버에 연결할 수 없습니다")
    
    try:
        # Base64 디코딩
        if request.reference_audio_base64:
            audio_bytes = base64.b64decode(request.reference_audio_base64)
        else:
            raise HTTPException(status_code=400, detail="reference_audio_base64가 필요합니다")
        
        # 오디오 로드
        audio_data, sample_rate = sf.read(io.BytesIO(audio_bytes))
        
        # Triton 추론 (위와 동일한 로직)
        inputs = []
        inputs.append(httpclient.InferInput("reference_text", [1], "BYTES"))
        inputs.append(httpclient.InferInput("target_text", [1], "BYTES"))
        inputs.append(httpclient.InferInput("reference_wav", [1, len(audio_data)], "FP32"))
        inputs.append(httpclient.InferInput("reference_wav_len", [1, 1], "INT32"))
        
        inputs[0].set_data_from_numpy(np.array([request.reference_text.encode("utf-8")], dtype=np.object_))
        inputs[1].set_data_from_numpy(np.array([request.text.encode("utf-8")], dtype=np.object_))
        inputs[2].set_data_from_numpy(audio_data.astype(np.float32).reshape(1, -1))
        inputs[3].set_data_from_numpy(np.array([[len(audio_data)]], dtype=np.int32))
        
        outputs = [httpclient.InferRequestedOutput("waveform")]
        
        response = triton_client.infer("zipvoice_dialog", inputs, outputs=outputs)
        waveform = response.as_numpy("waveform").squeeze()
        
        # 패딩 제거
        valid_idx = np.where(waveform != -1.0)[0]
        if len(valid_idx) > 0:
            waveform = waveform[:valid_idx[-1] + 1]
        
        # WAV로 변환 후 base64 인코딩
        output_buffer = io.BytesIO()
        sf.write(output_buffer, waveform, 24000, format='WAV')
        output_buffer.seek(0)
        audio_base64 = base64.b64encode(output_buffer.read()).decode('utf-8')
        
        logger.info("TTS JSON 생성 완료", extra={"request_id": request_id})
        
        return JSONResponse(content={
            "audio_base64": audio_base64,
            "sample_rate": 24000,
            "duration_seconds": len(waveform) / 24000,
            "request_id": request_id
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS JSON 생성 실패: {e}", extra={"request_id": request_id}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"TTS 생성 중 오류 발생: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    logger.info("FastAPI 서버 시작...")
    uvicorn.run(
        "api_server:app",
        host=api_config['host'],
        port=api_config['port'],
        workers=api_config['workers'],
        reload=api_config['reload'],
        log_level="info",
        access_log=True
    )
