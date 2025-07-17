from modelscope import snapshot_download as snapshot_download_scp
from huggingface_hub import snapshot_download
import os

SAVE_PATH = "/home/leon/mount_point_c/LLM_models/"
MODEL_NAMES = ["Qwen/Qwen2.5-7B-Instruct"]
"""
MrezaPRZ/Qwen2.5-Coder-3B-grpo-llm_ex_syn_schema_ngram_250
qingy2024/Qwen2.5-0.5B-Instruct-Draft
"qingy2024/Qwen2.5-0.5B-Instruct-Draft"
"qingy2024/Qwen2.5-1.5B-Instruct-Draft",
"qingy2024/Qwen2.5-Coder-Draft-1.5B-Instruct",
"SmallDoge/Qwen2.5-14b-chain-of-draft25k",
"FrenzyBiscuit/Qwen2.5-QwQ-RP-Draft-v0.2-1.5B-AWQ",
"Vinitha2004/qwen2.5-coder-3b-instruct-awq-final-working_draft",
SmallDoge/Qwen2.5-14b-chain-of-draft25k
yuhuili/EAGLE-Qwen2-7B-Instruct
"""

def download_from_scope(_name, _path):

    print("Start Download file: {} TO  {}".format(_name, _path))
    model_dir = snapshot_download_scp(_name, cache_dir=_path)
    print("Finished           : {} TO  {}".format(_name, _path))
    
def download_from_hgf(_name, _path):
    save_sub_path = os.path.join(_path, _name) + "/"
    os.makedirs(save_sub_path)
    print("Start Download file: {} TO  {}".format(_name, save_sub_path))
    snapshot_download(_name, local_dir=save_sub_path) 
    #, cache_dir=save_sub_path export HF_HOME=
    print("Finished           : {} TO  {}".format(_name, save_sub_path))

for MODEL_NAME in MODEL_NAMES:
    try:
        # recall function || function ptr
        #download_from_hgf(MODEL_NAME, SAVE_PATH)
        download_from_scope(MODEL_NAME, SAVE_PATH)
    except:
        print("Error:{}".format(MODEL_NAME))
        continue
