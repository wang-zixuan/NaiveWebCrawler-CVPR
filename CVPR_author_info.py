import requests
import collections
import urllib3
import pandas as pd
from lxml import etree
urllib3.disable_warnings()


def main_crawler(year, info):
    url = 'https://dblp.org/db/conf/cvpr/cvpr' + str(year) + '.html'
    root_content = requests.get(url, verify=False).content
    root_tree = etree.HTML(root_content)

    pub_lists = root_tree.xpath(".//ul[@class='publ-list']")

    for pub_list in pub_lists:
        pub_info = pub_list.xpath(".//li[@class='entry inproceedings']")

        # skip entry editor
        if len(pub_info) == 0:
            continue

        for pub in pub_info:
            # only get the info of first author
            authors = pub.xpath(".//cite/span[@itemprop='author']")
            if not authors:
                continue

            first_author = authors[0]
            name = first_author.xpath(".//span[@itemprop='name']/text()")
            name = ''.join(name)

            # dblp main page of the author
            site = first_author.xpath(".//a[@itemprop='url']/@href")
            site = ''.join(site)

            # institute
            affiliation = affiliation_crawler(site)
            print(name, site, affiliation)

            info[name][0] += 1

            # keep the newest institute
            if info[name][1] == "?" and affiliation:
                info[name][1] = affiliation


def affiliation_crawler(site):
    page = requests.get(site, verify=False).content
    page_tree = etree.HTML(page)
    aff_tag = page_tree.xpath(".//li[@itemprop='affiliation']")
    affiliation = None

    if len(aff_tag) == 1:
        affiliation = aff_tag[0].xpath(".//span[@itemprop='name']/text()")
        affiliation = ''.join(affiliation)

    elif len(aff_tag) > 1:
        affiliation = ''
        for aff in aff_tag:
            aff_elem = aff.xpath(".//span[@itemprop='name']/text()")
            aff_elem = ''.join(aff_elem)
            affiliation += ' & ' + aff_elem if affiliation != "" else aff_elem

    return affiliation


if __name__ == '__main__':
    infos = collections.defaultdict(lambda: [0, "?"])

    # in the range of i years
    years = [2020 - i for i in range(5)]
    for year in years:
        main_crawler(year, infos)
        print(year, 'done..')

    print(len(infos), 'authors found.')

    # sort by the number of articles reversely
    infos_sorted = sorted(infos.items(), key=lambda x: x[1][0], reverse=True)
    infos_sorted = [[k] + list(v) for k, v in infos_sorted]

    # only keep first 1000 authors and save it to the xlsx file
    df = pd.DataFrame(infos_sorted[:min(1000, len(infos_sorted))])

    writer = pd.ExcelWriter('info.xlsx', engine='xlsxwriter')
    df.to_excel(writer, sheet_name='info', index=False, header=['Name', 'Cnt', 'Institute'])
    writer.save()
