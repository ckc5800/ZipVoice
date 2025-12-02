import argparse
import numpy as np
import tritonclient.http as httpclient
from scipy.io.wavfile import write

def verify_health(url):
    try:
        client = httpclient.InferenceServerClient(url=url)
        if client.is_server_live():
            print("Server is live.")
        else:
            print("Server is NOT live.")
            return False
        
        if client.is_server_ready():
            print("Server is ready.")
        else:
            print("Server is NOT ready.")
            return False
            
        if client.is_model_ready("zipvoice_dialog"):
            print("Model 'zipvoice_dialog' is ready.")
        else:
            print("Model 'zipvoice_dialog' is NOT ready.")
            return False
            
        return True
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def verify_inference(url, text, output_file):
    try:
        client = httpclient.InferenceServerClient(url=url)
        
        inputs = []
        inputs.append(httpclient.InferInput("target_text", [1], "BYTES"))
        inputs.append(httpclient.InferInput("reference_text", [1], "BYTES"))
        
        # Dummy reference text/audio for now as we are not using speaker cache in this simple test
        # or we can use the defaults if the model handles it.
        # Based on pytriton_server.py logic:
        # inputs=[
        #     Tensor(name="reference_text", dtype=np.object_, shape=(1,)),
        #     Tensor(name="target_text", dtype=np.object_, shape=(1,)),
        #     Tensor(name="reference_wav", dtype=np.float32, shape=(-1,), optional=True),
        #     Tensor(name="reference_wav_len", dtype=np.int32, shape=(1,), optional=True),
        # ],
        
        inputs[0].set_data_from_numpy(np.array([text.encode("utf-8")], dtype=np.object_))
        inputs[1].set_data_from_numpy(np.array(["dummy reference".encode("utf-8")], dtype=np.object_))
        
        outputs = []
        outputs.append(httpclient.InferRequestedOutput("waveform"))
        
        print(f"Sending inference request for text: '{text}'")
        response = client.infer("zipvoice_dialog", inputs, outputs=outputs)
        
        waveform = response.as_numpy("waveform")
        print(f"Received waveform shape: {waveform.shape}")
        
        # Save to file
        # Assuming 24kHz as per pytriton_server.py default
        write(output_file, 24000, waveform.squeeze())
        print(f"Saved audio to {output_file}")
        return True
        
    except Exception as e:
        print(f"Inference failed: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", type=str, default="localhost:8000", help="Triton server URL")
    parser.add_argument("--text", type=str, default="안녕하세요, 테스트입니다.", help="Text to synthesize")
    parser.add_argument("--output", type=str, default="verify_output.wav", help="Output audio file")
    args = parser.parse_args()
    
    print("Verifying Triton Server Health...")
    if verify_health(args.url):
        print("\nVerifying Inference...")
        verify_inference(args.url, args.text, args.output)
    else:
        print("\nSkipping inference verification due to health check failure.")
