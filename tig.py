#!/usr/bin/env python3
# _*_ coding:utf-8 _*_
# author TeamsSix
# blog https://www.teamssix.com
# github https://github.com/teamssix

import os
import sys
import base64
import requests
import argparse
import subprocess
import pandas as pd
from pandas import DataFrame
from configparser import ConfigParser

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'}


def init(config_path):
    config_text = '''[Threat Intelligence]

# 微步威胁情报查询，查看 api 地址：https://x.threatbook.cn/nodev4/vb4/myAPI（每天 50 次的免费额度）
ThreatBook_enable = true
ThreatBook_api = ''

[IP Passive Information]

# IP 反查，调用 http://api.webscan.cc/ 的 api
IP_reverse_enable = true

# ICP 备案信息查询，调用 https://api.vvhan.com/api/icp 的 api，如果目标 IP 没有反查到域名，该项即使开启也不会有输出
ICP_beian_enable = true

# Fofa ip 信息查询，查看 api 地址：https://fofa.so/user/users/detail（付费，普通会员每次100条，高级会员每次10000条）
Fofa_enable = true
Fofa_email = ''
Fofa_api = ''

[IP Active Information]

# 利用 ping 命令对 IP 进行存活检测
IP_survive_enable = true'''
    with open(config_path, 'w', encoding='utf-8-sig') as w:
        w.write(config_text)


def print_list(list):
    print_text = ''
    for i in list:
        if i != list[-1]:
            print_text = print_text + i + ','
        else:
            print_text = print_text + i
    return print_text


def youdao_trans(text):
    url = 'http://fanyi.youdao.com/translate?&doctype=json&type=EN2ZH_CN&i=%s' % text
    r = requests.get(url, headers=headers)
    text_trans = r.json()['translateResult'][0][0]['tgt']
    return text_trans.strip('。').strip('，')


def req(url, headers):
    try:
        r = requests.get(url, headers=headers)
    except requests.exceptions.ConnectTimeout:
        print('[-] 连接 %s 发生超时' % url)
    except requests.exceptions.ProxyError:
        print('[-] 连接代理失败' % url)
    return r


