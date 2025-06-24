import re
import argparse
from collections import defaultdict


def parse_logs(input_file, output_system, output_other):
    block_pattern = re.compile(r'<\|im_start\|>(system).*?<\|im_end\|>', re.DOTALL)
    #log_entries = defaultdict(lambda: {"system": [], "other": []})
    log_entries = {"system": [], "other": []}

    lines_cnt = 0

    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.replace("\n", "")
            #print("[DEBUG]{}".format(type(line)))
            if len(line) < 1:
                continue
            lines_cnt = lines_cnt + 1
            system_block = ""
            line_other = ""
            line_sys = ""
            for block in block_pattern.finditer(line):
                block_type = block.group(1)
                block_content = block.group(0)
                if block_type == "system":
                    system_block = block_content
                
            if system_block == "":
                line_other = line
            else:
                line_other = line.replace(system_block, "")
                p = line.find(system_block)
                line_sys = line[0:p + len(system_block)]
            if line_sys != "":
                log_entries["system"].append(line_sys)
            log_entries["other"].append(line_other)
    
    print("{} >= (o){} > (s){}".format(lines_cnt,  len(log_entries["other"]), len(log_entries["system"])))

    with open(output_system, 'w', encoding='utf-8') as f_sys, \
         open(output_other, 'w', encoding='utf-8') as f_other:
        for k in log_entries:
            contextes_ = log_entries[k]
            if k == "other":
                for c in contextes_:
                    f_other.write(f"{c}\n")
            else:
                for c in contextes_:
                    f_sys.write(f"{c}\n")
    print("FINISHED.")



def parse_logs_less_timestamp(input_file, output_system, output_other):
    # 正则匹配时间戳（格式如 "INFO 06-23 14:21:29.225"）
    timestamp_pattern = re.compile(r'^(INFO \d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})')
    # 正则匹配所有 <|im_start|> 到 <|im_end|> 的块
    block_pattern = re.compile(r'<\|im_start\|>(system|user|assistant).*?<\|im_end\|>', re.DOTALL)

    # 按时间戳分类存储内容
    log_entries = defaultdict(lambda: {"system": [], "other": []})

    current_timestamp = None

    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            # 提取时间戳
            timestamp_match = timestamp_pattern.match(line)
            if timestamp_match:
                current_timestamp = timestamp_match.group(1)

            # 跳过无时间戳的行（如多行块的后续行）
            if not current_timestamp:
                continue

            # 查找所有块
            for block in block_pattern.finditer(line):
                block_type = block.group(1)
                block_content = block.group(0)
                if block_type == "system":
                    log_entries[current_timestamp]["system"].append(block_content)
                else:
                    log_entries[current_timestamp]["other"].append(block_content)

    # 写入输出文件
    with open(output_system, 'w', encoding='utf-8') as f_sys, \
         open(output_other, 'w', encoding='utf-8') as f_other:
        for timestamp, blocks in log_entries.items():
            for sys_block in blocks["system"]:
                f_sys.write(f"{timestamp} {sys_block}\n")
            for other_block in blocks["other"]:
                f_other.write(f"{timestamp} {other_block}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Split log into system blocks (b.log) and other blocks (c.log).')
    parser.add_argument('input_file', help='Input log file (e.g., a.log)')
    parser.add_argument('output_system', help='Output file for system blocks (e.g., b.log)')
    parser.add_argument('output_other', help='Output file for other blocks (e.g., c.log)')
    args = parser.parse_args()

    parse_logs(args.input_file, args.output_system, args.output_other)
    print(f"System blocks saved to {args.output_system}")
    print(f"Other blocks saved to {args.output_other}")
