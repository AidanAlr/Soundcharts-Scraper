import math
import time
from threading import Thread

import pandas as pd
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
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
        time.sleep(0.5)
        element = WebDriverWait(driver, 10).until(lambda drvr: drvr.find_element(By.CSS_SELECTOR, "div.sc-gKLXLV.fAiEjs.custom-scrollbar"))
        if element:
            driver.execute_script("arguments[0].scrollTop += arguments[0].scrollHeight*0.2*arguments[1]", element, scroll_amount)
            time.sleep(0.5)
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
            "spotify": "",
            "apple-music": "top-100-global",
            "shazam": "shazam-top-200-world"
        }
        self.filters_dict = {
            # "no_labels": "eyJmbHQiOiJTZWxmIHJlbGVhc2VkfFVua25vd24ifQ%3D%3D",
            "no_labels": "eyJmc2ciOiJBTExfR0VOUkVTIiwiZmx0IjoiU2VsZiByZWxlYXNlZHxVbmtub3duIn0%3D",

        }
        self.chart = charts[platform]
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


def parse_labels(labels):
    labels = [div.text for div in labels]
    labels = [remove_substring_from_string("Unknown", label) for label in labels]
    labels = [remove_substring_from_string("Self released", label) for label in labels]
    labels = [label.replace("\n", "-") for label in labels]
    return labels


def parse_genre(genre):
    songs_and_genres = [div.text for div in genre]

    genre_list = ["Pop", "Rock", "Hip Hop", "Rap", "R&B", "Soul", "Jazz", "Blues", "Country", "Folk", "Reggae", "Dance", "Electronic",
                  "Classical", "Metal", "Punk", "Indie", "Alternative", "World", "Latin", "K-Pop", "J-Pop", "Anime", "Soundtrack",
                  "Children's Music", "Electro", "Latin", "Asian", "R&B", "Soul", "Funk", "Disco", "House", "Techno", "Trance", "Dubstep",
                  "African", "American", "Asian", "European", "Indian", "Middle Eastern", "Oceanian", "Caribbean", "Latin American",
                  "Instrumental", "Spirituals", "Spoken", "Sports", "Others", "Unknown", "Mena"]

    def remove_before_first_newline(s):
        parts = s.split("\n")  # split the string into two parts at the first newline
        parts = [part.strip() for part in parts if part in genre_list]
        return "-".join(parts)  # join the parts back together with a hyphen

    genres = [remove_before_first_newline(song) for song in songs_and_genres]
    return genres


def parse_songs(songs_and_genre):
    songs_and_genres = [div.text for div in songs_and_genre]
    songs = [div.split("\n", 1)[0] for div in songs_and_genres]
    return songs


def take_data_return_df(driver, labels_to_remove, counter=0) -> pd.DataFrame():
    general_css_selector = {
        "songs": "div.sc-eTuwsz.jWHscE",
        "artists": "div.sc-esOvli.cfpVgy",
        "links": "img.sc-epnACN.ksrdaN",
        "rank": "div.sc-hENMEE.deWhnr",
        "doc": "div.sc-hmyDHa.jWjosp",
        "labels": "div.sc-hAcydR.gdSjQR",
        "change": "div.sc-ekulBa.jsSggV",
        "genre": "div.sc-eTuwsz.jWHscE"
    }
    songs = driver.find_elements(By.CSS_SELECTOR, general_css_selector["songs"])
    links = driver.find_elements(By.CSS_SELECTOR, general_css_selector["links"])
    artists = driver.find_elements(By.CSS_SELECTOR, general_css_selector["artists"])
    rank = driver.find_elements(By.CSS_SELECTOR, general_css_selector["rank"])
    doc = driver.find_elements(By.CSS_SELECTOR, general_css_selector["doc"])
    labels = driver.find_elements(By.CSS_SELECTOR, general_css_selector["labels"])
    change = driver.find_elements(By.CSS_SELECTOR, general_css_selector["change"])
    genre = driver.find_elements(By.CSS_SELECTOR, general_css_selector["genre"])

    if len(songs) == len(artists) == len(links) == len(rank) == len(doc) == len(labels) == len(change) == len(genre):
        # Replace the last output with the new one
        # sys.stdout.write("\r" + f"{counter}/4 SNG/ART/LINK/RANK/DOC/LABELS ({len(songs)} results)")
        songs = parse_songs(songs)
        links = [parse_img_link(link) for link in links]
        artists = extract_names([div.text for div in artists])
        rank = parse_rank(rank)
        doc = [div.text for div in doc]
        labels = parse_labels(labels)
        change = [div.text for div in change]
        genre = parse_genre(genre)

        # create dataframe with columns
        df = pd.DataFrame()
        df["rank"] = rank
        df["Song"] = songs
        df["Artists"] = artists
        df["Labels"] = labels
        df["Link"] = links
        df["DOC"] = doc
        df["Change"] = change
        df["Genre"] = genre

        df = remove_songs_with_labels_from_df(df, labels_to_remove)
        df = remove_songs_with_more_than_x_doc(df, 30)
        return df

    else:
        print("Genres: " + str(len(genre)))
        print("Songs: " + str(len(songs)))
        print("Artists: " + str(len(artists)))
        print("Links: " + str(len(links)))
        print("Rank: " + str(len(rank)))
        print("DOC: " + str(len(doc)))
        print("Labels: " + str(len(labels)))
        print("Change: " + str(len(change)))

        print("Length of lists are not equal")


