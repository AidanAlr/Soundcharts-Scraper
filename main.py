import time

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
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


def parse_rank(rank):
    return [s.text for s in rank]


def scroll(driver, scroll_amount):
    if scroll_amount == 0:
        return
    try:
        element = WebDriverWait(driver, 10).until(lambda driver: driver.find_element(By.CSS_SELECTOR, "div.sc-gKLXLV.fAiEjs.custom-scrollbar"))
        if element:
            driver.execute_script("arguments[0].scrollTop += arguments[0].scrollHeight*0.2*arguments[1]", element, scroll_amount)
            print(f"Scrolled down {scroll_amount * 20}%")
            time.sleep(1)
    except Exception as e:
        print("Could not scroll")


def make_dataframe(*args):
    df = pd.DataFrame()
    for arg in args:
        df = pd.concat([df, pd.DataFrame(arg)], axis=1)
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
        down_button = driver.find_elements(By.CSS_SELECTOR, "div.sc-kGeDwz.irzRFw")
        down_button[1].click()
        time.sleep(0.1)
        down_button_2 = driver.find_elements(By.CSS_SELECTOR, "div.sc-kGeDwz.jexWuv")
        down_button_2[0].click()
        time.sleep(0.1)
        # print("Sorted by DOC")
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


def remove_substring_from_string(substring, string):
    return string.replace(substring, "")


def label_filter(label_list):
    filtered_labels = ["sony", 'umg', 'warner', 'independent', 'universal', 'warner music', 'sony music', 'universal music']


def parse_labels(labels):
    labels = [div.text for div in labels]
    labels = [remove_substring_from_string("Unknown", label) for label in labels]
    labels = [remove_substring_from_string("Self released", label) for label in labels]
    labels = [label.replace("\n", "-") for label in labels]
    return labels


def parse_webpage_once(driver, url, labels_to_remove, scroll_amount) -> pd.DataFrame():
    general_css_selector = {
        "songs": "div.sc-cMhqgX.hQLcyr",
        "artists": "div.sc-esOvli.cfpVgy",
        "links": "img.sc-epnACN.ksrdaN",
        "rank": "div.sc-hENMEE.deWhnr",
        "doc": "div.sc-hmyDHa.jWjosp",
        "labels": "div.sc-hAcydR.gdSjQR",
    }
    # songs, artists, links, labels, rank, doc = None, None, None, None, None, None
    # sorted_by_doc = False
    # while not songs or not artists or not links or not rank or not sorted_by_doc or not doc:
    driver.get(url)
    # Cannot be lower than 5
    time.sleep(6)
    sorted_by_doc = sort_by_doc(driver)
    time.sleep(0.25)
    scroll(driver, scroll_amount)
    time.sleep(1)

    songs = driver.find_elements(By.CSS_SELECTOR, "div.sc-eTuwsz.jWHscE")
    links = driver.find_elements(By.CSS_SELECTOR, general_css_selector["links"])
    artists = driver.find_elements(By.CSS_SELECTOR, general_css_selector["artists"])
    rank = driver.find_elements(By.CSS_SELECTOR, general_css_selector["rank"])
    doc = driver.find_elements(By.CSS_SELECTOR, general_css_selector["doc"])
    labels = driver.find_elements(By.CSS_SELECTOR, general_css_selector["labels"])

    if len(songs) == len(artists) == len(links) == len(rank) == len(doc) == len(labels):
        print(f"SNG/ART/LINK/RANK/DOC/LABELS ({len(songs)})")
    else:
        print("Length of lists are not equal")

    songs = [div.text for div in songs]
    links = [parse_img_link(link) for link in links]
    artists = extract_names([div.text for div in artists])
    rank = parse_rank(rank)
    doc = [div.text for div in doc]
    labels = parse_labels(labels)

    # create dataframe with columns
    df = pd.DataFrame()
    df["rank"] = rank
    df["Song"] = songs
    df["Artists"] = artists
    df["Labels"] = labels
    df["Link"] = links
    df["DOC"] = doc

    df = remove_songs_with_labels_from_df(df, labels_to_remove)
    return df


