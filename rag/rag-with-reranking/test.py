from pydantic import BaseModel , Field
from typing import List
import json

class Test(BaseModel):
    question:str = Field(description="Question for the evaluation")
    reference_answer:str = Field(description="Reference Answer/Golden truth answer for the question to evaluate")
    keywords:List[str] = Field(description="List of keywords that should occur in the generated answer")
    category:str = Field(description="Category of the question asked should be in temporal, numerical , direct_fact, relationship , holistic")

TEST_FILE = "test.jsonl"

def load_test_dataset(file_path: str = TEST_FILE) -> List[Test]:
    test_docs = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:                  
            line = line.strip()         
            if not line:                
                continue
            # print(line)
            single_json = json.loads(line)
            test_docs.append(Test(**single_json))
        print(len(test_docs))
    return test_docs