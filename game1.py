from flask import Flask, render_template, request, jsonify
import random
import datetime

app = Flask(__name__)

history = []
today_counts = {}
ip_key_usage = {}  # 记录每个IP地址的key使用情况
MAX_HISTORY_SIZE = 50  # 设置最大历史记录数量
KEY_FILE = 'keys.txt'  # 存储key的文件

def roll_dice():
    return random.randint(1, 100)

def calculate_final_score(level, dice):
    base_score = level * 0.6 + dice * 0.4
    if dice > level:
        final_score = base_score * 1.1
    elif dice < level:
        final_score = base_score * 0.9
    else:
        final_score = base_score
    final_score = max(1, min(100, final_score))
    return round(final_score)

def get_next_key():
    with open(KEY_FILE, 'r') as file:
        keys = file.readlines()
    if not keys:
        return None
    next_key = keys[0].strip()
    with open(KEY_FILE, 'w') as file:
        file.writelines(keys[1:])
    return next_key

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.get_json()
    name = data.get('name').strip()
    level = int(data.get('level'))
    current_date = datetime.date.today()
    ip_address = request.remote_addr

    # 检查今天的计算次数
    if name in today_counts:
        if today_counts[name]['date'] != current_date:
            today_counts[name] = {'count': 1, 'date': current_date}
        else:
            today_counts[name]['count'] += 1

        if today_counts[name]['count'] > 1:
            return jsonify({'error': f"{name} 今天已经计算过一次，无法继续！"}), 400
    else:
        today_counts[name] = {'count': 1, 'date': current_date}

    # 检查IP地址的key使用情况
    if ip_address in ip_key_usage:
        if ip_key_usage[ip_address]['date'] == current_date:
            key = ip_key_usage[ip_address]['key']
        else:
            key = get_next_key()
            ip_key_usage[ip_address] = {'key': key, 'date': current_date}
    else:
        key = get_next_key()
        ip_key_usage[ip_address] = {'key': key, 'date': current_date}

    if key is None:
        return jsonify({'error': '没有可用的key！'}), 400

    dice = roll_dice()
    score = calculate_final_score(level, dice)

    # 检查并清理历史记录
    if len(history) >= MAX_HISTORY_SIZE:
        history.pop()  # 删除最旧的记录

    # 将新记录插入到历史记录的开头
    history.insert(0, {
        "name": name,
        "level": level,
        "dice": dice,
        "final_score": score,
        "date": current_date.isoformat()
    })

    return jsonify({'name': name, 'level': level, 'dice': dice, 'score': score, 'key': key})

@app.route('/history', methods=['GET'])
def get_history():
    page = int(request.args.get('page', 1))
    items_per_page = 5  # 每页5条记录

    # 不需要再排序，因为新记录已经在开头
    total_items = len(history)

    # 分页
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page
    items = history[start_index:end_index]

    is_last_page = end_index >= total_items

    return jsonify({
        'items': items,
        'isLastPage': is_last_page
    })

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=False)