def ThreatBook(ip, config_path):  # 微步威胁情报查询
    cfg = ConfigParser()
    cfg.read(config_path, encoding='utf-8-sig')
    ThreatBook_api = cfg.get('Threat Intelligence', 'ThreatBook_api').strip("'")

    if ThreatBook_api == "":
        print('\n[-] 未检测到微步 API')
    else:
        url = 'https://api.threatbook.cn/v3/scene/ip_reputation'
        query = {
            "apikey": "%s" % ThreatBook_api,
            "resource": "%s" % ip
        }
        r = requests.request("GET", url, params=query)

        def tag_trans(tag):
            tag_list = ['Spam', 'Zombie', 'Scanner', 'Exploit', 'Botnet', 'Suspicious', 'Brute Force', 'Proxy',
                        'Whitelist',
                        'Info', 'C2', 'Hijacked', 'Phishing', 'Malware', 'Compromised', 'MiningPool', 'CoinMiner',
                        'Sinkhole C2', 'SSH Brute Force', 'FTP Brute Force', 'SMTP Brute Force', 'Http Brute Force',
                        'Web Login Brute Force', 'HTTP Proxy', 'HTTP Proxy In', 'HTTP Proxy Out', 'Socks Proxy',
                        'Socks Proxy In', 'Socks Proxy Out', 'VPN', 'VPN In', 'VPN Out', 'Tor', 'Tor Proxy In',
                        'Tor Proxy Out', 'Bogon', 'FullBogon', 'Gateway', 'IDC', 'Dynamic IP', 'Edu', 'DDNS', 'Mobile',
                        'Search Engine Crawler', 'CDN', 'Advertisement', 'DNS', 'BTtracker', 'Backbone']
            tag_trans = ['垃圾邮件', '傀儡机', '扫描', '漏洞利用', '僵尸网络', '可疑', '暴力破解', '代理', '白名单', '基础信息', '远控', '劫持', '钓鱼',
                         '恶意软件',
                         '失陷主机', '矿池', '私有矿池', '安全机构接管 C2', 'SSH暴力破解', 'FTP暴力破解', 'SMTP暴力破解', 'HTTP AUTH暴力破解', '撞库',
                         'HTTP Proxy', 'HTTP代理入口', 'HTTP代理出口', 'Socks代理', 'Socks代理入口', 'Socks代理出口', 'VPN代理', 'VPN入口',
                         'VPN出口', 'Tor代理', 'Tor入口', 'Tor出口', '保留地址', '未启用IP', '网关', 'IDC服务器', '动态IP', '教育', '动态域名',
                         '移动基站',
                         '搜索引擎爬虫', 'CDN服务器', '广告', 'DNS服务器', 'BT服务器', '骨干网']
            try:
                tag_index = tag_list.index(tag)
                return tag_trans[tag_index]
            except:
                return tag

        def scene_trans(scene):
            scene_list = ['CDN', 'University', 'Mobile Network', 'Unused', 'Unrouted', 'WLAN', 'Anycast',
                          'Infrastructure',
                          'Internet Exchange', 'Company', 'Hosting', 'Satellite Communication', 'Residence',
                          'Special Export', 'Institution', 'Cloud Provider']
            scene_trans = ['CDN', '学校单位', '移动网络', '已路由-未使用', '已分配-未路由', 'WLAN', 'Anycast', '基础设施', '交换中心', '企业专线',
                           '数据中心',
                           '卫星通信', '住宅用户', '专用出口', '组织机构', '云厂商']
            try:
                scene_index = scene_list.index(scene)
                return scene_trans[scene_index]
            except:
                return scene

        r_json = r.json()
        if r_json['response_code'] != 0:
            if r_json['verbose_msg'] == 'Beyond Daily Limitation':
                print('\n[-] 微步 API 已超出当日使用次数')
            else:
                print('\n[-] 微步 API 调用失败，错误信息：%s' % r_json['verbose_msg'])
        else:
            # 情报可信度
            confidence_level = r_json['data']['%s' % ip]['confidence_level']
            if confidence_level == 'low':
                print('\n[+] 情报可信度：低')
            elif confidence_level == 'medium':
                print('\n[+] 情报可信度：中等')
            elif confidence_level == 'high':
                print('\n[+] 情报可信度：高')

            # 是否为恶意 IP
            if r_json['data']['%s' % ip]['is_malicious'] == False:
                print('[+] 是否为恶意IP：否')
            else:
                print('[+] 是否为恶意IP：是')

            # 危害程度
            severity = r_json['data']['%s' % ip]['severity']
            if severity == 'info':
                print('[+] IP危害等级：无')
            elif severity == 'low':
                print('[+] IP危害等级：低')
            elif severity == 'medium':
                print('[+] IP危害等级：中')
            elif severity == 'high':
                print('[+] IP危害等级：高')
            elif severity == 'critical':
                print('[+] IP危害等级：严重')

            # 微步标签
            print('[+] 微步标签：', end='')
            tag_original = r_json['data']['%s' % ip]['judgments']
            for i in tag_original:
                if i != tag_original[-1]:
                    print(tag_trans(i), end=',')
                else:
                    print(tag_trans(i))

            # 标签类别
            tags_classes = r_json['data']['%s' % ip]['tags_classes']
            if len(tags_classes) > 0:
                print('[+] 标签类别：', end='')
                print(print_list(tags_classes[0]['tags']))
                print('[+] 安全事件标签：%s' % tags_classes[0]['tags_type'])

            # 场景
            scene = r_json['data']['%s' % ip]['scene']
            if scene != '':
                print('[+] 应用场景：%s' % scene_trans(scene))

            # IP 基本信息
            print('[+] 运营商：%s' % youdao_trans(r_json['data']['%s' % ip]['basic']['carrier']))
            location = r_json['data']['%s' % ip]['basic']['location']
            if location['province'] in ['Shanghai', 'Beijing', 'Tianjin', 'Chongqing']:
                ip_location = location['country'] + ' ' + location['city']
            else:
                ip_location = location['country'] + ' ' + location['province'] + ' ' + location['city']
            print('[+] 地理位置：%s' % youdao_trans(ip_location))

            print('[+] 情报更新时间：%s' % r_json['data']['%s' % ip]['update_time'])


