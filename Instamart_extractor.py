# streamlit_swiggy_scraper.py

import streamlit as st
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import re
import warnings

warnings.filterwarnings('ignore')

# Initialize WebDriver only once
@st.cache_resource
def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    return webdriver.Chrome(options=options)

def scroller(driver):
    scroll_pause_time = 1
    screen_height = driver.execute_script("return window.screen.height;")
    i = 1
    while True:
        driver.execute_script("window.scrollTo(0, {screen_height}*{i});".format(screen_height=screen_height, i=i))
        i += 1
        time.sleep(scroll_pause_time)
        scroll_height = driver.execute_script("return document.body.scrollHeight;")
        if (screen_height) * i > scroll_height * (3/4):
            break

def product_scraper(driver, url):
    driver.get(url)
    wait = WebDriverWait(driver, 10)

    df_prod = pd.DataFrame()
    df_prod["URL"] = pd.Series(url)
    time.sleep(2)

    def extract_product_id(url):
        match = re.search(r'/item/([\w-]+)', url)
        return match.group(1) if match else None

    df_prod["Product ID"] = pd.Series(extract_product_id(url))

    try:
        df_prod["Image URL"] = driver.find_element(By.CLASS_NAME, "_2ldxo").find_element(By.TAG_NAME, "img").get_attribute('src')
    except:
        df_prod["Image URL"] = None

    try:
        scroller(driver)
    except:
        pass

    try:
        title = driver.title
        match = re.search(r'Buy\s+((?:\b\w+\b\s*)+)\1', title)
        if match:
            df_prod["Brand"] = match.group(1)
    except:
        pass

    try:
        df_prod["Product Name"] = driver.find_element(By.CLASS_NAME, "sc-aXZVg.gPfbij._AHZN").text
    except:
        pass

    try:
        df_prod["Quantity"] = driver.find_element(By.CLASS_NAME, "sc-aXZVg.kYaBqd._1TwvP").text
    except:
        pass

    try:
        df_prod["Selling Price"] = driver.find_element(By.CLASS_NAME, "sc-aXZVg.jLtxeJ._1bWTz._2XPBo").text
    except:
        pass

    try:
        x = driver.find_elements(By.CLASS_NAME, "_3Lj8S")
        for i in x:
            h = i.find_element(By.CLASS_NAME, "_3F5nE").text
            v = i.find_element(By.CLASS_NAME, "F53lh").text
            df_prod[h] = pd.Series(v)
    except:
        pass

    try:
        elem = driver.find_element(By.CLASS_NAME, '_3O02u').find_elements(By.CLASS_NAME, '_2Q05q')
        for i in elem:
            head = i.find_element(By.CLASS_NAME, "sc-aXZVg.gPfbij.-SSas").text
            val = i.find_element(By.CLASS_NAME, '_3g9ka').text
            df_prod[head] = pd.Series(val)
    except:
        pass

    try:
        x = driver.find_element(By.CLASS_NAME, "_2VPtu").find_element(By.CLASS_NAME, "sc-aXZVg.qyIkA").find_elements(By.TAG_NAME, "p")
        for i in x:
            if ':' in i.text:
                h, v = i.text.split(":", 1)
                df_prod[h.strip()] = pd.Series(v.strip())
    except:
        pass

    try:
        x = driver.find_elements(By.CSS_SELECTOR, '._2VPtu .sc-aXZVg.qyIkA')
        for i in x:
            if "Customer Care" in i.text:
                h, v = i.text.split(":", 1)
                df_prod[h.strip()] = pd.Series(v.strip())
    except:
        pass

    try:
        H, V = driver.find_element(By.CLASS_NAME, "_1HVEP").find_element(By.CLASS_NAME, "_3g9ka").text.split(':')
        df_prod[H.strip()] = pd.Series(V.strip())
    except:
        pass

    return df_prod

# Streamlit App
st.set_page_config(page_title="🛒 Swiggy Instamart Product Scraper", layout="centered")

st.title("🛍️ Swiggy Instamart Product Info Extractor")
st.markdown("Enter a Swiggy Instamart product link below to fetch product information.")

url = st.text_input("🔗 Enter Swiggy Product URL", placeholder="https://www.swiggy.com/instamart/item/XYZ")

if st.button("🔍 Scrape Product Info"):
    if url:
        with st.spinner("Scraping data... please wait ⏳"):
            driver = get_driver()
            try:
                df_result = product_scraper(driver, url)
                st.success("✅ Product data extracted successfully!")
                st.dataframe(df_result.T, use_container_width=True)
                
                if "Image URL" in df_result.columns:
                    st.image(df_result["Image URL"].values[0], caption="Product Image", width=300)
                
                csv = df_result.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Download as CSV", csv, "product_info.csv", "text/csv")
            except Exception as e:
                st.error(f"❌ Error occurred: {e}")
    else:
        st.warning("⚠️ Please enter a valid Swiggy product URL.")
