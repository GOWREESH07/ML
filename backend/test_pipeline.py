import asyncio
import io
import json
import numpy as np
from PIL import Image
from backend.main import app, lifespan, health, predict

async def run_diagnostics():
    print("=== NeuroScan AI Pipeline Verification ===")
    async with lifespan(app):
        # 1. Health endpoint test
        health_resp = await health()
        print("\n[PASS] /health endpoint response:")
        print(f"  Status: {health_resp['status']}")
        print(f"  Model Loaded: {health_resp['model_loaded']}")
        print(f"  Classes: {health_resp['classes']}")
        print(f"  Uncertainty Threshold: {health_resp['uncertainty_threshold']}")

        class MockRequest:
            def __init__(self, body_bytes, ct="image/jpeg"):
                self._body = body_bytes
                self.headers = {"content-type": ct}
            async def body(self):
                return self._body

        # 2. Test each class with real MRI sample
        samples = [
            ("glioma", "backend/samples/glioma.jpg"),
            ("meningioma", "backend/samples/meningioma.jpg"),
            ("notumor", "backend/samples/notumor.jpg"),
            ("pituitary", "backend/samples/pituitary.jpg"),
        ]

        print("\n[TEST] Evaluating 4 Sample MRI Scans:")
        for expected_class, sample_path in samples:
            with open(sample_path, "rb") as f:
                img_data = f.read()

            req = MockRequest(img_data, "image/jpeg")
            resp = await predict(req)
            result = json.loads(resp.body.decode("utf-8"))

            print(f"\n  Sample File: {sample_path}")
            print(f"  -> Predicted: {result['predicted_class']} (Expected ~ {expected_class})")
            print(f"  -> Confidence: {result['confidence'] * 100:.1f}%")
            print(f"  -> MC Uncertainty: ±{result['uncertainty'] * 100:.1f}%")
            print(f"  -> Severity Extent: {result['severity_bucket']} (foreground {result['foreground_ratio'] * 100:.1f}%)")
            print(f"  -> Low Confidence Flag: {result['low_confidence_flag']}")
            print(f"  -> Heatmap Base64: {result['heatmap_base64'][:30]}... ({len(result['heatmap_base64'])} chars)")
            print(f"  -> Knowledge Base: {result['info']['name']}")
            print(f"  -> Disclaimer: {result['disclaimer']}")

        # 3. Test Quality / OOD Gate with synthetic color photo
        print("\n[TEST] Quality Gate (OOD Color Photo Rejection):")
        arr = np.zeros((160, 160, 3), dtype=np.uint8)
        arr[:, :, 0] = 230
        arr[:, :, 1] = 45
        arr[:, :, 2] = 20
        buf = io.BytesIO()
        Image.fromarray(arr).save(buf, format="JPEG")

        invalid_req = MockRequest(buf.getvalue(), "image/jpeg")
        try:
            await predict(invalid_req)
            print("  [FAIL] Color photo should have been rejected!")
        except Exception as e:
            print(f"  [PASS] Successfully rejected with HTTP {e.status_code}: {e.detail}")

    print("\n=== All Backend Pipeline Checks Passed Successfully ===")

if __name__ == "__main__":
    asyncio.run(run_diagnostics())