def IP_survive(ip):
    os_name = os.name
    if os_name == 'nt':
        res = subprocess.call("ping -n 2 %s" % ip, shell=True, stdout=subprocess.PIPE)
    else:
        res = subprocess.call("ping -c 2 %s" % ip, shell=True, stdout=subprocess.PIPE)
    if res == 0:
        print('\n[+] %s 可以 ping 通' % ip)
    else:
        print('\n[-] %s 无法 ping 通，主机可能不存活' % ip)


def ip_reverse(ip, config_path):
    print()
    url = 'http://api.webscan.cc/?action=query&ip=%s' % ip
    r = req(url, headers)
    if r.text != 'null':
        pd.set_option('display.max_columns', 1000)
        pd.set_option('display.width', 1000)
        pd.set_option('display.max_colwidth', 1000)
        pd.set_option('display.unicode.ambiguous_as_wide', True)
        pd.set_option('display.unicode.east_asian_width', True)
        print('[+] IP 反查域名信息：\n')
        cfg = ConfigParser()
        cfg.read(config_path, encoding='utf-8-sig')
        ICP_beian_enable = cfg.get('IP Passive Information', 'ICP_beian_enable')
        if ICP_beian_enable == 'true':
            pools = []
            for i in r.json():
                result = {}
                url = 'https://api.vvhan.com/api/icp?url=%s' % i['domain']
                r_icp = req(url, headers)
                r_icp_json = r_icp.json()
                if 'message' not in r_icp_json:  # 存在备案信息
                    if i['title'] == '' or i['title'] == 'Null':
                        result['域名'] = i['domain'].strip()
                        result['标题'] = 'N/A'
                        result['备案类型'] = r_icp_json['info']['nature'].strip()
                        result['备案名称'] = r_icp_json['info']['name'].strip()
                        result['备案号'] = r_icp_json['info']['icp'].strip()
                    else:
                        result['域名'] = i['domain'].strip()
                        result['标题'] = i['title'].strip()
                        result['备案类型'] = r_icp_json['info']['nature'].strip()
                        result['备案名称'] = r_icp_json['info']['name'].strip()
                        result['备案号'] = r_icp_json['info']['icp'].strip()
                else:  # 不存在备案信息
                    if i['title'] == '' or i['title'] == 'Null':
                        result['域名'] = i['domain'].strip()
                        result['标题'] = 'N/A'
                        result['备案类型'] = 'N/A'
                        result['备案名称'] = 'N/A'
                        result['备案号'] = 'N/A'
                    else:
                        result['域名'] = i['domain'].strip()
                        result['标题'] = i['title'].strip()
                        result['备案类型'] = 'N/A'
                        result['备案名称'] = 'N/A'
                        result['备案号'] = 'N/A'
                pools.append(result)
            df = DataFrame(pools, columns=['域名', '标题', '备案类型', '备案名称', '备案号'])
            print(df)
        else:
            pools = []
            for i in r.json():
                result = {}
                if i['title'] == '' or i['title'] == 'Null':
                    result['域名'] = i['domain'].strip()
                    result['标题'] = 'N/A'
                else:
                    result['域名'] = i['domain'].strip()
                    result['标题'] = i['title'].strip()
                pools.append(result)
            df = DataFrame(pools, columns=['域名', '标题'])
            print(df)
    else:
        print('[-] 未发现该 IP 的反查域名')


