from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from client import LIClient
from settings import search_keys
import argparse
import time
import json

def parse_command_line_args():
    parser = argparse.ArgumentParser(description="""
        parse LinkedIn search parameters
        """)
    parser.add_argument('--username', default=search_keys['username'], type=str,
        help="""
        enter LI username
        """)
    parser.add_argument('--password', default=search_keys['password'], type=str,
        help="""
        enter LI password
        """)
    parser.add_argument('--keyword', default=search_keys['keywords'], nargs='*', 
        help="""
        enter search keys separated by a single space. If the keyword is more
        than one word, wrap the keyword in double quotes.
        """)
    parser.add_argument('--location', default=search_keys['locations'], nargs='*',
        help="""
        enter search locations separated by a single space. If the location 
        search is more than one word, wrap the location in double quotes.
        """)
    parser.add_argument('--filename', type=str, default=search_keys['filename'], nargs='?', 
        help="""
        specify a filename to which data will be written. Defaults to
        'output.txt'
        """)
    parser.add_argument('--chrome_profile', type=str, default=search_keys['chrome_profile'], nargs='?', 
        help="""specify the path to the chrome profile to which data will be written.""")
    return vars(parser.parse_args())

if __name__ == "__main__":
    search_keys = parse_command_line_args()

    # Load cookies from user profile, this helps us skip security checks at login
    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir={search_keys['chrome_profile']}")

    # Initialize selenium webdriver
    driver = webdriver.Chrome('C:/Python projects/chromedriver.exe', options=chrome_options)

    # Go to linkedin
    driver.get("https://www.linkedin.com/jobs/")

    # Initialize LinkedIn web client
    liclient = LIClient(driver, **search_keys)
    
    assert isinstance(search_keys["keyword"], list) and isinstance(search_keys["location"], list)

    for keyword in search_keys["keyword"]:
        for location in search_keys["location"]:
            liclient.keyword  = keyword
            liclient.location = location
            liclient.enter_search_keys()
            liclient.sort_by_date()
            job_data = liclient.navigate_search_results()

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(job_data, f, ensure_ascii=False, indent=4)
    liclient.driver_quit()