def parse_webpage(driver, url, labels_to_remove, test_mode=False) -> pd.DataFrame():
    print("Parsing webpage: " + url)
    driver.get(url)
    # Cannot be lower than 5
    time.sleep(6)
    sort_by_doc(driver)

    result = []

    scroll_count = 5
    if test_mode:
        scroll_count = 1
    for i in range(scroll_count):
        time.sleep(0.25)
        scroll(driver, 1)
        result.append(take_data_return_df(driver, labels_to_remove, i))

    result_df = pd.concat(result, axis=0)
    result_df = result_df.drop_duplicates(subset="Song", keep="first")
    print("\n" + "Successfully parsed webpage")
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
    time.sleep(6)
    return driver


def output_to_excel_from_dict(excel_dict):
    time_string = time.strftime("%Y-%m-%d %H-%M-%S")
    filename = f"soundcharts_{time_string}.xlsx"
    with pd.ExcelWriter(filename) as writer:
        for sheet_name, df in excel_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    print(f"Saved to {filename}")


def remove_songs_with_labels_from_df(df, labels):
    # Remove songs with labels in the list, check with lowercase
    for label in labels:
        df = df[~df["Labels"].str.lower().str.contains(label.lower())]

    return df


def remove_songs_with_more_than_x_doc(df, days):
    df = df[df["DOC"].astype(int) < days]
    return df


def estimate_runtime(country_list, platform_list, filters_list):
    time_per_request = 22
    number_of_requests = len(country_list) * len(platform_list) * len(filters_list)
    estimated_time = time_per_request * number_of_requests
    print(f"Number of requests: {number_of_requests}")
    print(f"Estimated time: {math.floor(estimated_time / 60)}m:{round(estimated_time % 60)}s")


def change_to_spotify(link):
    link = link.replace("overview", "trends")
    return link


def print_current_songs_time_remaining():
    global songs_to_get_stats_for
    songs_to_get_stats_for -= 1

    print(f"{songs_to_get_stats_for} songs remaining. Estimated time: {math.floor(songs_to_get_stats_for * 4 / 60)}m:"
          f"{round(songs_to_get_stats_for * 4 % 60)}s")


def locate_and_move_to_spotify_chart(driver):
    charts = WebDriverWait(driver, 4).until(
        EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "path.recharts-curve.recharts-line-curve")))
    charts = min(charts, key=lambda x: x.location['x'] + x.location['y'])
    ActionChains(driver).move_to_element(charts).perform()
    tooltip_size = charts.size
    return tooltip_size


def get_streams(link, driver):
    try:
        print_current_songs_time_remaining()
        streams = ""
        attempts = 0
        link = change_to_spotify(link)
        while not streams and attempts < 4:
            attempts += 1
            driver.get(link)
            time.sleep(3)

            # Find the parent element and move to it
            tooltip_size = locate_and_move_to_spotify_chart(driver)

            # Find the child element which holds the stream data
            mouse_shifts = 11
            for i in range(mouse_shifts):
                # Move the mouse horizontally by 20% of the tooltip wrapper size
                if streams:
                    horizontal_move = tooltip_size['width'] * 0.05
                    ActionChains(driver).move_by_offset(horizontal_move, 0).perform()

                child_elements = driver.find_elements(By.CSS_SELECTOR, "div.sc-laTMn.ktlmrZ")
                child_elements = [element.text for element in child_elements][0].split("\n")
                date, daily_streams = child_elements[0], child_elements[-1]
                daily_streams = daily_streams.split(" ")[-1]
                streams += f"{date} - {daily_streams}\n"

        return streams

    except Exception as e:
        print("Could not get streams for:" + link)
        return "Error"


