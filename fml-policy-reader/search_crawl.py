import time
import os
import json
import tldextract
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

def _get_company_data(file_path="../assets/company_data.txt"):

    with open(file_path, "r", encoding="utf-8") as f:
        data = f.readlines()

    source_data = []
    no_url = 0

    for counter, row in enumerate(data):
        if counter > 0:  # Skip the header row
            row = row.strip().split("\t")
            company = {
                'company_name': row[0],
                'legal_name': row[1],
                'url': row[2]
            }
            if not company['url']:
                no_url += 1
            source_data.append(company)

    print(f"Number of companies: {len(source_data)}")
    print(f"Number of companies without URL: {no_url}")

    url_oriented_data = {}
    for company in source_data:
        url = company['url']
        tld = _extract_tld(url)
        if tld:
            if tld not in url_oriented_data:
                url_oriented_data[tld] = {}
                url_oriented_data[tld]['companies'] = []
            url_oriented_data[tld]['companies'].append(company)

    print(f"Number of companies with unique URL: {len(url_oriented_data)}")
    return url_oriented_data

def _extract_tld(url):
    if url is None or url == "":
        return None
      
    if not url.startswith("http"):
        url = f"https://{url}"
    
    extracted = tldextract.extract(url)
    # Combine the domain and suffix (TLD)
    tld = f"{extracted.domain}.{extracted.suffix}"
    return tld


def _process_url(data, driver):
    print(data)
    url = _extract_tld(data["companies"][0]['url'])
    return _query_google(url, driver)


def _query_google(url, driver):    
    log = {}
    log["timestamp"] = time.time()
    try:
        search_query = "family maternity leave paternity HR policy".replace(" ", "+")
        # Navigate to Google
        goog_url = "https://www.google.com/search?q=" + search_query + "+site%3A" + url + "&oq=" + search_query + "+site%3A" + url + "&sourceid=chrome&ie=UTF-8"
        log["url"] = goog_url
        driver.get(goog_url)
                
        # Wait for results to load
        time.sleep(15)
        print("Results loaded")
        page_source = driver.page_source
        log["page_source"] = page_source
    except Exception as e:
        print(f"An error occurred while querying Google: {e}")
        log["error"] = str(e)
    return log


def setup():
    """
    Set up the necessary directories and files to parse company
    information
    """
    company_data = _get_company_data()
    print(f"found {len(company_data)} viable company URLs")
    # we'll make a directory for each company, if we need it
    new_setup = 0
    for company in company_data.items():
        os.makedirs(f"../assets/{company}", exist_ok=True)
        # check if the file exists, if no, add it from the source
        if not os.path.exists(f"../assets/{company}/company_data.json"):
            with open(f"../assets/{company}/company_data.json", "w", encoding="utf-8") as f:
                f.write(json.dumps(company_data[company]))
                new_setup += 1
    print(f"Wrote {new_setup} new company data files")

def process():
    """
    Process local company data (filesystem) and crawl the URLs 
    by querying Google and saving the HTML results, if possible
    """
    driver_path ="./chromedriver" 
    service = Service(executable_path=driver_path)

    # Initialize the Chrome driver with the Service object
    driver = webdriver.Chrome(service=service)

    for root, _, files in os.walk("../assets"):
        if "company_data.json" in files:
            with open(f"{root}/company_data.json", "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    complete = False
                    if 'status' in data:
                        if data['status'] == "complete":
                            complete = True
                    if not complete:
                        response = _process_url(data, driver)
                        if "crawl" not in data:
                            data["crawl"] = []
                        data["crawl"].append(response)
                        data["status"] = "complete"
                        with open(f"{root}/company_data.json", "w", encoding="utf-8") as f:
                            f.write(json.dumps(data))
                    else:
                        print("Already crawled")
                except Exception as e:
                    print(f"An error occurred while processing company data: {e}")
        else:
            print("No company data file found")
    driver.quit()

if __name__ == "__main__":
    setup()
    process()
