from __future__ import print_function
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from scrape import *
import datetime
import json
import time

import pprint


def write_line_to_file(filename, data):
    """
    output the current job title, company, job id, then write
    the scraped data to file
    """
    job_title = data["job_info"]["job_title"]
    company   = data["job_info"]["company"]
    job_id    = data["job_info"]["job_id"]
    message = u"Writing data to file for job listing:"
    message += "\n  {}  {};   job id  {}\n"
    try:
        print(message.format(job_title, company, job_id))
    except Exception as e:
        print("Encountered a unicode encode error while attempting to print " \
                    "the job post information;  job id {}".format(job_id))
    with open(filename, "a") as f:
        f.write(json.dumps(data) + '\n')

def wait_for_clickable_element(driver, delay, selector):
    """use WebDriverWait to wait for an element to become clickable"""
    obj = WebDriverWait(driver, delay).until(
            EC.element_to_be_clickable(
                (By.XPATH, selector)
            )
        )
    return obj  

def wait_for_clickable_element_css(driver, delay, selector):
    """use WebDriverWait to wait for an element to become clickable"""
    obj = WebDriverWait(driver, delay).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, selector)
            )
        )
    return obj  

def link_is_present(driver, delay, selector, index, results_page):
    """
    verify that the link selector is present and print the search 
    details to console. This method is particularly useful for catching
    the last link on the last page of search results
    """
    print(selector)
    try:
        WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, selector)))
        print(f"Scraping data for result {index} on results page {results_page}")
    except Exception as e:
        print(e)
        if index < 25:
            print("Was not able to wait for job_selector to load. Search results may have been exhausted.")           
            return True
        else:
            return False
    return True 


def search_suggestion_box_is_present(driver, selector, index, results_page):
    """
    check results page for the search suggestion box,
    as this causes some errors in navigate search results.
    """
    if (index == 1) and (results_page == 1):
        try:
            # This try-except statement allows us to avoid the 
            # problems cause by the LinkedIn search suggestion box
            driver.find_element_by_css_selector("div.suggested-search.bd")
        except Exception as e:
            pass
        else:
            return True
    else:
        return False

def next_results_page(driver, delay):
    """
    navigate to the next page of search results. If an error is encountered
    then the process ends or new search criteria are entered as the current 
    search results may have been exhausted.
    """
    try:
        # wait for the next page button to load
        print("  Moving to the next page of search results... \n" \
                "  If search results are exhausted, will wait {} seconds " \
                "then either execute new search or quit".format(delay))
        wait_for_clickable_element_css(driver, delay, "a.next-btn")
        # navigate to next page
        driver.find_element_by_css_selector("a.next-btn").click()
    except Exception as e:
        print ("\nFailed to click next page link; Search results " \
                                "may have been exhausted\n{}".format(e))
        raise ValueError("Next page link not detected; search results exhausted")
    else:
        # wait until the first job post button has loaded
        first_job_button = "a.job-title-link"
        # wait for the first job post button to load
        wait_for_clickable_element_css(driver, delay, first_job_button)

def go_to_specific_results_page(driver, delay, results_page):
    """
    go to a specific results page in case of an error, can restart 
    the webdriver where the error occurred.
    """
    if results_page < 2:
        return
    current_page = 1
    for i in range(results_page):
        current_page += 1
        time.sleep(5)
        try:
            next_results_page(driver, delay)
            print("\n**************************************************")
            print("\n\n\nNavigating to results page {}" \
                  "\n\n\n".format(current_page))
        except ValueError:
            print("**************************************************")
            print("\n\n\n\n\nSearch results exhausted\n\n\n\n\n")

def print_num_search_results(driver, keyword, location):
    """print the number of search results to console"""
    # scroll to top of page so first result is in view
    driver.execute_script("window.scrollTo(0, 0);")
    selector = "div.results-context div strong"
    try:
        num_results = driver.find_element_by_css_selector(selector).text
    except Exception as e:
        num_results = ''
    print("**************************************************")
    print("\n\n\n\n\nSearching  {}  results for  '{}'  jobs in  '{}' " \
            "\n\n\n\n\n".format(num_results, keyword, location))


