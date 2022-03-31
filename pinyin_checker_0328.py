#!/usr/bin/env python3

import csv
import fnmatch
import os
import re
import sys
from termcolor import colored
from collections import defaultdict
from pprint import pprint
from tempfile import NamedTemporaryFile

duo_yin = {
    "还": "huan/hai", "朝": "chao/zhao", "钿": "dian/tian", "㑚": "nuo/na",
    "仔": "zai/zi", "吓": "xia/he", "轧": "ya/ga"
}
# duo_yin = {"还":"huan/hai","朝":"chao/zhao","钿":"dian/tian","㑚":"nuo/na",
#             "仔":"zai/zi","吓":"xia/he","轧":"ya/ga",
#             "重":"chong/zhong","弄":"long/nong","长":"chang/zhang","调":"tiao/diao",
#             "觉":"jiao/jue","了":"liao/le","着":"zhao/zhe"
#         }
chinese_punc = "！？｡。＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏."


def find_files(path, pattern):
    result = []
    if os.path.isfile(path) and fnmatch.fnmatch(path, pattern):
        result.append(path)
    elif os.path.isdir(path):

        for root, dirs, files in os.walk(path):
            for file in files:
                if fnmatch.fnmatch(file, pattern):
                    result.append(os.path.join(root, file))

    if result:
        return result
    sys.exit('No csv file found.')


def writer(header, data, filename, option):
    dirname = os.path.dirname(filename)
    basename = os.path.basename(filename)
    dirname = dirname+'_reviewed'
    output_path = os.path.join(dirname, basename)
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    with open(output_path, "w", newline="") as csvfile:
        if option == "write":
            movies = csv.writer(csvfile, delimiter="\t")
            movies.writerow(header)
            for x in data:
                movies.writerow(x)
        elif option == "update":
            writer = csv.DictWriter(
                csvfile, fieldnames=header, delimiter="\t", lineterminator='\n')
            writer.writeheader()
            writer.writerows(data)
        else:
            print("Option is not known")
    with open(output_path, 'r') as f:
        new_str = ''
        for line in f:
            if line[-2] == '\t':
                new_str += line.replace('\t\n', '\n')
            else:
                new_str += line

        with open(output_path, 'w', newline='') as ff:
            ff.write(new_str.strip())


def updater(filename):
    with open(filename, 'r', newline="") as file:
        readData = [row for row in csv.DictReader(file, delimiter="\t")]
        for row in readData:
            # 把中文分割成单个字
            regex = r"[\u2E80-\u2FD5\u3190-\u319f\u3400-\u4DBF\u4E00-\u9FCC\uF900-\uFAAD]|[0-9a-zA-Z]|[\W]"
            original_tokens = re.findall(regex, row['original'], re.UNICODE)

            # 检查语句中是否有多音字
            common_items = list(set(duo_yin.keys()) & set(original_tokens))
            if not common_items:
                continue

            # 分割拼音
            pinyin_tokens = re.split(r"(['\s])\s*", row['pinyin'])
            reviewed_arr = pinyin_tokens[:]
            reviewed_values = reviewed_arr[::2]
            reviewed_delimiters = reviewed_arr[1::2] + ['']
            # print(row['original'], common_items)
            # print(reviewed_values)
            # print('\n')

            indexes = [i for i, x in enumerate(
                original_tokens) if x in common_items]
            for key in common_items:
                old = duo_yin[key].split('/')[0]
                advice = duo_yin[key].split('/')[1]
                for index in indexes:
                    if reviewed_values[index] == old:
                        reviewed_values[index] = advice
            reviewed_str = ''.join(
                v+d for v, d in zip(reviewed_values, reviewed_delimiters))
            if reviewed_str != row['pinyin']:
                row['pinyin_reviewed'] = reviewed_str
    need_updatd_rows = [
        obj for obj in readData if "pinyin_reviewed" in obj.keys()]
    if need_updatd_rows:
        readHeader = list(readData[0].keys())
        if 'pinyin_reviewed' not in readHeader:
            readHeader.append('pinyin_reviewed')
        writer(readHeader, readData, filename, "update")
        # print("update")
    else:
        print("no update")
        print(filename)


def review_files(path):
    # Directory to be scanned
    files = find_files(sys.argv[1], '*.csv')
    for file in files:
        updater(file)


def hightlight_keyword(need_review_dict):
    for file_path, values in need_review_dict.items():
        print(colored(file_path, 'blue'))
        for row in values:
            original_tokens = row["original_tokens"]
            pinyin_tokens = row["pinyin_tokens"]
            common_items = row["common_items"]
            indexes = [i for i, x in enumerate(
                original_tokens) if x in common_items]
            # 高亮关键字
            for item in common_items:
                for index in indexes:
                    token_in_original = '{}'.format(item)
                    original_tokens[index] = original_tokens[index].replace(
                        token_in_original,
                        colored(token_in_original, "magenta")
                    )
                    token_in_pinyin = '{}'.format(duo_yin[item].split('/')[0])
                    pinyin_tokens[index] = pinyin_tokens[index].replace(
                        token_in_pinyin,
                        colored(token_in_pinyin, "magenta")
                    )
                    if "reviewed_tokens" in row.keys():
                        token_in_pinyin_review = '{}'.format(
                            duo_yin[item].split('/')[1])
                        row["reviewed_tokens"][index] = row["reviewed_tokens"][index].replace(
                            token_in_pinyin_review,
                            colored(token_in_pinyin_review, "magenta")
                        )
                        advice = '{}: {}-->{}\n'.format(item, duo_yin[item].split('/')[
                                                        0], duo_yin[item].split('/')[1])
                        if 'advice' not in row.keys():
                            row['advice'] = advice
                        else:
                            if advice not in row['advice']:
                                row['advice'] += advice

            print("".join(row['original_tokens']))
            print("'".join(row['pinyin_tokens']))
            if "reviewed_tokens" in row.keys():
                print("'".join(row['reviewed_tokens']))
                print(colored("建议", "blue"))
                print(row['advice'])
            # print('\n')


