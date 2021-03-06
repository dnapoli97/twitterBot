import os  
from selenium import webdriver  
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys  
from selenium.webdriver.chrome.options import Options  



class driver:


    def __init__(self, path):
        chrome_options = Options()  
        chrome_options.add_argument("headless") 
        chrome_options.binary_location = "/app/.apt/usr/bin/google-chrome"
        self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)   
 

    def get_page(self, url):
        self.driver.implicitly_wait(15)
        self.driver.get(url)
        


    def get_source(self):
        return self.driver.page_source
        
        
    def close_driver(self):
        self.driver.close()