class LIClient(object):
    def __init__(self, driver, **kwargs):
        self.driver         =  driver
        self.username       =  kwargs["username"]
        self.password       =  kwargs["password"]
        self.filename       =  kwargs["filename"]

    def driver_quit(self):
        self.driver.quit()

    def login(self):
        """login to linkedin then wait 3 seconds for page to load"""
        # Enter login credentials
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "username")))
        elem = self.driver.find_element_by_id("username")
        elem.send_keys(self.username)
        elem = self.driver.find_element_by_id("password")
        elem.send_keys(self.password)
        # Enter credentials with Keys.RETURN
        elem.send_keys(Keys.RETURN)
        # Wait a few seconds for the page to load
        time.sleep(3)

    def enter_search_keys(self):
        """
        execute the job search by entering job and location information.
        The location is pre-filled with text, so we must clear it before
        entering our search.
        """
        keyword_Xpath = "//*[contains(@id,'jobs-search-box-keyword-id')]"
        location_Xpath = "//*[contains(@id,'jobs-search-box-location-id')]"
        WebDriverWait(self.driver, 6).until(EC.presence_of_element_located((By.XPATH, keyword_Xpath)))

        # Enter search criteria
        elem = self.driver.find_element_by_xpath(keyword_Xpath)
        elem.send_keys(self.keyword)
        
        # clear the text in the location box then enter location
        elem = self.driver.find_element_by_xpath(location_Xpath)
        elem.send_keys(self.location)
        
        elem.send_keys(Keys.RETURN)
        time.sleep(3)

    def sort_by_date(self):
        button = '//div[@class="relative mr2"]'
        option_path = '//label[@for="advanced-filter-sortBy-DD"]'
        # Click more filter options
        self.driver.find_element_by_xpath(button).click()
        time.sleep(1)
        # Click sort by date
        self.driver.find_element_by_xpath(option_path).click()
        time.sleep(1)
        # Click show results
        self.driver.find_element_by_xpath("//button[contains(@class,'filters-show-results-button')]").click()
        time.sleep(1)

    def navigate_search_results(self):
        job_ads = {}
        page_nr = 1
        isLastPage = False
        while not isLastPage:
            # Give enough time for all job postings to load
            time.sleep(2)
            # Collect listed job adverts on page
            jobs_listings = self.driver.find_elements_by_xpath("//li[contains(@data-occludable-entity-urn,'_jobPosting:')]")
            print(f"Found: {len(jobs_listings)} job postings")
            for job_item in jobs_listings:
                # Scroll to specific job advert in list, this trigger the javascript to load related data like the href
                ActionChains(self.driver).move_to_element(job_item).perform()
                # Click on ad advert to trigge javascript to load even more data like views
                job_item.click()
                time.sleep(1)
                # Extract job url
                job_url = job_item.find_element_by_xpath(".//a[@data-control-id]").get_attribute("href")
                # Extract job id
                job_id = job_item.find_element_by_xpath(".//div[@data-job-id]").get_attribute("data-job-id")
                views, post_age= extract_views_age(self.driver)
                job_ads[job_id] = {"num_views": views, "post_age": post_age, "job_url": job_url}
            page_nr += 1
            if page_nr == 2:
                isLastPage = True
            try:
                self.driver.find_element_by_xpath(f"//button[@aria-label='Pagina {page_nr}']").click()
            except:
                print(f"Ended scraping at page {page_nr-1}")
                isLastPage = True
        for job_id, job_data in job_ads.items():
            premium = True
            print(f'job ID {job_id}')
            job_url = job_data['job_url']
            self.driver.get(job_url)
            try:
                WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'jobs-premium-applicant-insights')]")))
            except:
                print("No premium data available...")
                premium=False
            job_data.update(scrape_page(self.driver, premium=premium))
        return job_ads
        
        

        
        pprint.pprint(job_ads)
    # Scrape page and prepare to write the data to file
    # data = scrape_page(driver, keyword=keyword, location=location, dt=date)
    # # Write data to file
    # write_line_to_file(filename, data)
    # # Return to 
    # driver.execute_script("window.history.go(-1)")


        # extract_transform_load(driver, job_url, self.keyword, self.location, date, self.filename)
        # while not search_results_exhausted:
        #     for i in range(1,26):  # 25 results per page
        #         # define the css selector for the blue 'View' button for job i
        #         job_selector = list_element_tag + str(i) + ']'
        #         if search_suggestion_box_is_present(driver, job_selector, i, results_page):
        #             continue
        #         # wait for the selector for the next job posting to load.
        #         # if on last results page, then throw exception as job_selector 
        #         # will not be detected on the page
        #         if not link_is_present(driver, delay, job_selector, i, results_page):
        #             continue
        #         robust_wait_for_clickable_element(driver, delay, job_selector)
        #         extract_transform_load(driver, delay, job_selector, date, self.keyword, self.location, self.filename)
        #     # attempt to navigate to the next page of search results
        #     # if the link is not present, then the search results have been 
        #     # exhausted
        #     try:
        #         next_results_page(driver, delay)
        #         print("\n**************************************************")
        #         print("\n\n\nNavigating to results page  {}" \
        #               "\n\n\n".format(results_page + 1))
        #     except ValueError:
        #         search_results_exhausted = True
        #         print("**************************************************")
        #         print("\n\n\n\n\nSearch results exhausted\n\n\n\n\n")
        #     else:
        #         results_page += 1



        