def Fofa(ip, config_path):  # Fofa ip 信息查询
    cfg = ConfigParser()
    cfg.read(config_path, encoding='utf-8-sig')
    Fofa_email = cfg.get('IP Passive Information', 'Fofa_email').strip("'")
    Fofa_api = cfg.get('IP Passive Information', 'Fofa_api').strip("'")
    if Fofa_api == "":
        print('\n[-] 未检测到Fofa API')
    else:
        size = 100
        search_string_byte = base64.b64encode(ip.encode('utf-8')).decode()
        url = 'https://fofa.so/api/v1/search/all?email=%s&key=%s&qbase64=%s&size=%s' % (
            Fofa_email, Fofa_api, search_string_byte, size)
        r = req(url, headers)
        r_json = r.json()
        if r_json['error'] == True:
            if r_json['errmsg'] == '401 Unauthorized, make sure 1.email and apikey is correct 2.FOFA coin is enough.':
                print('\n[-] Fofa API 调用失败，错误原因有：\n    1、Fofa 邮箱或 API 填写错误\n    2、F币余额不足')
            else:
                print('\n[-] Fofa 获取数据发生错误，错误信息：%s' % r_json['errmsg'])
        elif len(r_json['results']) > 0:
            ip_port = []
            for i in r_json['results']:
                ip_port.append(i[2])
            ip_port = list(set(ip_port))
            ip_port.sort(key=int)
            print('\n[+] IP 可能开放端口：%s' % print_list(ip_port))
            url_port = []
            for i in r_json['results']:
                url_port.append(i[0])
                url_port = list(set(url_port))
                url_port.sort()
            if len(url_port) > 1:
                print('[+] URL 信息：')
                for i in url_port:
                    print('[+] %s' % i)
            else:
                print('[+] URL 信息：%s' % i)


def main(ip, config_path):
    print('\n\n[!] 正在查询 %s 的情报信息' % ip)
    cfg = ConfigParser()
    cfg.read(config_path, encoding='utf-8-sig')
    ThreatBook_enable = cfg.get('Threat Intelligence', 'ThreatBook_enable')
    IP_reverse_enable = cfg.get('IP Passive Information', 'IP_reverse_enable')
    Fofa_enable = cfg.get('IP Passive Information', 'Fofa_enable')
    IP_survive_enable = cfg.get('IP Active Information', 'IP_survive_enable')

    if ThreatBook_enable == 'true':
        ThreatBook(ip, config_path)
    if IP_survive_enable == 'true':
        IP_survive(ip)
    if IP_reverse_enable == 'true':
        ip_reverse(ip, config_path)
    if Fofa_enable == 'true':
        Fofa(ip, config_path)


if __name__ == '__main__':
    print('''
 +-+-+-+-+-+-+ +-+-+-+-+-+-+-+-+-+-+-+-+ +-+-+-+-+-+-+-+-+-+
 |T|h|r|e|a|t| |I|n|t|e|l|l|i|g|e|n|c|e| |G|a|t|h|e|r|i|n|g|
 +-+-+-+-+-+-+ +-+-+-+-+-+-+-+-+-+-+-+-+ +-+-+-+-+-+-+-+-+-+
    Author: TeamsSix    Version: 0.2    Date: 2021-03-11   ''')
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', dest='ip', help='目标 IP')
    parser.add_argument('-f', dest='file', help='IP 文本，一行一个')
    parser.add_argument('-c', dest='config', help='指定配置文件，默认 ./config.ini')
    args = parser.parse_args()

    if args.config:
        config_path = args.config
    else:
        root_path = sys.path[0]
        config_path = '%s/config.ini' % root_path
        if not os.path.exists(config_path):
            init(config_path)
            print('[!] 未检测到配置文件，已自动生成配置文件，请修改配置文件后重新运行')
            sys.exit()
    if not os.path.exists(config_path):
        print('[-] 未找到配置文件，请确认配置文件路径是否正确')
        sys.exit()

    if args.ip:
        main(args.ip, config_path)
    elif args.file:
        with open(args.file) as f:
            f = f.readlines()
            for i in f:
                i = i.strip()
                main(i, config_path)
    else:
        print('[!] 请输入待扫描的 IP 或 IP 列表文件')
        sys.exit()