def print_message(data):
    print("".center(50, "-"))
    for key, value in data.items():
        print(colored(key, 'magenta'))
        for obj in value:
            print(obj["original"])
            print(obj["pinyin"])
            print(obj["original_tokens"], len(obj["original_tokens"]))
            print(obj["pinyin_tokens"], len(obj["pinyin_tokens"]))
            print(obj["reviewed_tokens"], len(obj["reviewed_tokens"]), '\n')

    print("".center(50, "-"))


def main():

    # Directory to be scanned
    files = find_files(sys.argv[1], '*.csv')
    token_unmatched = defaultdict(list)
    unchange_need_review = defaultdict(list)
    change_need_review = defaultdict(list)

    for file in files:
        with open(file, 'r') as f:
            # f_csv = csv.reader(f, delimiter='\t')
            # f_csv = csv.Dictreader(f, delimiter='\t')
            readData = [row for row in csv.DictReader(f, delimiter="\t")]
            need_review = [row for row in readData if row['pinyin_reviewed']]
            # pprint(change_need_review)
            # sys.exit()
            for row in need_review:

                # 把中文分割成单个字
                regex = r"[\u2E80-\u2FD5\u3190-\u319f\u3400-\u4DBF\u4E00-\u9FCC\uF900-\uFAAD]|[0-9a-zA-Z]"
                original_tokens = re.findall(
                    regex, row['original'], re.UNICODE)

                # 分割拼音
                pinyin_tokens = re.split(r"['\s]\s*", row['pinyin'])
                pinyin_tokens = [
                    item for item in pinyin_tokens if item.isdigit() or item.isalpha()]

                # 检查语句中是否有多音字
                common_items = list(set(duo_yin.keys()) & set(original_tokens))
                if not common_items:
                    continue

                row["common_items"] = common_items
                row["original_tokens"] = original_tokens
                row["pinyin_tokens"] = pinyin_tokens

                try:
                    # 分割review部分的拼音
                    reviewed_tokens = re.split(
                        r"['\s]\s*", row["pinyin_reviewed"])
                    reviewed_tokens = [
                        item for item in reviewed_tokens if item.isdigit() or item.isalpha()]
                    row['reviewed_tokens'] = reviewed_tokens
                    change_need_review[file].append(row)
                    # 检查拼音和每个字是否匹配
                    if len(original_tokens) != len(reviewed_tokens):
                        token_unmatched[file].append(row)
                except Exception as e:
                    raise colored(e, 'red')
                    # 对于没有修改的语句，row[3]会触发异常
                    # unchange_need_review[file].append(row_object)

    if not change_need_review and not token_unmatched:
        sys.exit(colored("文件还没有被Review!", 'blue'))

    if token_unmatched:
        print(colored("检查Pinyin_Review和中文个数是否匹配:", 'blue'),
              "({})".format(colored('N', 'red')))
        print_message(token_unmatched)
        sys.exit()
    else:
        print(colored("检查Pinyin_Review和中文个数是否匹配:", 'blue'),
              "({})".format(colored('Y', 'green')))

    if change_need_review:
        print(colored("检查Review部分的多音字:", 'blue'))
        print("".center(50, "-"))
        hightlight_keyword(change_need_review)
        print("".center(50, "-"))


if __name__ == '__main__':
    review_files(sys.argv[1])
    # main()
    # regex_s = r"[\u2E80-\u2FD5\u3190-\u319f\u3400-\u4DBF\u4E00-\u9FCC\uF900-\uFAAD]|[0-9a-zA-Z]|[\W]"
    # s = "侬一讲人家就嘣跳起来了会得，对伐？"

    # # regex_p = r"['\s]\s*]|[0-9a-zA-Z]|[\W]"
    # regex_p = r"['\s0-9a-zA-Z]|[\W]"
    # p = "nong'yi'jiang ren'jia jiu'beng'tiao'qi'lai'le hui'de ， dui'fa ？"

    # result1 = re.findall(regex_s, s, re.UNICODE)
    # result2 = re.split(r"(['\s])\s*", p)
    # values = result2[::2]
    # delimiters = result2[1::2] + ['']
    # reviewed_str = ''.join(v+d for v, d in zip(values,delimiters))
    # print(result1, len(result1))
    # print(values, len(values))
    # print(p)
    # print(reviewed_str==p)
