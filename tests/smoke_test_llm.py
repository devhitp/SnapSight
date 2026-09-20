"""
Real local LLM smoke test for Sprint 4 verification.
Requires the GGUF model at: models/Phi-3.5-mini-instruct-Q4_K_M.gguf
NOT committed to Git.
"""
import sys
import os
import time

# Resolve project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "Phi-3.5-mini-instruct-Q4_K_M.gguf")

def run_smoke_test():
    if not os.path.isfile(MODEL_PATH):
        print(f"SKIP: Model file not found at: {MODEL_PATH}")
        return False

    print(f"Model file: {MODEL_PATH}")
    print(f"Model size: {os.path.getsize(MODEL_PATH) / 1e9:.2f} GB")

    try:
        from llama_cpp import Llama
    except ImportError:
        print("SKIP: llama-cpp-python not installed.")
        return False

    print("\n--- Loading model (first call, cold start) ---")
    t_load_start = time.perf_counter()
    llm = Llama(
        model_path=MODEL_PATH,
        n_ctx=2048,
        n_threads=4,
        verbose=False,
    )
    load_ms = (time.perf_counter() - t_load_start) * 1000
    print(f"Model load time: {load_ms:.0f} ms ({load_ms/1000:.1f} s)")

    def ask(question, context, label):
        print(f"\n--- {label} ---")
        print(f"Question: {question}")
        prompt = (
            "<|system|>\n"
            "You are SnapSight, a helpful screen reading assistant. "
            "Answer questions using the screen text provided as reference data. "
            "Do not invent information not present in the context.<|end|>\n"
            f"<|user|>\n"
            f"--- BEGIN SCREEN TEXT ---\n{context}\n--- END SCREEN TEXT ---\n\n"
            f"Question: {question}<|end|>\n"
            "<|assistant|>\n"
        )
        t0 = time.perf_counter()
        response = llm(prompt, max_tokens=128, stop=["<|end|>", "<|user|>", "\n\n\n"], echo=False)
        gen_ms = (time.perf_counter() - t0) * 1000
        answer = response["choices"][0]["text"].strip()
        usage = response.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens")
        comp_tokens = usage.get("completion_tokens")

        print(f"Answer: {answer}")
        print(f"Generation time: {gen_ms:.0f} ms ({gen_ms/1000:.1f} s)")
        if prompt_tokens is not None:
            print(f"Prompt tokens: {prompt_tokens}")
        if comp_tokens is not None:
            print(f"Generated tokens: {comp_tokens}")
            if gen_ms > 0:
                tps = (comp_tokens / gen_ms) * 1000
                print(f"Tokens/sec: {tps:.1f}")
        return answer, gen_ms

    # First inference
    context1 = "SnapSight is a local screen intelligence application that analyzes captured screen content on the user's computer."
    answer1, gen1 = ask("What is SnapSight?", context1, "FIRST INFERENCE")

    # Second inference — verify model reuse (no reload)
    context2 = "SnapSight keeps screen data on the local computer."
    answer2, gen2 = ask("Where does SnapSight process screen data?", context2, "SECOND INFERENCE (model reuse)")

    print("\n--- SUMMARY ---")
    print(f"Model: Phi-3.5-mini-instruct-Q4_K_M.gguf")
    print(f"Runtime: llama-cpp-python 0.3.35 / llama.cpp")
    print(f"Acceleration: CPU (Intel i5-11400H)")
    print(f"Load time: {load_ms:.0f} ms")
    print(f"First generation: {gen1:.0f} ms")
    print(f"Second generation: {gen2:.0f} ms")
    print("\nSMOKE TEST COMPLETE")
    return True

if __name__ == "__main__":
    ok = run_smoke_test()
    sys.exit(0 if ok else 1)
