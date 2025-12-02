"""
설정 파일 로더 모듈

YAML 설정 파일을 읽고 환경 변수로 오버라이드를 지원합니다.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class Config:
    """설정 클래스"""
    
    def __init__(self, config_dict: Dict[str, Any]):
        self._config = config_dict
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        점 표기법으로 설정 값 가져오기
        예: config.get('api.port') -> 8080
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def __getitem__(self, key: str) -> Any:
        """딕셔너리 스타일 접근"""
        return self._config[key]
    
    def __contains__(self, key: str) -> bool:
        """in 연산자 지원"""
        return key in self._config


def load_config(config_path: Optional[str] = None) -> Config:
    """
    설정 파일 로드
    
    Args:
        config_path: 설정 파일 경로 (기본값: config/server_config.yaml)
    
    Returns:
        Config 객체
    """
    if config_path is None:
        # 기본 설정 파일 경로
        config_path = Path(__file__).parent.parent / "config" / "server_config.yaml"
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
    
    # YAML 파일 읽기
    with open(config_path, 'r', encoding='utf-8') as f:
        config_dict = yaml.safe_load(f)
    
    # 환경 변수로 오버라이드
    config_dict = _override_with_env(config_dict)
    
    return Config(config_dict)


def _override_with_env(config: Dict[str, Any], prefix: str = "ZIPVOICE") -> Dict[str, Any]:
    """
    환경 변수로 설정 오버라이드
    
    환경 변수 형식: ZIPVOICE_SECTION_KEY
    예: ZIPVOICE_API_PORT=9000 -> config['api']['port'] = 9000
    
    Args:
        config: 설정 딕셔너리
        prefix: 환경 변수 접두사
    
    Returns:
        오버라이드된 설정 딕셔너리
    """
    for section, values in config.items():
        if not isinstance(values, dict):
            continue
        
        for key, value in values.items():
            env_key = f"{prefix}_{section}_{key}".upper()
            env_value = os.getenv(env_key)
            
            if env_value is not None:
                # 타입 변환
                if isinstance(value, bool):
                    config[section][key] = env_value.lower() in ('true', '1', 'yes')
                elif isinstance(value, int):
                    config[section][key] = int(env_value)
                elif isinstance(value, float):
                    config[section][key] = float(env_value)
                else:
                    config[section][key] = env_value
    
    return config


def get_inference_config(config: Config) -> Dict[str, Any]:
    """추론 설정 추출"""
    return {
        'model_dir': config.get('inference.model_dir'),
        'checkpoint_name': config.get('inference.checkpoint_name'),
        'sampling_rate': config.get('inference.sampling_rate'),
        'target_rms': config.get('inference.target_rms'),
        'feat_scale': config.get('inference.feat_scale'),
        'speed': config.get('inference.speed'),
        't_shift': config.get('inference.t_shift'),
        'num_steps': config.get('inference.num_steps'),
        'guidance_scale': config.get('inference.guidance_scale'),
        'vocoder_model': config.get('inference.vocoder_model'),
    }


def get_triton_config(config: Config) -> Dict[str, Any]:
    """Triton 설정 추출"""
    return {
        'model_name': config.get('triton.model_name'),
        'http_port': config.get('triton.http_port'),
        'grpc_port': config.get('triton.grpc_port'),
        'metrics_port': config.get('triton.metrics_port'),
        'max_batch_size': config.get('triton.max_batch_size'),
        'max_queue_delay_ms': config.get('triton.max_queue_delay_ms'),
        'log_verbose': config.get('triton.log_verbose'),
        'trt_engine_path': config.get('triton.trt_engine_path'),
    }


def get_api_config(config: Config) -> Dict[str, Any]:
    """API 설정 추출"""
    return {
        'host': config.get('api.host'),
        'port': config.get('api.port'),
        'workers': config.get('api.workers'),
        'reload': config.get('api.reload'),
        'triton_url': config.get('api.triton_url'),
        'triton_timeout': config.get('api.triton_timeout'),
    }


def get_logging_config(config: Config) -> Dict[str, Any]:
    """로깅 설정 추출"""
    return {
        'level': config.get('logging.level'),
        'log_dir': config.get('logging.log_dir'),
        'max_file_size_mb': config.get('logging.max_file_size_mb'),
        'backup_count': config.get('logging.backup_count'),
        'json_format': config.get('logging.json_format'),
        'console_output': config.get('logging.console_output'),
    }
