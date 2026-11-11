# -*- coding: utf-8 -*-
"""
摩陌到家落地页 - 后端服务
功能：内容管理、图片上传、API接口、管理后台
"""
import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory

app = Flask(__name__)
app.secret_key = 'momodao_2026_secret_key_change_me'
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

DB_PATH = 'momodao.db'

# ============ 数据库初始化 ============
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # 站点全局配置
    c.execute('''CREATE TABLE IF NOT EXISTS site_config (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')

    # 服务项目
    c.execute('''CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        desc TEXT,
        duration TEXT,
        image TEXT,
        sort_order INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1
    )''')

    # FAQ问答
    c.execute('''CREATE TABLE IF NOT EXISTS faqs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        answer TEXT,
        sort_order INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1
    )''')

    # 管理员账号
    c.execute('''CREATE TABLE IF NOT EXISTS admin_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )''')

    conn.commit()

    # 插入默认数据（如果不存在）
    c.execute('SELECT COUNT(*) FROM site_config')
    if c.fetchone()[0] == 0:
        default_config = {
            'site_name': '摩陌到家',
            'wechat_id': 'momodao_kefu',
            'wechat_guide': '这是老师的微信号：',
            'wechat_tip': '（长按复制添加好友），打开微信添加好友，免费获取一对一专业指导呦！',
            'wechat_btn_text': '添加微信',
            'bottom_btn_text': '关注',
            'company_name': '四川宅约科技有限公司',
            'banner_bg_color': '#b8384a',
            'faqs_title': '更多问答',
            'kefu_btn_text': '立即咨询',
            'banner_image': 'banner.png',
            'services_image': 'services.png',
        }
        for k, v in default_config.items():
            c.execute('INSERT INTO site_config (key, value) VALUES (?, ?)', (k, v))

    c.execute('SELECT COUNT(*) FROM services')
    if c.fetchone()[0] == 0:
        default_services = [
            ('帝王尊享SPA', '身心舒缓｜激活能量', '100分钟', 'service1.png', 1, 1),
            ('梦幻柔韵SPA', '身心解压｜帮助睡眠', '90分钟', 'service2.png', 2, 1),
            ('古典舒缓SPA', '舒筋活络｜焕然神态', '80分钟', 'service3.png', 3, 1),
            ('芳香舒缓推拿', '活血化瘀｜消除疲劳', '70分钟', 'service4.png', 4, 1),
            ('中式古法推拿', '舒缓疲劳｜疏通经络', '60分钟', 'service5.png', 5, 1),
        ]
        c.executemany('INSERT INTO services (name, desc, duration, image, sort_order, is_active) VALUES (?,?,?,?,?,?)', default_services)

    c.execute('SELECT COUNT(*) FROM faqs')
    if c.fetchone()[0] == 0:
        default_faqs = [
            ('长期晚上睡觉失眠什么原因？', '长期晚上睡觉失眠的原因可能有很多，以下是一些可能的因素：\n\n1. 环境因素：噪音、光线、温度等环境因素都可能影响睡眠质量。\n2. 生活方式：不规律的生活方式、过度依赖刺激性饮料或药物、抽烟和饮酒等不良习惯都可能影响睡眠。\n3. 心理因素：焦虑、抑郁、压力等负面情绪都可能引起失眠。\n4. 生理因素：年龄、性别、健康状况等生理因素也可能影响睡眠。\n\n如果长期晚上睡觉失眠，可以尝试改变生活方式，建立规律的生活习惯，减少刺激性饮料或药物的摄入，避免过度劳累和压力等负面情绪，同时考虑咨询专业医生，以了解是否需要进一步的医疗治疗。', 1, 1),
            ('推拿上门服务可加盟哪些？', '推拿上门服务是一种非常受欢迎的服务，加盟要求主要包含以下几个方面：\n\n1. 具备良好的专业技能和行业知识：推拿服务需要对人体解剖学、生理学、病理学等方面有一定的了解，同时需要掌握相关的推拿手法和技巧。\n2. 具备一定的服务意识和沟通能力：推拿上门服务的客户体验非常重要，因此要求加盟商具备较强的服务意识和沟通能力，能够提供优质的服务和客户体验。\n3. 具备一定的管理经验和团队领导能力：加盟商需要具备一定的管理经验和团队领导能力，能够带领团队实现业绩目标，提高服务质量和客户满意度。\n4. 具备良好的商业信誉和品牌形象：加盟商需要具备良好的商业信誉和品牌形象，能够为品牌带来正面的影响力和价值。\n5. 具备一定的经济实力和资金实力：加盟商需要具备一定的经济实力和资金实力，能够承担加盟所需的费用和投资。', 2, 1),
        ]
        c.executemany('INSERT INTO faqs (question, answer, sort_order, is_active) VALUES (?,?,?,?)', default_faqs)

    c.execute('SELECT COUNT(*) FROM admin_users')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO admin_users (username, password) VALUES (?, ?)', ('admin', 'admin123'))

    # 确保主图配置项存在（兼容旧数据库）
    for k, v in [('banner_image', 'banner.png'), ('services_image', 'services.png')]:
        c.execute('SELECT COUNT(*) FROM site_config WHERE key=?', (k,))
        if c.fetchone()[0] == 0:
            c.execute('INSERT INTO site_config (key, value) VALUES (?, ?)', (k, v))

    conn.commit()
    conn.close()

# ============ 工具函数 ============
def get_config():
    conn = get_db()
    rows = conn.execute('SELECT key, value FROM site_config').fetchall()
    conn.close()
    return {row['key']: row['value'] for row in rows}

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# ============ 前台页面 ============
@app.route('/')
def index():
    config = get_config()
    conn = get_db()
    services = conn.execute('SELECT * FROM services WHERE is_active=1 ORDER BY sort_order').fetchall()
    faqs = conn.execute('SELECT * FROM faqs WHERE is_active=1 ORDER BY sort_order').fetchall()
    conn.close()
    return render_template('index.html', config=config, services=services, faqs=faqs)

# FAQ详情页
@app.route('/faq/<int:faq_id>')
def faq_detail(faq_id):
    config = get_config()
    conn = get_db()
    faq = conn.execute('SELECT * FROM faqs WHERE id=? AND is_active=1', (faq_id,)).fetchone()
    conn.close()
    if not faq:
        return redirect(url_for('index'))
    return render_template('faq_detail.html', config=config, faq=faq)

# ============ API ============
@app.route('/api/config')
def api_config():
    return jsonify(get_config())

@app.route('/api/services')
def api_services():
    conn = get_db()
    rows = conn.execute('SELECT * FROM services WHERE is_active=1 ORDER BY sort_order').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/faqs')
def api_faqs():
    conn = get_db()
    rows = conn.execute('SELECT * FROM faqs WHERE is_active=1 ORDER BY sort_order').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# ============ 管理后台 ============
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = get_db()
        user = conn.execute('SELECT * FROM admin_users WHERE username=? AND password=?', (username, password)).fetchone()
        conn.close()
        if user:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return redirect(url_for('admin_dashboard'))
        return render_template('admin/login.html', error='用户名或密码错误')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    config = get_config()
    conn = get_db()
    services = conn.execute('SELECT * FROM services ORDER BY sort_order').fetchall()
    faqs = conn.execute('SELECT * FROM faqs ORDER BY sort_order').fetchall()
    conn.close()
    return render_template('admin/dashboard.html', config=config, services=services, faqs=faqs)

# 保存配置
@app.route('/admin/save_config', methods=['POST'])
@login_required
def save_config():
    data = request.form.to_dict()
    conn = get_db()
    for k, v in data.items():
        if k.startswith('config_'):
            key = k[7:]
            conn.execute('UPDATE site_config SET value=? WHERE key=?', (v, key))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# 保存服务项目
@app.route('/admin/save_service', methods=['POST'])
@login_required
def save_service():
    sid = request.form.get('id')
    name = request.form.get('name')
    desc = request.form.get('desc')
    duration = request.form.get('duration')
    image = request.form.get('image', '')
    sort_order = request.form.get('sort_order', 0)

    conn = get_db()
    if sid:
        conn.execute('UPDATE services SET name=?, desc=?, duration=?, image=?, sort_order=? WHERE id=?',
                     (name, desc, duration, image, sort_order, sid))
    else:
        conn.execute('INSERT INTO services (name, desc, duration, image, sort_order, is_active) VALUES (?,?,?,?,?,1)',
                     (name, desc, duration, image, sort_order))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# 删除服务项目
@app.route('/admin/delete_service/<int:sid>')
@login_required
def delete_service(sid):
    conn = get_db()
    conn.execute('DELETE FROM services WHERE id=?', (sid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# 保存FAQ
@app.route('/admin/save_faq', methods=['POST'])
@login_required
def save_faq():
    fid = request.form.get('id')
    question = request.form.get('question')
    answer = request.form.get('answer')
    sort_order = request.form.get('sort_order', 0)

    conn = get_db()
    if fid:
        conn.execute('UPDATE faqs SET question=?, answer=?, sort_order=? WHERE id=?',
                     (question, answer, sort_order, fid))
    else:
        conn.execute('INSERT INTO faqs (question, answer, sort_order, is_active) VALUES (?,?,?,1)',
                     (question, answer, sort_order))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# 删除FAQ
@app.route('/admin/delete_faq/<int:fid>')
@login_required
def delete_faq(fid):
    conn = get_db()
    conn.execute('DELETE FROM faqs WHERE id=?', (fid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# 上传图片
@app.route('/admin/upload_image', methods=['POST'])
@login_required
def upload_image():
    if 'file' not in request.files:
        return jsonify({'success': False, 'msg': '没有文件'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'msg': '未选择文件'})

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ('.png', '.jpg', '.jpeg', '.gif', '.webp'):
        return jsonify({'success': False, 'msg': '只允许图片格式'})

    filename = f'img_{datetime.now().strftime("%Y%m%d%H%M%S")}{ext}'
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    return jsonify({'success': True, 'url': f'/static/images/{filename}'})

# 上传banner图
@app.route('/admin/upload_banner', methods=['POST'])
@login_required
def upload_banner():
    return upload_image()

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    print('=' * 50)
    print('  摩陌到家落地页系统')
    print(f'  运行端口: {port}')
    print(f'  调试模式: {debug}')
    print('=' * 50)
    app.run(host='0.0.0.0', port=port, debug=debug)