def parse_webpage(driver, url, labels_to_remove) -> pd.DataFrame():
    print("Parsing webpage: " + url)
    result_dict = {
        1: parse_webpage_once(driver, url, labels_to_remove, scroll_amount=0),
        2: parse_webpage_once(driver, url, labels_to_remove, scroll_amount=1),
        3: parse_webpage_once(driver, url, labels_to_remove, scroll_amount=2),
        4: parse_webpage_once(driver, url, labels_to_remove, scroll_amount=3),
        5: parse_webpage_once(driver, url, labels_to_remove, scroll_amount=4),
    }

    # Concat values in result dict into a single dataframe
    result_df = pd.concat(result_dict.values(), axis=0)

    # Remove rows that have the same song as another row
    result_df = result_df.drop_duplicates(subset="Song", keep="first")
    print("Successfully parsed webpage")
    return result_df


def start_driver_and_login(detach=False):
    options = Options()
    if detach:
        options.add_experimental_option("detach", True)

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
    time.sleep(4)
    return driver


def remove_songs_with_labels_from_df(df, labels):
    # Remove songs with labels in the list, check with lowercase
    for label in labels:
        df = df[~df["Labels"].str.lower().str.contains(label.lower())]

    return df


def run(headless):
    start_time = time.time()

    # try:
    driver = start_driver_and_login(headless)

    country_list = ["GLOBAL", "AR", "AU", "AT", "BY", "BE", "BO", "BR", "BG", "CA", "CL", "CO", "CR", "CY", "CZ", "DK", "DO", "EC", "EG", "SV",
                    "EE", "FI", "FR", "DE", "GR", "GT", "HN", "HK", "HU", "IS", "IN", "ID", "IE", "IL", "IT", "JP", "LV", "KZ", "LT", "LU",
                    "MY", "MX", "MA", "NL", "NZ", "NI", "NO", "NG", "PK", "PA", "PY", "PE", "PH", "PL", "PT", "RO", "SG", "SK", "KR", "ZA", "ES",
                    "SE", "CH", "TW", "TH", "TR", "UA", "AE", "GB", "US", "UY", "VN", "VE"]

    platform_list = ["spotify", "apple-music"]
    filters_list = ["no_labels"]

    labels_to_remove = ["sony", 'umg', 'warner', 'independent', 'universal', 'warner music', 'sony music', 'universal music', "yzy"]

    results_dict = {}

    time_per_request = 55
    estimated_time = time_per_request * len(country_list) * len(platform_list) * len(filters_list)
    print(f"Estimated time: {round(estimated_time / 60)}m:{round(estimated_time % 60)}s")

    count = 0
    for country in country_list:
        for platform in platform_list:
            for filters in filters_list:
                try:
                    page = Link("song", country, platform, filters)
                    df = parse_webpage(driver, page.link, labels_to_remove)
                    assert df
                    results_dict[f"{page.country}_{page.platform}"] = df
                    count += 1
                    print(f"Finished {count}/{len(country_list) * len(platform_list) * len(filters_list)}")
                    elapsed_time = time.time() - start_time
                    time_remaining = estimated_time - elapsed_time
                    print(f"Time remaining: {round(time_remaining / 60)}m:{round(time_remaining % 60)}s")

                except Exception as e:
                    pass

    def output_to_excel(excel_dict):
        time_string = time.strftime("%Y-%m-%d %H-%M-%S")
        filename = f"soundcharts_{time_string}.xlsx"
        with pd.ExcelWriter(filename) as writer:
            for sheet_name, df in excel_dict.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)

    output_to_excel(results_dict)
    end_time = time.time()
    print(f"Time taken: {round((end_time - start_time) / 60)}m:{round((end_time - start_time) % 60)}s")

    # except Exception as e:
    #     print(e)


if __name__ == "__main__":
    run(headless=True)
