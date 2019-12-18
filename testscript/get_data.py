# coding: utf-8
import re
import requests
from bs4 import BeautifulSoup


def get_log_path(root_url):
    log_path = requests.get(root_url)
    res = log_path.content
    soup = BeautifulSoup(res, 'lxml')
    items = soup.findAll("a")
    for item in items:
        if "paas_log" in item.text:
            paas_log_url = root_url + "paas_log/"
            get_paas_log_data(paas_log_url)
        if "paas_deploy" in item.text:
            paas_deploy_url = root_url + "paas_deploy/"
            get_paas_deploy_data(paas_deploy_url)

def get_paas_log_data(paas_log_url):
    log_path = requests.get(paas_log_url)
    res = log_path.content
    soup = BeautifulSoup(res, 'lxml')
    items = soup.findAll("a")
    for item in items:
        if re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", item.text.split("/")[0]):
            data_url = paas_log_url + item.text
            time_data_info = requests.get(data_url)
            time_data_res = time_data_info.content
            data_soup = BeautifulSoup(time_data_res, 'lxml')
            data_items = data_soup.findAll('a')


            # 配置需要解析的文件名称
            simple_data_dict = dict()
            for data_item in data_items:
                if "simple" in data_item.text:
                    simple_data_req = requests.get(data_url+data_item.text)
                    simple_data_res = simple_data_req.content
                    simple_data_items = simple_data_res.split("\n")
                    for simple_data_item in simple_data_items:
                        if simple_data_item:
                            key, value = simple_data_item.split("|")
                            simple_data_dict[key.strip()] = value


def get_paas_deploy_data(paas_deploy_url):
    pass

if __name__ == "__main__":
    root_url = "http://192.168.0.101:8000/"
    get_log_path(root_url)
