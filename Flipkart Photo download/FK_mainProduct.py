import pandas as pd
import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Paths
file_path = r'C:\Users\Shiva\Desktop\Automatic Photo\FK Photos\FK.xlsm'
save_dir = r'C:\Users\Shiva\Desktop\Automatic Photo\FK Photos\Mainimage'
placeholder_url = "https://cdn-icons-png.flaticon.com/512/189/189665.png"

if not os.path.exists(save_dir):
    os.makedirs(save_dir)

# Browser Setup
options = Options()
options.add_argument('--headless=new')
options.add_argument('--window-size=1920,1080')
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

df = pd.read_excel(file_path)
fsn_list = df.iloc[:, 3].tolist() 

print(f"--- Process Start ---")

for i, fsn in enumerate(fsn_list, 1):
    serial_no = i
    screenshot_path = os.path.join(save_dir, f"{serial_no}.png")
    
    if pd.isna(fsn) or str(fsn).strip() == '':
        continue

    url = f"https://www.flipkart.com/product/p/item?pid={fsn}"
    
    try:
        driver.get(url)
        time.sleep(5) 
        
        images = driver.find_elements(By.TAG_NAME, "img")
        main_img = None
        max_area = 0
        
        for img in images:
            width = img.size.get('width', 0)
            height = img.size.get('height', 0)
            area = width * height
            if area > 10000: 
                if area > max_area:
                    max_area = area
                    main_img = img

        if main_img:
            main_img.screenshot(screenshot_path)
            print(f"[{serial_no}] SAVED: Image found")
        else:
            # Yahan ab ? wali image save ho jayegi
            img_data = requests.get(placeholder_url).content
            with open(screenshot_path, 'wb') as f:
                f.write(img_data)
            print(f"[{serial_no}] NOT FOUND: Saved ? placeholder")
            
    except Exception as e:
        print(f"[{serial_no}] FAILED: {fsn}")

driver.quit()
print("Done!")