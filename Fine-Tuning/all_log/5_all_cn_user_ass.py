import json
import re


def is_chinese_content(user_str):
    """检查字符串是否为非JSON格式的中文内容"""
    # 尝试解析为JSON，若成功则为JSON格式
    try:
        json.loads(user_str)
        return False
    except:
        # 检查是否包含中文或中文标点
        if re.search(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]', user_str):
            return True
        return False


def filter_chinese_users(input_file, output_file):
    """过滤出user字段为中文内容的行"""
    with open(input_file, 'r', encoding='utf-8') as infile, \
            open(output_file, 'w', encoding='utf-8') as outfile:

        for line in infile:
            try:
                # 解析每行JSON
                data = json.loads(line)
                user_content = data['user']

                # 检查user内容是否为中文
                if is_chinese_content(user_content):
                    outfile.write(line)
            except (json.JSONDecodeError, KeyError):
                continue


if __name__ == "__main__":
    input_file = "all_no_chongfu_user_ass.txt"
    output_file = "all_chinese_user_reason_data.txt"
    filter_chinese_users(input_file, output_file)
    print(f"处理完成！结果已保存到 {output_file}")