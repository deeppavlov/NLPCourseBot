from bs4 import BeautifulSoup
import urllib
from pprint import pprint
import json


class GoogleFormParser:
    """
    Takes url of the Google form with Quiz
    or takes html file path on the file system
    and return quiz tasks as an array of dicts.
        e.g: each task is a dict which contains such fields:
            1. 'text' -- is a question text;
            2. 'variants' -- is an array of ans-variants; only one right;
            3. 'several_poss_vars' -- is an array of ans-variants; several may be right;
            4. 'grids' -- same as variants, but only numbers (from 1 to len(grids), only one ans right)
            5. 'img' -- image path on file sys or url
    """

    def __init__(self, url: object = None, file_path: object = None) -> object:

        assert (url is not None) ^ (file_path is not None), "Only one of 2 arguments must be specified!"

        if url is not None:
            try:
                self.url = url
                self.html = urllib.request.urlopen(url).read()
            except:
                print("Smth went wrong with opening url!")
                exit(1)
        if file_path is not None:
            with open(file_path, 'r') as fn:
                self.html = fn.read()
        self.soup = BeautifulSoup(self.html, "html5lib")

    def get_tasks_json(self):

        def get_text_from_lists(tag_lists):
            return [f.getText() if len(f) > 0 else '' for f in tag_lists]

        tasks = []
        blist = self.soup.find_all("div", class_="freebirdFormviewerViewItemsItemItem")

        for bl in blist:
            task = dict()
            task['text'] = bl.find_all("div", class_="freebirdCustomFont")[0].getText()

            grids = get_text_from_lists(bl.find_all("label", class_="freebirdMaterialScalecontentColumn"))
            variants = get_text_from_lists(bl.find_all("label", class_="freebirdFormviewerViewItemsRadioChoice"))
            several_poss_vars = get_text_from_lists(
                bl.find_all("label", class_="freebirdFormviewerViewItemsCheckboxContainer"))
            imgs = bl.find_all("img", class_="freebirdFormviewerViewItemsEmbeddedobjectImage")
            if len(imgs) > 0:
                imgs = imgs[0]['src']  # img address on the file system or in the internet;
            else:
                imgs = ''

            task['grids'] = grids
            task['variants'] = variants
            task['several_poss_vars'] = several_poss_vars
            task['img'] = imgs
            tasks.append(task)

        return tasks

    def save_json(self, path_file):
        with open(path_file, 'w') as fn:
            json.dump(self.get_tasks_json(), fn)
        print("json saved to: {}".format(path_file))


if __name__ == "__main__":
    # test url:
    # gf = GoogleFormParser(
    #     url="https://docs.google.com/forms/d/e/1FAIpQLScrVP6urS02qm7bOAkbpwqSXBFJOSgvUi8J9X727j_zc8tacw/viewform#start=openform")
    # # pprint(gf.get_tasks_json())
    # gf.save_json("./quiz6.json")

    gf = GoogleFormParser(file_path='NLP.Quiz2.html')
    gf.save_json("./quiz2.json")

    # test loading
    with open("./quiz6.json") as f:
        lol = json.load(f)
    pprint(lol)

    # test file:
    # gf2 = GoogleFormParser(file_path="NLP._Quiz6.html")
    # pprint(gf2.get_tasks_json())

    # test empty arguments:
    # gf3 = GoogleFormParser()

    # test full arguments:
    # gf4 = GoogleFormParser(url="sdfgs", file_path="sdfgsd")
