import pandas as pd
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Paths
file_path = r'C:\Users\Shiva\Desktop\AUTOMATION PROCESS\Automatic Photo\FK Photos\FK.xlsm'
save_dir = r'C:\Users\Shiva\Desktop\AUTOMATION PROCESS\Automatic Photo\FK Photos\fullProduct_screenshot'

if not os.path.exists(save_dir):
    os.makedirs(save_dir)

# Browser Setup
options = Options()
options.add_argument('--headless=new')
options.add_argument('--window-size=1920,1080') # Screen size set hai
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
        time.sleep(5) # Page load hone ka wait
        
        # POORE PAGE KA SCREENSHOT LENE KE LIYE YAHI CHANGE KIYA HAI:
        driver.save_screenshot(screenshot_path)
        print(f"[{serial_no}] SAVED: Full page screenshot")
            
    except Exception as e:
        print(f"[{serial_no}] FAILED: {fsn} - Error: {e}")

driver.quit()
print("Done!")