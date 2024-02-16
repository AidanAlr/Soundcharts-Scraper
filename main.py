import time

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

spotify = "https://app.soundcharts.com/app/market/charts?chart=global-28&chart_type=song&country=GLOBAL&period=1&platform=spotify"
spotify_noLabels = "https://app.soundcharts.com/app/market/charts?chart=global-28&chart_type=song&country=GLOBAL&filters=eyJmbHQiOiJTZWxmIHJlbGVhc2VkfFVua25vd24ifQ%3D%3D&period=1&platform=spotify"
apple_music = "https://app.soundcharts.com/app/market/charts?chart=top-100-global&chart_type=song&country=GLOBAL&platform=apple-music"
apple_music_noLabels = "https://app.soundcharts.com/app/market/charts?chart=top-100-global&chart_type=song&country=GLOBAL&filters=eyJmbHQiOiJTZWxmIHJlbGVhc2VkfFVua25vd24ifQ%3D%3D&platform=apple-music"
shazam = "https://app.soundcharts.com/app/market/charts?chart=shazam-top-200-world&chart_type=song&country=GLOBAL&platform=shazam"

general_css_selector = {
    "songs": "div.sc-cMhqgX.hQLcyr",
    "artists": "div.sc-hMFtBS.gzoeoI",
    "links": "img.sc-epnACN.ksrdaN"
}

css_selector_dict = {
    spotify: general_css_selector,
    spotify_noLabels: general_css_selector,
    apple_music: general_css_selector,
    apple_music_noLabels: general_css_selector,
    shazam: general_css_selector
}


def get_variable_name(var):
    for name, value in globals().items():
        if value is var:
            return name


def extract_after_last_slash(url):
    parts = url.split('/')
    return parts[-1]


def parse_link(link):
    """
    This function takes in the image link and returns the song page
    :param link:
    :return:

    Example
    https://assets.soundcharts.com/song/c/6/a/399221ee-3a6c-454c-ae79-23024d428f30.jpg
    https://app.soundcharts.com/app/song/399221ee-3a6c-454c-ae79-23024d428f30/playlists?playlist-categories=algorithmic.charts.curators_listeners.editorial.algotorial.major.this_is
    """
    link: str = extract_after_last_slash(link.get_attribute("src")).rstrip(".jpg")
    result = "https://app.soundcharts.com/app/song/" + link + "/overview"
    return result


def parse_webpage(driver, url) -> pd.DataFrame():
    chart_name = get_variable_name(url)

    songs, artists, links = None, None, None

    while not songs or not artists or not links:
        print("Parsing webpage: {}".format(chart_name))
        driver.get(url)
        time.sleep(10)
        # This works for scrolling the entire page
        # Need to create some scrolling function to capture all ements of the div
        # element = driver.find_element(By.CSS_SELECTOR, 'div.sc-gKLXLV.dghebG.custom-scrollbar')
        # # Scroll to the end of the element
        # driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", element)
        time.sleep(5)
        songs = driver.find_elements(By.CSS_SELECTOR, css_selector_dict[url]["songs"])
        # artists = driver.find_elements(By.CSS_SELECTOR, css_selector_dict[url]["artists"])
        links = driver.find_elements(By.CSS_SELECTOR, css_selector_dict[url]["links"])
        artists = driver.find_elements(By.CSS_SELECTOR, 'div.sc-esOvli.cfpVgy')

        print("Songs: ", len(songs))
        print("Artists: ", len(artists))
        print("Links: ", len(links))

    songs = [div.text for div in songs]
    artists = [div.text for div in artists]
    links = [parse_link(link) for link in links]

    artists = extract_names(artists)

    def make_dataframe(songs, artists, links):
        df = pd.DataFrame(list(zip(songs, artists, links)), columns=["Song", "Artist", "Link"])
        print(df)
        return df

    df = (make_dataframe(songs, artists, links))
    df.to_csv(f"{chart_name}.csv")
    print("csv/df created")
    return df


def extract_names(names):
    joined_names = []
    result = ""
    for name in names:
        if name == "•":
            result += "/"
        else:
            if result:
                if result[-1] == "•":
                    print("hit fs")
                    result += "/"
                else:
                    joined_names.append(result)
                    result = name
            else:
                result += name

    joined_names.append(result)

    return joined_names


def run(headless):
    try:
        print("Starting")
        options = Options()

        if headless:
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
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

        print("Logged in")

        # Wait for the page to load
        time.sleep(5)  # Adjust the time as needed
        parse_webpage(driver, spotify)
        # parse_webpage(driver, spotify_noLabels)
        # parse_webpage(driver, apple_music)
        # parse_webpage(driver, apple_music_noLabels)
        # parse_webpage(driver, shazam)

    except Exception as e:
        print(e)


if __name__ == "__main__":
    run(headless=True)
