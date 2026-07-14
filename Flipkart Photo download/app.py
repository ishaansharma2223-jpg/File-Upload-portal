import os
import time
import threading
import requests
import pandas as pd
from flask import Flask, request, render_template, jsonify, send_file
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from openpyxl import load_workbook
from openpyxl.drawing.image import Image
from PIL import Image as PILImage

app = Flask(__name__)

# Paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
PROCESSED_FOLDER = os.path.join(BASE_DIR, 'processed')
MAIN_IMAGE_FOLDER = os.path.join(BASE_DIR, 'Mainimage')
SCREENSHOT_FOLDER = os.path.join(BASE_DIR, 'fullProduct_screenshot')

for folder in [UPLOAD_FOLDER, PROCESSED_FOLDER, MAIN_IMAGE_FOLDER, SCREENSHOT_FOLDER]:
    os.makedirs(folder, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
PLACEHOLDER_URL = "https://cdn-icons-png.flaticon.com/512/189/189665.png"

# Global status tracker for polling
task_status = {
    'progress': 0,
    'completed': 0,
    'total': 0,
    'current_fsn': '',
    'current_step': 'Initializing...',
    'done': False,
    'error': None,
    'output_path': None,
    'output_filename': None
}
status_lock = threading.Lock()

def setup_driver():
    options = Options()
    options.add_argument('--headless') # Standard headless mode
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--window-position=-2000,-2000') # Forces window completely off-screen
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--log-level=3')
    options.add_argument('--disable-gpu')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def create_dummy_image(path, color):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        img = PILImage.new('RGB', (100, 100), color=color)
        img.save(path, 'PNG')
    except Exception as e:
        print(f"Error creating dummy: {e}")

def download_images_for_fsn(fsn, index, driver, get_main, get_screen):
    url = f"https://www.flipkart.com/product/p/item?pid={fsn}"
    main_path = os.path.join(MAIN_IMAGE_FOLDER, f"{index}_main.png")
    screen_path = os.path.join(SCREENSHOT_FOLDER, f"{index}_screen.png")
    
    try:
        driver.get(url)
        time.sleep(1) 
        
        if get_main:
            with status_lock:
                task_status['current_step'] = 'Downloading Main Image...'
            images = driver.find_elements(By.TAG_NAME, "img")
            main_img = None
            max_area = 0
            for img in images:
                try:
                    width = img.size.get('width', 0)
                    height = img.size.get('height', 0)
                    area = width * height
                    if area > 10000 and area > max_area:
                        max_area = area
                        main_img = img
                except:
                    continue
            
            if main_img:
                main_img.screenshot(main_path)
            else:
                img_data = requests.get(PLACEHOLDER_URL).content
                with open(main_path, 'wb') as f:
                    f.write(img_data)
                    
        if get_screen:
            with status_lock:
                task_status['current_step'] = 'Taking Full Screenshot...'
            driver.save_screenshot(screen_path)
            
    except Exception as e:
        print(f"Error processing FSN {fsn}: {e}")
        if get_main:
            create_dummy_image(main_path, (255, 0, 0))
        if get_screen:
            create_dummy_image(screen_path, (0, 0, 255))

def background_process(file_path, get_main, get_screen):
    global task_status
    try:
        with status_lock:
            task_status.update({
                'progress': 0, 'completed': 0, 'total': 0,
                'current_fsn': '', 'current_step': 'Reading Excel File...',
                'done': False, 'error': None, 'output_path': None
            })
            
        df = pd.read_excel(file_path)
        fsn_list = df.iloc[:, 3].tolist() 
        fsn_list = [str(fsn).strip() for fsn in fsn_list if pd.notna(fsn) and str(fsn).strip() != '']
        
        total = len(fsn_list)
        with status_lock:
            task_status['total'] = total
            task_status['current_step'] = 'Starting Browser...'
            
        driver = setup_driver()
        try:
            for i, fsn in enumerate(fsn_list, 1):
                with status_lock:
                    task_status['current_fsn'] = fsn
                    task_status['current_step'] = f'Processing product {i} of {total}'
                
                download_images_for_fsn(fsn, i, driver, get_main, get_screen)
                
                with status_lock:
                    task_status['completed'] = i
                    task_status['progress'] = int((i / total) * 100)
            
            with status_lock:
                task_status['current_step'] = 'Updating Excel File...'
                
            wb = load_workbook(file_path)
            ws = wb.active
            
            for row_idx, fsn in enumerate(fsn_list, 2): 
                index = row_idx - 1
                if get_main:
                    main_path = os.path.join(MAIN_IMAGE_FOLDER, f"{index}_main.png")
                    if os.path.exists(main_path):
                        try:
                            img = Image(main_path)
                            img.width = 100
                            img.height = 100
                            ws.add_image(img, f"T{row_idx}")
                        except: pass
                
                if get_screen:
                    screen_path = os.path.join(SCREENSHOT_FOLDER, f"{index}_screen.png")
                    if os.path.exists(screen_path):
                        try:
                            img = Image(screen_path)
                            img.width = 150
                            img.height = 150
                            ws.add_image(img, f"U{row_idx}")
                        except: pass
            
            ws.column_dimensions['T'].width = 18
            ws.column_dimensions['U'].width = 24
            for row in range(2, total + 2):
                ws.row_dimensions[row].height = 80
            
            base_name = os.path.basename(file_path).rsplit('.', 1)[0]
            output_filename = f"processed_{base_name}.xlsx"
            output_path = os.path.join(PROCESSED_FOLDER, output_filename)
            wb.save(output_path)
            
            with status_lock:
                task_status['done'] = True
                task_status['current_step'] = 'Completed Successfully!'
                task_status['output_path'] = output_path
                task_status['output_filename'] = output_filename
                
        finally:
            driver.quit()
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        with status_lock:
            task_status['error'] = str(e)
            task_status['current_step'] = 'Failed'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        get_main = request.form.get('get_main') == 'true'
        get_screen = request.form.get('get_screen') == 'true'
        
        t = threading.Thread(target=background_process, args=(filepath, get_main, get_screen))
        t.start()
        
        return jsonify({'status': 'started'})

@app.route('/status', methods=['GET'])
def get_status():
    with status_lock:
        return jsonify(task_status)

@app.route('/download_result', methods=['GET'])
def download_result():
    with status_lock:
        path = task_status.get('output_path')
        name = task_status.get('output_filename', 'processed_file.xlsx')
    
    if path and os.path.exists(path):
        return send_file(path, as_attachment=True, download_name=name)
    return "File not ready or not found", 400

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)