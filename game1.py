from flask import Flask, render_template, request, jsonify
import random
import datetime

app = Flask(__name__)

history = []
today_counts = {}
MAX_HISTORY_SIZE = 50  # 设置最大历史记录数量

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

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.get_json()
    name = data.get('name').strip()
    level = int(data.get('level'))
    current_date = datetime.date.today()

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

    dice = roll_dice()
    score = calculate_final_score(level, dice)

    # 检查并清理历史记录
    if len(history) >= MAX_HISTORY_SIZE:
        history.pop(0)  # 删除最旧的记录

    history.append({
        "name": name,
        "level": level,
        "dice": dice,
        "final_score": score,
        "date": current_date.isoformat()
    })

    return jsonify({'name': name, 'level': level, 'dice': dice, 'score': score})

@app.route('/history', methods=['GET'])
def get_history():
    page = int(request.args.get('page', 1))
    items_per_page = 10  # 每页10条记录

    # 按日期排序
    sorted_history = sorted(history, key=lambda x: x['date'], reverse=True)
    total_items = len(sorted_history)

    # 分页
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page
    items = sorted_history[start_index:end_index]

    is_last_page = end_index >= total_items

    return jsonify({
        'items': items,
        'isLastPage': is_last_page
    })

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