def get_followers(artist, driver):
    if "•" in artist:
        artist = artist.split("•")[0]

    artist = artist.strip().replace(" ", "-").lower()
    link = f"https://app.soundcharts.com/app/artist/{artist}/overview"
    followers = []
    attempts = 0
    while not followers and attempts < 3:
        try:
            attempts += 1
            driver.get(link)
            time.sleep(5)
            followers = WebDriverWait(driver, 5).until(
                lambda drvr: drvr.find_elements(By.CSS_SELECTOR, "div.sc-gleUXh.jjAkJt.social-evolution-details.clickable"))
            followers = [div.text for div in followers]
        except Exception as e:
            print("Could not get followers for:" + artist)
            pass

    if not followers:
        return "Error"
    spotify_followers = [follower for follower in followers if "spotify" in follower.lower()]
    spotify_followers = spotify_followers[0].split("\n")[1]
    return spotify_followers


def parse_streams_into_columns(df):
    # Split the "Streams" column into separate columns for each date
    streams_df = df["Streams"].str.split("\n", expand=True)
    streams_df = pd.DataFrame(streams_df)
    streams_df.drop(streams_df.columns[-1], axis=1, inplace=True)
    # Extract column names from first row
    streams_df.columns = streams_df.iloc[1].str.split(" - ", expand=True)[0]
    streams_df.to_csv("saved_here_2.csv", index=False)

    # Remove the dates from cells
    streams_df = streams_df.applymap(lambda x: x.split(" - ")[-1] if x else x)
    streams_df = streams_df.applymap(lambda x: int(x.replace(",", "")) if x and x.replace(",", "").isdigit() else x)
    streams_df = streams_df.apply(pd.to_numeric, errors='coerce')
    streams_df.to_csv("saved_here_3.csv", index=False)
    last_day = streams_df[streams_df.columns[-1]]

    last_3_days_avg = streams_df[streams_df.columns[-3:]].mean(axis=1)
    # if the value in the last day is nan  use last 3 days average
    last_day = last_day.combine_first(last_3_days_avg)
    temp_3_day = ((last_day - streams_df[streams_df.columns[-3]]) / streams_df[streams_df.columns[-3]] * 100)
    temp_7_day = (last_day - streams_df[streams_df.columns[-6]]) / streams_df[streams_df.columns[-6]] * 100
    temp_14_day = (last_day - streams_df[streams_df.columns[-11]]) / streams_df[streams_df.columns[-11]] * 100
    new_df = pd.DataFrame()
    new_df["Yesterday"] = streams_df[streams_df.columns[-1]]
    new_df["3_day_avg"] = last_3_days_avg
    new_df["3_day_%_change"] = temp_3_day
    new_df["7_day_%_change"] = temp_7_day
    new_df["14_day_%_change"] = temp_14_day
    new_df.to_csv("saved_here_4.csv", index=False)

    for column in new_df.columns:
        new_df[column] = new_df[column].apply(lambda x: round(x, 2) if isinstance(x, float) else x)

    return new_df


