import os
from pathlib import Path
import sys

def main():
    root_dir = Path(__file__).resolve().parent.parent
    dist_dir = root_dir / "dist" / "SnapSight"
    
    if not dist_dir.exists():
        print(f"FAIL: Distribution directory {dist_dir} does not exist.")
        sys.exit(1)
        
    print(f"Validating distribution at {dist_dir}...")
    
    # Check for expected core files
    expected_files = [
        "SnapSight.exe",
    ]
    
    for f in expected_files:
        if not (dist_dir / f).exists():
            print(f"FAIL: Expected file {f} missing from distribution.")
            sys.exit(1)
            
    # PROHIBITED FILES - Must not be bundled
    prohibited_extensions = [
        ".gguf", 
        ".onnx", 
        ".env", 
        ".log", 
        ".png", 
        ".jpg"
    ]
    
    # We walk the ENTIRE dist_dir EXCEPT the external models junction we made for testing
    models_junction = dist_dir / "models"
    
    for current_dir, dirs, files in os.walk(dist_dir):
        # Skip the models junction for validation
        if Path(current_dir) == models_junction:
            continue
            
        for file in files:
            p = Path(file)
            if p.suffix.lower() in prohibited_extensions:
                print(f"FAIL: Prohibited file found in bundle: {Path(current_dir) / file}")
                sys.exit(1)
                
            if p.name.lower() in ["api_keys.json", "secrets.json", ".env"]:
                print(f"FAIL: Prohibited secret file found: {Path(current_dir) / file}")
                sys.exit(1)
                
    print("Release validation PASSED: No prohibited models, secrets, or captures found in bundle.")

if __name__ == "__main__":
    main()
