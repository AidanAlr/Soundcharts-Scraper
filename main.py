from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd

options = Options()
# options.add_experimental_option("detach", True)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

driver.get("https://app.soundcharts.com/login")

# Find the username and password input fields by XPath
username_input = driver.find_element(By.NAME, "email")
password_input = driver.find_element(By.NAME, "password")

# Enter username and password
username_input.send_keys("jhlevy01@gmail.com")
password_input.send_keys("pogg4$33a!")

# Find and click the login button
login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
login_button.click()

# Wait for the page to load
time.sleep(5)  # Adjust the time as needed

def load_webpage(url):
    driver.get(url)
    time.sleep(10)

# driver.get("https://app.soundcharts.com/app/market/charts?chart=airplay-daily&chart_type=song&country=GLOBAL&period=1&platform=airplay")

spotify = "https://app.soundcharts.com/app/market/charts?chart=global-28&chart_type=song&country=GLOBAL&period=1&platform=spotify"

# tiktok = driver.get("https://app.soundcharts.com/app/market/charts?chart=tiktok-weekly-songs&chart_type=song&country=GLOBAL&platform=tiktok")

# Wait for the page to load


# Find all div elements with the specified class name
# div_elements = driver.find_elements(By.XPATH, "//div[@class='sc-bvCTgw iGqjOB']")
songs = driver.find_elements(By.CSS_SELECTOR, "div.sc-cMhqgX.hQLcyr")
artists = driver.find_elements(By.CSS_SELECTOR, "div.sc-hMFtBS.gzoeoI")
links = driver.find_elements(By.CSS_SELECTOR, "img.sc-epnACN.ksrdaN")

while not songs or not artists or not links:
    load_webpage(spotify)
    songs = driver.find_elements(By.CSS_SELECTOR, "div.sc-cMhqgX.hQLcyr")
    artists = driver.find_elements(By.CSS_SELECTOR, "div.sc-hMFtBS.gzoeoI")
    links = driver.find_elements(By.CSS_SELECTOR, "img.sc-epnACN.ksrdaN")


def parse_link(link):
    """
    This function takes in the image link and returns the song page
    :param link:
    :return:

    Example
    https://assets.soundcharts.com/song/c/6/a/399221ee-3a6c-454c-ae79-23024d428f30.jpg
    https://app.soundcharts.com/app/song/399221ee-3a6c-454c-ae79-23024d428f30/playlists?playlist-categories=algorithmic.charts.curators_listeners.editorial.algotorial.major.this_is
    """

    link: str = link.get_attribute("src").rstrip(".jpg").lstrip("https://assets.soundcharts.com/song/d/b/e/")
    result = "https://app.soundcharts.com/app/song/" + link + "/playlists?playlist-categories=algorithmic.charts.curators_listeners.editorial.algotorial.major.this_is"
    return result


try:

    songs = [div.text for div in songs]
    artists = [div.text for div in artists]
    links = [parse_link(link) for link in links]

    def make_dataframe(songs, artists, links):
        df = pd.DataFrame(list(zip(songs, artists, links)), columns=["Song", "Artist", "Link"])
        return df

    df = make_dataframe(songs, artists, links)
    print(df)
    df.to_csv("top_29.csv")
except Exception as e:
    print(e)
    print("An error occurred")
    print(songs)
    print(artists)
    print(links)