def run(country_list, platform_list, filters_list, labels_to_remove, detach, number_of_threads, test_mode=False):
    global project_tasks_completed
    global project_tasks

    driver = start_driver_and_login(detach=detach)

    results_dict = {}

    estimate_runtime(country_list, platform_list, filters_list)

    total_tasks = len(country_list) * len(platform_list) * len(filters_list)
    project_tasks += total_tasks

    count = 0
    for country in country_list:
        for platform in platform_list:
            for filters in filters_list:
                try:
                    # Start the timer
                    task_start_time = time.time()
                    # Create the link
                    page = Link("song", country, platform, filters)
                    # Parse the webpage

                    df = parse_webpage(driver, page.link, labels_to_remove, test_mode)
                    # Add the country and platform to the dataframe
                    df["Country"] = country
                    df["Platform"] = platform
                    # Add the dataframe to the dictionary
                    results_dict[f"{page.country}_{page.platform}"] = df

                    # End the timer
                    task_end_time = time.time()
                    count += 1

                    # Print the progress
                    time_per_request = task_end_time - task_start_time
                    total_task_time = time_per_request * project_tasks - project_tasks_completed
                    time_remaining = total_task_time - (time_per_request * count)

                    project_tasks_completed += 1
                    print(
                        f"Task {project_tasks_completed}/{project_tasks} completed - Time taken: "
                        f"{math.floor(time_per_request / 60)}m:{round(time_per_request % 60)}s "
                        f"- Time remaining: {math.floor(time_remaining / 60)}m:{round(time_remaining % 60)}s")
                except Exception as e:
                    print(e)
                    pass

    df = (pd.concat(results_dict.values(), axis=0))

    if test_mode:
        df = df.head(5)

    global songs_to_get_stats_for
    songs_to_get_stats_for += len(df)

    df["Streams"] = df["Link"].apply(get_streams, driver=driver)
    time.sleep(2)

    df["Followers"] = df["Artists"].apply(get_followers, driver=driver)

    print("df after followers")
    print(df)
    print("streams df")
    print(parse_streams_into_columns(df))
    df = pd.concat([df, parse_streams_into_columns(df)], axis=1)
    print(2)
    # Display last 4 columns
    print(df[df.columns[-4:]])

    # Drop rows with Yesterday less than 2000
    df = df[df["Yesterday"] > 2000]
    # Sort df by song
    df = df.sort_values(by="Song")
    df.to_csv("saved_here_2.csv", index=False)
    return df


def run_with_threading(country_list, platform_list, filters_list, labels_to_remove, detach, number_of_threads, test_mode=False):
    start_time = time.time()

    number_of_threads = number_of_threads
    threads = []

    if len(country_list) < number_of_threads:
        number_of_threads = len(country_list)

    tasks_per_thread = len(country_list) // number_of_threads
    extra_tasks = len(country_list) % number_of_threads

    start = 0
    for i in range(number_of_threads):
        end = start + tasks_per_thread + (1 if i < extra_tasks else 0)
        t = Thread(target=run, args=(country_list[start:end], platform_list, filters_list,
                                     labels_to_remove, detach, number_of_threads, test_mode))
        t.start()
        threads.append(t)
        start = end

    result_dfs = [t.join() for t in threads]

    for df in result_dfs:
        print(df)

    pd.concat(result_dfs, axis=0).to_csv(f"soundcharts_{time.strftime('%Y-%m-%d %H-%M-%S')}.csv", index=False)

    end_time = time.time()
    print(f"Finished - Time taken: {math.floor((end_time - start_time) / 60)}m:{round((end_time - start_time) % 60)}s")


if __name__ == "__main__":
    global songs_to_get_stats_for
    global project_tasks
    global project_tasks_completed
    project_tasks_completed = 0
    project_tasks = 0
    songs_to_get_stats_for = 0
    # COUNTRY_LIST = ["GLOBAL", "AR", "AU", "AT", "BY", "BE", "BO", "BR", "BG", "CA", "CL", "CO", "CR", "CY", "CZ", "DK", "DO", "EC", "EG", "SV",
    #                 "EE", "FI", "FR", "DE", "GR", "GT", "HN", "HK", "HU", "IS", "IN", "ID", "IE", "IL", "IT", "JP", "LV", "KZ", "LT", "LU",
    #                 "MY", "MX", "MA", "NL", "NZ", "NI", "NO", "NG", "PK", "PA", "PY", "PE", "PH", "PL", "PT", "RO", "SG", "SK", "KR", "ZA", "ES",
    #                 "SE", "CH", "TW", "TH", "TR", "UA", "AE", "GB", "US", "UY", "VN", "VE"]
    country_list = ["SE", "GB", "DE"]
    platform_list = ["spotify", "apple-music", "shazam"]
    filters_list = ["no_labels"]
    labels_to_remove = ["sony", 'umg', 'warner', 'independent', 'universal', 'warner music', 'sony music', 'universal music', "yzy", "Island"
                                                                                                                                     "Def Jam",
                        "Republic", "Interscope", "Atlantic", "Columbia", "Capitol", "RCA", "Epic", "Sony Music", "Warner Music", ]

    run_with_threading(country_list, platform_list, filters_list, labels_to_remove, detach=False, number_of_threads=4, test_mode=True)
