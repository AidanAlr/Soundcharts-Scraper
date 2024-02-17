import time

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


def get_variable_name(var):
    for name, value in globals().items():
        if value is var:
            return name


def extract_after_last_slash(url):
    parts = url.split('/')
    return parts[-1]


def parse_img_link(link):
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


def parse_change(change):
    change = [s.text for s in change]
    change = [s.split('\n')[1] for s in change if '\n' in s]
    return change


def scroll_20_pct(driver):
    element = driver.find_element(By.CSS_SELECTOR, 'div.sc-gKLXLV.dghebG.custom-scrollbar')
    driver.execute_script("arguments[0].scrollBy(0, 100)", element)
    print("Scrolled 20% down")


def make_dataframe(*args):
    df = pd.DataFrame()
    for arg in args:
        df = pd.concat([df, pd.DataFrame(arg)], axis=1)

    return df


def zoom_out(driver):
    driver.execute_script("document.body.style.zoom='50%'")
    print("Zoomed out")
    time.sleep(5)


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


def sort_by_doc(driver):
    try:
        print("Sorting by DOC")
        down_button = driver.find_elements(By.CSS_SELECTOR, "div.sc-kGeDwz.irzRFw")
        down_button[1].click()
        time.sleep(5)
        down_button_2 = driver.find_elements(By.CSS_SELECTOR, "div.sc-kGeDwz.jexWuv")
        down_button_2[0].click()
        return True
    except Exception as e:
        print(e)
        return False


class Link:
    def __init__(self, chart_type, country, platform, filters=None):
        charts = {
            "spotify": "global-28",
            "apple-music": "top-100-global",
            "shazam": "shazam-top-200-world"
        }
        self.filters_dict = {
            "no_labels": "eyJmbHQiOiJTZWxmIHJlbGVhc2VkfFVua25vd24ifQ%3D%3D"
        }
        self.chart = charts[platform] if country == "GLOBAL" else "top-200-" + country
        self.chart_type = chart_type
        self.country = country
        self.platform = platform
        self.filters = self.filters_dict[filters] if filters else ""

        self.link = f"https://app.soundcharts.com/app/market/charts?chart={self.chart}&chart_type={self.chart_type}&country={self.country}"
        if self.platform == "spotify":
            self.link += "&period=1"
        if self.filters:
            self.link += f"&filters={self.filters}"
        self.link += f"&platform={self.platform}"


def label_filter(label_list):
    filtered_labels = ["sony", 'umg', 'warner', 'independent', 'universal', 'warner music', 'sony music', 'universal music']


def parse_webpage(driver, url, labels_to_remove) -> pd.DataFrame():
    general_css_selector = {
        "songs": "div.sc-cMhqgX.hQLcyr",
        "artists": "div.sc-esOvli.cfpVgy",
        "links": "img.sc-epnACN.ksrdaN",
        "change": "div.sc-hENMEE.deWhnr",
        "doc": "div.sc-hmyDHa.jWjosp",
        "labels": "div.sc-hAcydR.gdSjQR",
    }

    songs, artists, links, labels, change, doc = None, None, None, None, None, None

    sorted_by_doc = False

    scroll = 0
    while scroll < 60:
        while not songs or not artists or not links or not change or not sorted_by_doc or not doc:
            print("Parsing webpage: {}".format(url))
            driver.get(url)
            time.sleep(8)
            sorted_by_doc = sort_by_doc(driver)
            time.sleep(4)

            # songs = driver.find_elements(By.CSS_SELECTOR, general_css_selector["songs"])
            songs = driver.find_elements(By.CSS_SELECTOR, "div.sc-eTuwsz.jWHscE")
            links = driver.find_elements(By.CSS_SELECTOR, general_css_selector["links"])
            artists = driver.find_elements(By.CSS_SELECTOR, general_css_selector["artists"])
            change = driver.find_elements(By.CSS_SELECTOR, general_css_selector["change"])
            doc = driver.find_elements(By.CSS_SELECTOR, general_css_selector["doc"])
            labels = driver.find_elements(By.CSS_SELECTOR, general_css_selector["labels"])
            labels = [div.text for div in labels]

            def remove_substring_from_string(substring, string):
                return string.replace(substring, "")

            labels = [remove_substring_from_string("Unknown", label) for label in labels]
            labels = [remove_substring_from_string("Self released", label) for label in labels]
            labels = [label.replace("\n", "-") for label in labels]

            print(labels)

            print("Songs({}), Artists({}), Labels({}), Links({}), Change({}), DOC({})".format(len(songs),
                                                                                              len(artists),
                                                                                              len(labels),
                                                                                              len(links),
                                                                                              len(change),
                                                                                              len(doc)))

    songs = [div.text for div in songs]
    artists = extract_names([div.text for div in artists])
    links = [parse_img_link(link) for link in links]
    change = parse_change(change)
    doc = [div.text for div in doc]

    # create dataframe with columns
    df = pd.DataFrame()
    df["Change"] = change
    df["Song"] = songs
    df["Artists"] = artists
    df["Labels"] = labels
    df["Link"] = links
    df["DOC"] = doc
    print("Successfully parsed webpage")
    remove_songs_with_labels_from_df(df, labels_to_remove)
    return df


