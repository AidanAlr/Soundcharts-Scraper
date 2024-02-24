import math
import statistics
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

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


def append_row(df, row):
    return pd.concat([df, pd.DataFrame([row], columns=row.index)]
                     ).reset_index(drop=True)


def send_email_notification(recipient, subject, message, attachment_path):
    sender_email = 'aidanalrawi@icloud.com'
    smtp_key = 'H7qhF8DV2ysktrv0'
    recipient_email = recipient

    # Setup the email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))

    # Attach the CSV file
    with open(attachment_path, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header(
        'Content-Disposition',
        f'attachment; filename= {os.path.basename(attachment_path)}'
    )
    msg.attach(part)

    # Connect to the SMTP server
    try:
        server = smtplib.SMTP('smtp-relay.brevo.com', 587)
        server.starttls()
        server.login(sender_email, smtp_key)
    except Exception as e:
        print("Failed to connect to SMTP server:", e)
        return False

    # Send the email
    try:
        server.sendmail(sender_email, recipient_email, msg.as_string())
        print("Email notification sent successfully to:", recipient_email)
        return True
    except Exception as e:
        print("Failed to send email:", e)
        return False
    finally:
        server.quit()


def convert_seconds_to_time_str(seconds):
    minutes = math.floor(seconds / 60)
    seconds = math.floor(seconds % 60)
    return f"{minutes}m:{seconds}s"


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
        element = WebDriverWait(driver, 10).until(
            lambda drvr: drvr.find_element(By.CSS_SELECTOR, "div.sc-gKLXLV.fAiEjs.custom-scrollbar"))
        if element:
            driver.execute_script("arguments[0].scrollTop += arguments[0].scrollHeight*0.2*arguments[1]", element,
                                  scroll_amount)
            time.sleep(0.5)
    except Exception:
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
    def __init__(self, chart_type, country, platform, filters=None, custom_url=None):
        charts = {
            "spotify": "",
            "apple-music": "top-100-global",
            "shazam": "shazam-top-200-world",
            "soundcloud": "all-genres"
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

        self.link_string = f"https://app.soundcharts.com/app/market/charts?chart={self.chart}&chart_type={self.chart_type}&country={self.country}"
        if self.platform == "spotify":
            self.link_string += "&period=1"
        if self.filters:
            self.link_string += f"&filters={self.filters}"
        self.link_string += f"&platform={self.platform}"

        if custom_url:
            self.link_string = custom_url


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

    genre_list = ["Pop", "Rock", "Hip Hop", "Rap", "R&B", "Soul", "Jazz", "Blues", "Country", "Folk", "Reggae", "Dance",
                  "Electronic",
                  "Classical", "Metal", "Punk", "Indie", "Alternative", "World", "Latin", "K-Pop", "J-Pop", "Anime",
                  "Soundtrack",
                  "Children's Music", "Electro", "Latin", "Asian", "R&B", "Soul", "Funk", "Disco", "House", "Techno",
                  "Trance", "Dubstep",
                  "African", "American", "Asian", "European", "Indian", "Middle Eastern", "Oceanian", "Caribbean",
                  "Latin American",
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


def take_data_return_df(driver) -> pd.DataFrame():
    """
    This function extracts data from a webpage and returns it as a pandas DataFrame.

    Parameters:
    driver (webdriver): The selenium webdriver instance to interact with the webpage.

    Returns:
    pd.DataFrame: A DataFrame containing the extracted data from the webpage.

    """

    # CSS selectors for different elements on the webpage
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

    # Find elements on the webpage using the CSS selectors
    songs = driver.find_elements(By.CSS_SELECTOR, general_css_selector["songs"])
    links = driver.find_elements(By.CSS_SELECTOR, general_css_selector["links"])
    artists = driver.find_elements(By.CSS_SELECTOR, general_css_selector["artists"])
    rank = driver.find_elements(By.CSS_SELECTOR, general_css_selector["rank"])
    doc = driver.find_elements(By.CSS_SELECTOR, general_css_selector["doc"])
    labels = driver.find_elements(By.CSS_SELECTOR, general_css_selector["labels"])
    change = driver.find_elements(By.CSS_SELECTOR, general_css_selector["change"])
    genre = driver.find_elements(By.CSS_SELECTOR, general_css_selector["genre"])

    # Check if all elements have the same length
    if len(songs) == len(artists) == len(links) == len(rank) == len(doc) == len(labels) == len(change) == len(genre):
        # Parse the elements into lists
        songs = parse_songs(songs)
        links = [parse_img_link(link) for link in links]
        artists = extract_names([div.text for div in artists])
        rank = parse_rank(rank)
        doc = [div.text for div in doc]
        labels = parse_labels(labels)
        change = [div.text for div in change]
        genre = parse_genre(genre)

        # Create a dataframe with the parsed data
        df = pd.DataFrame()
        df["rank"] = rank
        df["Song"] = songs
        df["Artists"] = artists
        df["Labels"] = labels
        df["Link"] = links
        df["DOC"] = doc
        df["Change"] = change
        df["Genre"] = genre

        return df

    else:
        print("Inconsistent webpage schema trying again.")


def parse_webpage(driver, url) -> pd.DataFrame():
    """
    This function parses a webpage and extracts relevant data into a pandas DataFrame.

    Parameters:
    driver (webdriver): The selenium webdriver instance to interact with the webpage.
    url (str): The URL of the webpage to parse.

    Returns:
    pd.DataFrame: A DataFrame containing the parsed data from the webpage.

    """

    # Navigate to the specified URL
    driver.get(url)

    # Pause the execution for 6 seconds to allow the webpage to load
    time.sleep(6)

    # Sort the data on the webpage by DOC (Days on Chart)
    sort_by_doc(driver)

    result = []

    # Scroll the webpage 5 times to load more data
    scroll_count = 7
    for _ in range(scroll_count):
        # Pause the execution for 0.25 seconds between each scroll
        time.sleep(0.25)

        # Scroll the webpage and append the extracted data to the result list
        scroll(driver, 1)
        result.append(take_data_return_df(driver))

    # Concatenate all the dataframes in the result list into a single dataframe
    result_df = pd.concat(result, axis=0)

    # Remove songs with specified labels and more than 30 days on chart
    result_df = remove_songs_with_labels_from_df(result_df)
    # Filter out songs with more than 100 days on chart
    result_df = remove_songs_with_more_than_x_doc(result_df, 100)
    # Filter out songs with more than 1 artist
    result_df = result_df[~result_df["Artists"].str.contains("\n")]
    # Remove duplicate songs, keeping only the first occurrence
    result_df = result_df.drop_duplicates(subset="Song", keep="first")
    print("Parsing webpage: " + url + "(Success)")
    return result_df


def login_to_new_driver(detach=False) -> webdriver.Chrome():
    while True:
        try:
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
            time.sleep(15)

            if "app.soundcharts.com/login" not in driver.current_url:
                print("Successfully logged in")
                return driver

        except Exception:
            print("Could not log in, trying again in 5 seconds")
            time.sleep(5)


def output_to_excel_from_dict(excel_dict):
    time_string = time.strftime("%Y-%m-%d %H-%M-%S")
    filename = f"soundcharts_{time_string}.xlsx"
    with pd.ExcelWriter(filename) as writer:
        for sheet_name, df in excel_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    print(f"Saved to {filename}")


def remove_songs_with_labels_from_df(df):
    labels_to_remove = ["sony", 'umg', 'warner', 'independent', 'universal', 'warner music', 'sony music',
                        'universal music', "yzy", "Island",
                        "Def Jam",
                        "Republic", "Interscope", "Atlantic", "Columbia", "Capitol", "RCA", "Epic", "Sony Music",
                        "Warner Music", ]
    # Remove songs with labels in the list, check with lowercase
    for label in labels_to_remove:
        df = df[~df["Labels"].str.lower().str.contains(label.lower())]

    return df


def remove_songs_with_more_than_x_doc(df, days):
    df = df[df["DOC"].astype(int) < days]
    return df


def change_to_spotify(link):
    link = link.replace("overview", "trends")
    return link


def locate_and_move_to_spotify_chart(driver):
    charts = WebDriverWait(driver, 4).until(
        EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "path.recharts-curve.recharts-line-curve")))
    charts = min(charts, key=lambda x: x.location['x'] + x.location['y'])
    ActionChains(driver).move_to_element(charts).perform()
    tooltip_size = charts.size
    return tooltip_size


def get_streams(link, driver):
    attempts = 0
    link = change_to_spotify(link)
    while attempts < 4:
        streams = ""
        total_streams = []
        try:
            attempts += 1
            driver.get(link)
            time.sleep(5)

            # Find the parent element and move to it
            tooltip_size = locate_and_move_to_spotify_chart(driver)

            # Find the child element which holds the stream data
            mouse_shifts = 14
            for _ in range(mouse_shifts):
                # Move the mouse horizontally by 20% of the tooltip wrapper size
                if streams:
                    horizontal_move = tooltip_size['width'] * 0.04
                    ActionChains(driver).move_by_offset(horizontal_move, 0).perform()

                child_elements = driver.find_elements(By.CSS_SELECTOR, "div.sc-laTMn.ktlmrZ")
                child_elements = [element.text for element in child_elements][0].split("\n")
                date, daily_streams = child_elements[0], child_elements[-1]
                daily_streams = daily_streams.split(" ")[-1].replace(",", "")
                streams += f"{date} - {daily_streams}\n"

                if len(child_elements) > 2:
                    total_streams.append(child_elements[1].split(" ")[-1].replace(",", ""))

            if not total_streams:
                total_streams.append("0")

            return streams, total_streams[-1]

        except Exception as e:
            print("Could not get streams for:" + link)
            print(e)
            if attempts == 3:
                return "Error", "Error"


def parse_artist_if_multiple(artist):
    if "•" in artist:
        artist = artist.split("•")[0]
    artist = artist.strip().replace(" ", "-").lower()
    return artist


def get_spotify_followers_and_total_fans(artist, driver):
    artist = parse_artist_if_multiple(artist)
    link = f"https://app.soundcharts.com/app/artist/{artist}/overview"
    fans = ""
    spotify = ""
    try:
        driver.get(link)
        time.sleep(5)
        followers = WebDriverWait(driver, 5).until(
            lambda drvr: drvr.find_elements(By.CSS_SELECTOR, "div.sc-gleUXh.jjAkJt.social-evolution-details.clickable"))
        followers = [div.text for div in followers]
        spotify_followers = [follower for follower in followers if "spotify" in follower.lower()]

        if spotify_followers:
            spotify = spotify_followers[0].split("\n")[1].replace(",", "")

    except Exception:
        print("Could not get followers for:" + artist)

    try:
        total_fans = driver.find_element(By.CSS_SELECTOR, "div.sc-dUjcNx.VujJl")

        if total_fans and "Total fans" in total_fans.text:
            total_fans = total_fans.text.split("\n")[1].replace(",", "")
            fans = total_fans

    except Exception:
        print("Could not get total fans for:" + artist)

    # print(f"Spotify followers: {spotify}, Total fans: {fans} - {artist}")
    return spotify, fans


def parse_streams_into_columns(df):
    try:
        if df.empty:
            return None
        # Split the "Streams" column into separate columns for each date
        streams_df = df["Streams"].str.split("\n", expand=True)
        streams_df = pd.DataFrame(streams_df)
        streams_df.drop(streams_df.columns[-1], axis=1, inplace=True)

        # Extract column names from first row with all the dates
        # Find a full row with dates
        for i in range(len(streams_df)):
            if streams_df.iloc[i].str.contains(" - ").all():
                date_df = streams_df.iloc[i:]
                break

        # Set the first row as the column names
        streams_df.columns = date_df.iloc[0].str.split(" - ", expand=True)[0]

        # Drop last column
        streams_df = streams_df.drop(streams_df.columns[-1], axis=1)

        # Remove the dates from cells
        streams_df = streams_df.map(lambda x: x.split(" - ")[-1] if x else x)
        streams_df = streams_df.map(
            lambda x: x.replace(",", "") if isinstance(x, str) and x.replace(",", "").isdigit() else x)
        streams_df = streams_df.apply(pd.to_numeric, errors='coerce')

        last_day = streams_df[streams_df.columns[-1]]
        last_3_days_avg = streams_df[streams_df.columns[-3:]].mean(axis=1)

        temp_3_day = ((last_day - streams_df[streams_df.columns[-4]]) / streams_df[streams_df.columns[-4]] * 100)
        temp_5_day = (last_day - streams_df[streams_df.columns[-6]]) / streams_df[streams_df.columns[-6]] * 100
        temp_10_day = (last_day - streams_df[streams_df.columns[-11]]) / streams_df[streams_df.columns[-11]] * 100

        new_df = pd.DataFrame()
        new_df["Yesterday"] = streams_df[streams_df.columns[-2]]
        new_df["3_day_avg"] = last_3_days_avg
        new_df["3_day_%_change"] = temp_3_day
        new_df["5_day_%_change"] = temp_5_day
        new_df["10_day_%_change"] = temp_10_day

        for column in new_df.columns:
            # round if the value is a float and not infinite
            new_df[column] = new_df[column].apply(lambda x: round(x, 2) if x and not math.isinf(x) else x)

        return new_df
    except Exception as e:
        print("Could not parse streams into columns")
        print(e)


def reverse_streams_column(df):
    streams = df["Streams"]
    streams = streams.str.split("\n")
    streams = [stream[::-1] for stream in streams]
    streams = ["\n".join(stream) for stream in streams]
    streams = [stream.replace("\n - \n", "") for stream in streams]
    df["Streams"] = streams
    return df


def get_extra_song_chart_data(driver, extra_country_list, results_dict):
    ####
    # Extra tasks to get genre specific data from apple music
    # US, UK, Canada, Estonia, Ukraine, Lithuania, Latvia, Austria, Kazakhstan, Bulgaria, Hungary, Czechia
    alternative_chart_dict = {
        "US": "152",
        "GB": "153",
        "CA": "101",
        "EE": "108",
        "UA": "259",
        "LT": "124",
        "LV": "123",
        "AT": "92",
        "KZ": "272",
        "BG": "99",
        "HU": "118",
        "CZ": "105"
    }
    dance_chart_dict = {
        "US": "129",
        "GB": "128",
        "CA": "94",
        "EE": "99",
        "UA": "485",
        "LT": "111",
        "LV": "109",
        "AT": "90",
        "KZ": "517",
        "BG": "93",
        "HU": "104",
        "CZ": "96"
    }

    for country in extra_country_list:
        alternative_link = (
            f"https://app.soundcharts.com/app/market/charts?chart=alternative-{alternative_chart_dict[country]}&chart_type=song&country={country}&platform=apple-music")
        dance_link = f"https://app.soundcharts.com/app/market/charts?chart=dance-{dance_chart_dict[country]}&chart_type=song&country={country}&platform=apple-music"
        try:
            df = parse_webpage(driver, alternative_link)
            # Add the country and platform to the dataframe
            df["Country"] = country
            df["Platform"] = "apple-music"
            df["Genre"] = "Alternative"
            results_dict[f"{country}_{alternative_link}"] = df

            df = parse_webpage(driver, dance_link)
            df["Country"] = country
            df["Platform"] = "apple-music"
            df["Genre"] = "Dance"
            results_dict[f"{country}_{dance_link}"] = df

        except Exception as e:
            print(e)


def collect_all_genres_charts(driver, country_list, extra_country_list, platform_list, filters_list,
                              results_dict, test_mode) -> None:
    tasks = len(country_list) * len(platform_list) * len(filters_list) + len(extra_country_list) * 2
    count = 0
    for country in country_list:
        for platform in platform_list:
            for filters in filters_list:
                try:
                    # Create the link
                    page = Link("song", country, platform, filters)
                    # Parse the webpage
                    df = parse_webpage(driver, page.link_string)
                    if test_mode:
                        df = df.head(5)
                    # Add the country and platform to the dataframe
                    df["Country"] = country
                    df["Platform"] = platform
                    # Add the dataframe to the dictionary
                    results_dict[f"{page.country}_{page.platform}"] = df
                    count += 1
                    print(f"Parsed {count}/{tasks} pages")
                except Exception as e:
                    print(e)


def run_thread(country_list, extra_country_list, platform_list, filters_list, detach, thread_number,
               test_mode=False):
    """
    This function runs the data collection process using a single thread.

    Parameters:
    country_list (list): A list of countries to collect data from.
    extra_country_list (list): A list of additional countries to collect data from.
    platform_list (list): A list of platforms to collect data from.
    filters_list (list): A list of filters to apply during data collection.
    detach (bool): Whether to detach the webdriver after data collection.
    number_of_threads (int): The number of threads to use for data collection.
    test_mode (bool): Whether to run the function in test mode.

    """

    global final_df

    # Start the webdriver and login
    driver = login_to_new_driver(detach=detach)

    results_dict = {}

    # Collect all genres charts
    collect_all_genres_charts(driver, country_list, extra_country_list, platform_list, filters_list,
                              results_dict, test_mode)
    # Get extra song chart data
    get_extra_song_chart_data(driver, extra_country_list, results_dict)

    # Concatenate all the dataframes in the results dictionary into a single dataframe
    df = (pd.concat(results_dict.values(), axis=0))

    # Drop duplicates based on song
    df = df.drop_duplicates(subset="Song", keep="first")

    # Change the link to spotify
    df['Link'] = df['Link'].apply(change_to_spotify)

    # Reset the index
    df.reset_index(drop=True, inplace=True)

    # Loop through each row in the df and get the streams/total streams/followers/fans
    for index, row in df.iterrows():
        try:
            start_time = time.time()

            # Get the spotify followers and total fans
            spotify_followers, fans, *_ = get_spotify_followers_and_total_fans(row["Artists"], driver)
            row['Followers'] = spotify_followers
            row['Total_Fans'] = fans

            # Cast the followers and total fans to numeric
            row['Followers'] = pd.to_numeric(row['Followers'], errors='coerce')
            row['Total_Fans'] = pd.to_numeric(row['Total_Fans'], errors='coerce')

            if row['Total_Fans'] < 100_000:

                # Get the daily streams and total streams
                daily_streams, total_streams, *_ = get_streams(row["Link"], driver)
                # Add entire row to the dataframe
                row['Streams'] = daily_streams
                row['Total_Streams'] = total_streams

                # Cast the total streams to numeric
                row['Total_Streams'] = pd.to_numeric(row['Total_Streams'], errors='coerce')

                # Only add rows with total fans less than 100,000 and total streams less than 5,000,000
                if row['Total_Fans'] < 100_000 and row['Total_Streams'] < 5_000_000:
                    final_df = append_row(final_df, row)

            end_time = time.time()

            # Calculate the time remaining
            task_time_avg = end_time - start_time
            global time_remaining_dict
            time_remaining_dict[thread_number] = task_time_avg * (len(df) - int(index))
            time_remaining_string = convert_seconds_to_time_str(max(time_remaining_dict.values()))
            print(f"Thread {thread_number} got stats for {row['Song']} | {index}/{len(df)} | {time_remaining_string} remaining")

        except Exception as e:
            print(e)
            print("Problem getting data for:")
            print(row)

    print("Finished getting stats for all songs on this thread")


def apply_final_filters_and_formatting(df):
    # Concat the streams columns with the original dataframe
    df = pd.concat([df, parse_streams_into_columns(df)], axis=1)

    # Reverse the streams column
    df = reverse_streams_column(df)

    df['Streams'] = df['Streams'].apply(lambda x: x.lstrip(" - \n"))

    df["Song"] = df["Song"].astype(str)

    df.sort_values(by="Song", inplace=True)

    desired_order = ['Country', 'Platform', 'Genre', 'Labels', 'Artists', 'Followers',
                     'Total_Fans', 'Link', 'Song', 'DOC', 'rank', 'Change', 'Total_Streams', 'Streams', 'Yesterday',
                     '3_day_avg', '3_day_%_change', '5_day_%_change', '10_day_%_change']

    # Reorder the columns
    df = df[desired_order]

    country_dict = {
        "AR": "Argentina",
        "AU": "Australia",
        "AT": "Austria",
        "BY": "Belarus",
        "BE": "Belgium",
        "BO": "Bolivia",
        "BR": "Brazil",
        "BG": "Bulgaria",
        "CA": "Canada",
        "CL": "Chile",
        "CO": "Colombia",
        "CR": "Costa Rica",
        "CY": "Cyprus",
        "CZ": "Czech Republic",
        "DK": "Denmark",
        "DO": "Dominican Republic",
        "EC": "Ecuador",
        "EG": "Egypt",
        "SV": "El Salvador",
        "EE": "Estonia",
        "FI": "Finland",
        "FR": "France",
        "DE": "Germany",
        "GR": "Greece",
        "GT": "Guatemala",
        "HN": "Honduras",
        "HK": "Hong Kong",
        "HU": "Hungary",
        "IS": "Iceland",
        "IN": "India",
        "ID": "Indonesia",
        "IE": "Ireland",
        "IL": "Israel",
        "IT": "Italy",
        "JP": "Japan",
        "LV": "Latvia",
        "KZ": "Kazakhstan",
        "LT": "Lithuania",
        "LU": "Luxembourg",
        "MY": "Malaysia",
        "MX": "Mexico",
        "MA": "Morocco",
        "NL": "Netherlands",
        "NZ": "New Zealand",
        "NI": "Nicaragua",
        "NO": "Norway",
        "NG": "Nigeria",
        "PK": "Pakistan",
        "PA": "Panama",
        "PY": "Paraguay",
        "PE": "Peru",
        "PH": "Philippines",
        "PL": "Poland",
        "PT": "Portugal",
        "RO": "Romania",
        "SG": "Singapore",
        "SK": "Slovakia",
        "KR": "South Korea",
        "ZA": "South Africa",
        "ES": "Spain",
        "SE": "Sweden",
        "CH": "Switzerland",
        "TW": "Taiwan",
        "TH": "Thailand",
        "TR": "Turkey",
        "UA": "Ukraine",
        "AE": "United Arab Emirates",
        "GB": "United Kingdom",
        "US": "United States",
        "UY": "Uruguay",
        "VN": "Vietnam",
        "VE": "Venezuela"
    }

    df["Country"] = df["Country"].map(country_dict)

    return df


def run_with_threading(country_list, extra_country_list, platform_list, filters_list, detach,
                       number_of_threads, test_mode):
    """
    This function runs the data collection process using multiple threads.

    Parameters:
    country_list (list): A list of countries to collect data from.
    extra_country_list (list): A list of additional countries to collect data from.
    platform_list (list): A list of platforms to collect data from.
    filters_list (list): A list of filters to apply during data collection.
    detach (bool): Whether to detach the webdriver after data collection.
    number_of_threads (int): The number of threads to use for data collection.
    test_mode (bool): Whether to run the function in test mode.

    """
    # List to store the threads
    threads = []

    # If the number of threads is greater than the length of the country list, reduce the number of threads
    number_of_threads = min(number_of_threads, len(country_list))

    # Calculate the number of tasks per thread
    tasks_per_thread = len(country_list) // number_of_threads
    extra_tasks = len(country_list) % number_of_threads

    # Calculate the number of tasks per thread for the extra country list
    tasks_from_extra_country_list_per_thread = len(extra_country_list) // number_of_threads
    extra_tasks_from_extra_country_list = len(extra_country_list) % number_of_threads

    start = 0
    start_extra = 0

    for i in range(number_of_threads):
        end = start + tasks_per_thread + (1 if i < extra_tasks else 0)
        end_extra = start + tasks_from_extra_country_list_per_thread + (
            1 if i < extra_tasks_from_extra_country_list else 0)
        t = Thread(target=run_thread,
                   args=(
                       country_list[start:end], extra_country_list[start_extra:end_extra], platform_list, filters_list,
                       detach, i, test_mode))
        t.start()
        threads.append(t)

        start = end
        start_extra = end_extra

    for t in threads:
        t.join()

    global final_df
    final_df = apply_final_filters_and_formatting(final_df)

    completion_time = time.strftime("%Y-%m-%d %H-%M")
    file_path = f'soundcharts {completion_time}.csv'
    time.sleep(1)
    final_df.to_csv(file_path, index=False)
    print("Saved to csv: " + file_path)

    send_email_notification("jhlevy01@gmail.com",
                            'Song Scraping: SUCCESS',
                            'Your program is complete with no issues. Please check the results.',
                            file_path)

    send_email_notification("aidanalrawi@icloud.com",
                            'Chart Scraping: SUCCESS',
                            'Your program is complete with no issues. Please check the results.',
                            file_path)


if __name__ == "__main__":
    global final_df, time_remaining_dict
    time_remaining_dict = {}
    final_df = pd.DataFrame()
    pd.set_option('display.max_columns', 500)

    country_list = ["AR", "AU", "AT", "BY", "BE", "BO", "BR", "BG", "CA", "CL", "CO", "CR", "CY", "CZ", "DK", "DO",
                    "EC", "EG", "SV",
                    "EE", "FI", "FR", "DE", "GR", "GT", "HN", "HK", "HU", "IS", "IN", "ID", "IE", "IL", "IT", "JP",
                    "LV", "KZ", "LT", "LU",
                    "MY", "MX", "MA", "NL", "NZ", "NI", "NO", "NG", "PK", "PA", "PY", "PE", "PH", "PL", "PT", "RO",
                    ]

    extra_country_list = []
    platform_list = ["spotify", "apple-music", "shazam", "soundcloud"]
    filters_list = ["no_labels"]

    run_with_threading(country_list,
                       extra_country_list,
                       platform_list,
                       filters_list,
                       detach=False,
                       number_of_threads=3,
                       test_mode=False)
