import click
import time, csv, json

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options


WAIT_PERIOD = 10


def save_execution_context(context):
    conf = {
        "profile_urls": context.user_profile_urls,
        "current_page": context.current_page,
        "total_search_results": context.total_search_results
    }
    with open("saved_content.json", "w") as fd:
        fd.write(json.dumps(conf))


def get_total_search_result(driver, context):
    try:
        WebDriverWait(driver, WAIT_PERIOD).until(EC.presence_of_element_located(
            (By.XPATH, '//main[@id="main"]/div/div/div')
        ))
        element = driver.find_element_by_xpath('//main[@id="main"]/div/div/div')
        value = str(element.text).strip()
        value = value.split(" ")[1]
        value = value.replace(",", "")
        value = int(str(value))
    except Exception as e:
        print(e)
        save_execution_context(context)
        return None
    return value


def get_searched_user_profile(context, driver):
    WebDriverWait(driver, WAIT_PERIOD).until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, 'li[class="reusable-search__result-container "]')
    ))

    elements = driver.find_elements_by_css_selector('li.reusable-search__result-container')

    def get_user_profile_url(elem):
        link_elem = elem.find_element_by_css_selector('a[class="app-aware-link"]')
        # link_elem = elem.find_element_by_xpath('//div[@class="entity-result"]/div/div[1]/div/a[@class="app-aware-link"]')
        if link_elem:
            href = link_elem.get_attribute("href")
            href = str(href)
            if href.rfind("FACETED_SEARCH") < 0:
                click.echo(click.style(f"Added: {href}.", fg="blue"))
                context.user_profile_urls.append(href)

    for elem in elements:
        get_user_profile_url(elem)


class LinkedInScrapper(object):
    INITIAL_OPEN_TO_WORK_URL = "https://www.linkedin.com/search/results/people/?geoUrn=%5B%22105769538%22%5D&keywords=open%20to%20work&origin=FACETED_SEARCH&page={}"

    # INITIAL_OPEN_TO_WORK_URL =
    # "https://www.linkedin.com/search/results/people/?geoUrn=%5B%22105769538%22%5D&keywords=open%20to%20work&origin=GLOBAL_SEARCH_HEADER&page={}"

    def __init__(self, email, password, headless=False, page_nums=None, num_pages=10):
        options = Options()
        options.headless = headless

        options.add_argument("start-maximized")
        options.add_argument("disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-application-cache')
        options.add_argument('--disable-gpu')
        options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Firefox(options=options)
        self.driver.get("https://www.linkedin.com")
        
        self.email = email
        self.password = password

        self.user_profile_urls = ["https://www.linkedin.com/in/jonathan-naf-8222b920a/"]
        self.user_emails = []
        self.current_page = 1
        self.total_search_results = 0
        self.num_of_profiles_per_page = num_pages
        self.page_nums = page_nums

        click.echo(click.style("Logging user into linkedIn", fg="blue"))
        
        email_element = self.driver.find_element_by_name("session_key")
        password_element = self.driver.find_element_by_name("session_password")
        sign_in_btn_element = self.driver.find_element_by_css_selector("button.sign-in-form__submit-button")

        email_element.clear()
        password_element.clear()

        email_element.send_keys(self.email)
        password_element.send_keys(self.password)

        sign_in_btn_element.click()

    @classmethod
    def _load_save_context(cls, instance):
        with open("saved_content.json", "r") as fd:
            try:
                data = json.loads(fd.read())
                instance.user_profile_urls = data['profile_urls']
                instance.current_page = data['current_page']
                instance.total_search_results = data['total_search_results']
            except Exception:
                pass
        return instance

    @property
    def number_of_pages(self):
        if self.page_nums:
            return self.page_nums
        if self.total_search_results == 0:
            return 0
        return round(self.total_search_results/self.num_of_profiles_per_page)

    def feed_page(self):
        try:
            click.echo(click.style("User successfully logged in", blink=True, fg="green"))

            click.echo(click.style("Loading linkedin feed.", fg="blue"))
            WebDriverWait(self.driver, WAIT_PERIOD).until(EC.presence_of_element_located(
                (By.XPATH, '//li[@class="global-nav__primary-item"]')
            ))
        except Exception as e:
            print(e)

    def search_for_people_open_to_work(self):
        try:
            click.echo(click.style(f"Opening page {self.current_page} for people open to work", fg="blue"))
            self.driver.get(self.INITIAL_OPEN_TO_WORK_URL.format(self.current_page))
            click.echo(click.style(f"Page {self.current_page} opened.", fg="green"))
            if self.total_search_results == 0:
                total_results = get_total_search_result(self.driver, self)
                if total_results:
                    self.total_search_results = total_results
                    click.echo(click.style(f"Total number of result: {self.total_search_results}", fg="green"))
                else:
                    click.echo(click.style("Getting total search results failed."
                                           " Sorry the browser context ends here. Kindly try again", fg="red"))
            get_searched_user_profile(self, self.driver)
            click.echo(click.style("Read {} user profile urls".format(len(self.user_profile_urls))))
            self.current_page += 1

            click.echo("-----------------------------------------------")
            click.echo(click.style("Waiting for 3 seconds before making the next request.", fg="blue"))
            time.sleep(3)
        except Exception as e:
            save_execution_context(self)

    def profile_contact(self, profile_url):
        click.echo(click.style(f"Processing user profile: {profile_url}.", underline=True, bold=True))
        self.driver.get(profile_url)
        try:
            WebDriverWait(self.driver, WAIT_PERIOD).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'a[data-control-name="contact_see_more"]')
            ))

            element = self.driver.find_element_by_css_selector('a[data-control-name="contact_see_more"]')
            element.click()

            WebDriverWait(self.driver, WAIT_PERIOD).until(EC.presence_of_element_located((By.ID,
                                                                                          'artdeco-modal-outlet')))
            contact_modal = self.driver.find_element_by_id("artdeco-modal-outlet")

            WebDriverWait(contact_modal, WAIT_PERIOD).until(EC.presence_of_element_located((By.CLASS_NAME, 'ci-email')))

            username_div = contact_modal.find_element_by_css_selector('div.artdeco-modal__header')
            h1_header_elem = username_div.find_element_by_tag_name("h1")
            email_section = contact_modal.find_element_by_css_selector('section.ci-email')
            email_elem = email_section.find_element_by_tag_name("a")

            if email_elem:
                username = h1_header_elem.text

                first_name = ""
                last_name = ""

                if username:
                    username = username.split(" ")
                    if len(username) == 1:
                        first_name = username[0]
                    elif len(username) == 2:
                        first_name = username[0]
                        last_name = username[1]
                    else:
                        first_name, *last_name = username
                        last_name = " ".join(last_name)

                self.user_emails.append({"email": email_elem.text,
                                         "first_name": first_name,
                                         "last_name": last_name})

        except Exception as e:
            save_execution_context(self)
            print(e)

        time.sleep(3)

    def write_user_email_address_to_file(self):
        if self.user_emails:
            with open("user_emails.csv", "w") as fd:
                fieldnames = ['first_name', 'last_name', "email"]
                writer = csv.DictWriter(fd, fieldnames=fieldnames)

                writer.writeheader()
                for data in self.user_emails:
                    writer.writerow(data)

        else:
            click.echo(click.style("NO Email detected.", fg="red", bold=True))