def start_driver_and_login(headless=False):
    options = Options()
    options.add_experimental_option("detach", True)

    if headless:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get("https://app.soundcharts.com/login")
    driver.maximize_window()

    # Find the username and password input fields by name
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
    time.sleep(5)
    return driver


def remove_songs_with_labels_from_df(df, labels):
    # Remove songs with labels in the list, check with lowercase
    for label in labels:
        df = df[~df["Labels"].str.lower().str.contains(label.lower())]

    return df


def run(headless):
    start_time = time.time()

    try:
        driver = start_driver_and_login(headless)

        # country_list = ["GLOBAL", "AR", "AU", "AT", "BY", "BE", "BO", "BR", "BG", "CA", "CL", "CO", "CR", "CY", "CZ", "DK", "DO", "EC", "EG", "SV",
        #                 "EE", "FI", "FR", "DE", "GR", "GT", "HN", "HK", "HU", "IS", "IN", "ID", "IE", "IL", "IT", "JP", "LV", "KZ", "LT", "LU",
        #                 "MY", "MX", "MA", "NL", "NZ", "NI", "NO", "NG", "PK", "PA", "PY", "PE", "PH", "PL", "PT", "RO", "SG", "SK", "KR", "ZA", "ES",
        #                 "SE", "CH", "TW", "TH", "TR", "UA", "AE", "GB", "US", "UY", "VN", "VE"]

        country_list = ["BG"]

        platform_list = ["spotify", "apple-music"]
        filters_list = ["no_labels"]

        labels_to_remove = ["sony", 'umg', 'warner', 'independent', 'universal', 'warner music', 'sony music', 'universal music', "yzy"]

        results_dict = {}

        count = 0
        for country in country_list:
            for platform in platform_list:
                for filters in filters_list:
                    try:
                        page = Link("song", country, platform, filters)
                        results_dict[f"{page.country}_{page.platform}"] = parse_webpage(driver, page.link, labels_to_remove)
                        count += 1
                        print(f"Finished {count}/{len(country_list) * len(platform_list) * len(filters_list)}")
                    except Exception as e:
                        print(e)
                        pass

        def output_to_excel(excel_dict):
            time_string = time.strftime("%Y-%m-%d %H-%M-%S")
            filename = f"soundcharts_{time_string}.xlsx"
            with pd.ExcelWriter(filename) as writer:
                for sheet_name, df in excel_dict.items():
                    df.to_excel(writer, sheet_name=sheet_name)

        output_to_excel(results_dict)
        end_time = time.time()
        print(f"Time taken: {round((end_time - start_time) / 60)}m:{round((end_time - start_time) % 60)}s")

    except Exception as e:
        print(e)


if __name__ == "__main__":
    run(headless=False)
