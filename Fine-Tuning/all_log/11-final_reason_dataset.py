import json


def convert_dataset(input_file, output_file):
    converted_data = []

    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                # 解析每行JSON
                data = json.loads(line.strip())
                user = data["user"]

                # 解析assistant字段中的JSON字符串
                assistant_data = json.loads(data["assistant"])
                assistant = assistant_data["content"]

                # 构建对话格式
                conversation = {
                    "conversations": [
                        {"from": "user", "value": user},
                        {"from": "assistant", "value": assistant}
                    ]
                }
                converted_data.append(conversation)

            except (json.JSONDecodeError, KeyError) as e:
                print(f"解析错误跳过行: {line.strip()}，错误: {str(e)}")

    # 保存转换后的数据
    with open(output_file, 'w', encoding='utf-8') as f_out:
        json.dump(converted_data, f_out, ensure_ascii=False, indent=2)

    print(f"转换完成！共处理 {len(converted_data)} 条对话")


if __name__ == "__main__":
    input_file = "processed_type2_responses.json"  # 输入文件名
    output_file = "conversation_dataset.json"  # 输出文件名
    convert_dataset(input_file, output_file)