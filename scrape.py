from __future__ import print_function
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import datetime
import json
import time


def job_data(driver):
    job_info = {
        # "job_title"        :  "h1.title",
        # "company"          :  "span.company",
        # "location"         :  "h3.location",
        # "employment_type"  :  "div.employment div.content div.rich-text",
        # "industry"         :  "div.industry div.content div.rich-text",
        # "experience"       :  "div.experience div.content div.rich-text",
        # "job_function"     :  "div.function div.content div.rich-text",
        "description_textcontent"      :  ["div#job-details", "textContent"],
        "description_innertext"        :  ["div#job-details", "innerText"],
        "description_innerHTML"        :  ["div#job-details", "innerHTML"],
        "description_details"          :  ["div.jobs-description__details", "textContent"]
    }
    # # click the 'read more' button to reveal more about the job posting
    # try:
    #     driver.find_element_by_xpath("//button[@aria-label='Klik om meer van de beschrijving te zien']").click()
    # except Exception as e:
    #     print("Error in attempting to click 'reveal details' button", e)
    for key, (selector , attribute) in job_info.items():
        try:
            job_info[key] = driver.find_element_by_css_selector(selector).get_attribute(attribute)
        except Exception as e:
            job_info[key] = ""
    return job_info

def num_applicants(driver):
    selector = "span.jobs-unified-top-card__applicant-count"
    try:
        num_applicants = driver.find_element_by_css_selector(selector).text
        return num_applicants
    except:
        print("Number of applicants not found...")   

def extract_views_age(driver):
    data = [i.text for i in driver.find_elements_by_css_selector("span.jobs-details-top-card__bullet")]
    views = ''.join(list(filter(lambda x: 'weergaven' in x, data)))
    post_age = ''.join(list(filter(lambda x: 'geleden' in x, data)))
    views = [int(i) for i in views.split() if i.isdigit()]
    # views wil be an empty list if no views are extracted thus we need to catch this indexing error
    try:
        return views[0], post_age
    except:
        return 0, post_age

def applicants_education(driver):
    """return dictionary of applicant education levels"""
    education_selector = "table.applicants-education-table.comparison-table tbody tr"
    try:
        education = driver.find_elements_by_css_selector(education_selector)
        if education:
            # grab the degree type and proportion of applicants with that
            # degree.
            remove = ["have", "a", "Degree", "degrees", "(Similar", "to", "you)"]
            edu_map = list(map(
                    lambda edu: list(filter(
                            lambda word: word not in remove, 
                            edu
                        )), 
                    [item.text.split() for item in education]
                ))
            # store the education levels in a dictionary and prepare to 
            # write it to file
            edu_dict = {
                "education" + str(i + 1) : { 
                                    "degree" : ' '.join(edu_map[i][1:]), 
                                    "proportion": edu_map[i][0]
                                } 
                for i in range(len(edu_map))
            }
            return edu_dict
    except Exception as e:
        print("error acquiring applicants education")
        print(e)
    return {}

def scrape_page(driver, premium):
    # wait ~1 second for elements to be dynamically rendered
    time.sleep(1.2)
    containers = [
        "div#job-details",                         # job content
        "div.jobs-premium-applicant-insights",     # applicants skills
    ]
    for container in containers:
        try:
            WebDriverWait(driver, .25).until(EC.presence_of_element_located((By.CSS_SELECTOR, container)))
        except Exception as e:
            print(f"timeout error waiting for container to load or element not found: {container}")
    
    data = {
        "num_applicants"    :  num_applicants(driver),
        "job data"          :  job_data(driver)

    }

    return data
