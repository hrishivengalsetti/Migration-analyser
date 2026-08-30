import os
import sys
from brain.interpreter import generate_narrative
from models import Evidence, ComparisonStatus

if __name__ == "__main__":
    if not os.environ.get("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY is required for the manual integration test.")
        sys.exit(1)
        
    print("Testing real Groq API integration...")
    result = generate_narrative(
        diff_summary={"added_files": 1},
        blast_radius_summary={"directly_affected": 0},
        execution_summary={"passed": 1, "failed": 0},
        evidence_data=[Evidence(symbol_id="dummy", file="dummy", comparison=ComparisonStatus.UNCHANGED, failing_tests=[], passing_tests=[], unverified_tests=[])]
    )
    print("\nResult:")
    print(result.model_dump_json(indent=2))
