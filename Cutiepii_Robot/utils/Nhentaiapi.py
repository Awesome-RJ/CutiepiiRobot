from bs4 import BeautifulSoup
import requests

class nhentaiapi():  
    def __init__(self, code):
        self.code = code

    def get_chapter_by_code(code): 
        url = f"https://nhentai.net/g/{code}/1"
        response = requests.get(url)
        response_html = response.text
        soup = BeautifulSoup(response_html, 'lxml')
        page_count = soup.find("span", class_="num-pages").text
        img_link = soup.find("section", id= "image-container").img
        img_link_skeleton = img_link["src"].split("/")
        list_of_pages = []
        for i in range(int(page_count)):
            temp = img_link_skeleton[-1] 
            temp = temp.split(".")
            temp[0] = str(i+1)
            pagenum = ".".join(temp)
            img_link_skeleton[-1] = pagenum
            list_of_pages.append("/".join(img_link_skeleton))
        return list_of_pages
