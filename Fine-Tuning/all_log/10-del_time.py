import json


def process_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as infile, \
            open(output_file, 'w', encoding='utf-8') as outfile:

        for line in infile:
            # 解析每行JSON
            try:
                data = json.loads(line.strip())
            except json.JSONDecodeError:
                continue

            # 删除顶层timestamp和session_id
            data.pop('timestamp', None)
            data.pop('session_id', None)

            # 处理assistant字段
            if 'assistant' in data:
                try:
                    assistant_data = json.loads(data['assistant'])
                    # 删除assistant内容中的timestamp和session_id
                    assistant_data.pop('timestamp', None)
                    assistant_data.pop('session_id', None)
                    # 重新序列化为字符串
                    data['assistant'] = json.dumps(assistant_data, ensure_ascii=False)
                except (TypeError, json.JSONDecodeError):
                    # 如果解析失败则保持原样
                    pass

            # 写入处理后的数据
            outfile.write(json.dumps(data, ensure_ascii=False) + '\n')


# 使用示例
input_filename = 'type2_responses.json'
output_filename = 'processed_type2_responses.json'
process_file(input_filename, output_filename)