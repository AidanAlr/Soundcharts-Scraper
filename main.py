from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

options = Options()
options.add_experimental_option("detach", True)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

driver.get("https://app.soundcharts.com/login")

# Find the username and password input fields by XPath
username_input = driver.find_element(By.NAME, "email")
password_input = driver.find_element(By.NAME, "password")

# Enter username and password
username_input.send_keys("admin@thesystemrecords.com")
password_input.send_keys("E7$DQcEEESqZu$r")

# Find and click the login button
login_button = driver.find_element(By.XPATH,"//button[@type='submit']")
login_button.click()

# Wait for the page to load
time.sleep(5)  # Adjust the time as needed

# driver.get("https://app.soundcharts.com/app/market/charts?chart=airplay-daily&chart_type=song&country=GLOBAL&period=1&platform=airplay")

# driver.get("https://app.soundcharts.com/app/market/charts?chart=global-28&chart_type=song&country=GLOBAL&period=1&platform=spotify")

tiktok = driver.get("https://app.soundcharts.com/app/market/charts?chart=tiktok-weekly-songs&chart_type=song&country=GLOBAL&platform=tiktok")

# Wait for the page to load
time.sleep(7)

# Find all div elements with the specified class name
# div_elements = driver.find_elements(By.XPATH, "//div[@class='sc-bvCTgw iGqjOB']")
songs = driver.find_elements(By.CSS_SELECTOR, "div.sc-cMhqgX.hQLcyr")
artists = driver.find_elements(By.CSS_SELECTOR, "div.sc-hMFtBS.gzoeoI")
ranking = driver.find_elements(By.CSS_SELECTOR, "div.sc-hENMEE.deWhnr")


songs = [div.text for div in songs]
artists = [div.text for div in artists]


top_29 = {}
count = 0
for song in songs:
    top_29[count+1] = f"{songs[count]} - {artists[count]}"
    count += 1

print(top_29)


print("done")


