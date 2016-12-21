# -*- coding: utf-8 -*-
"""
Created on Sat Dec 03 21:16:20 2016

@author: zero
"""
from coral import Coral
from selenium import webdriver

# 创建一个浏览器实例
profileDir = r"C:\Users\zero\AppData\Roaming\Mozilla\Firefox\Profiles\qx6b4mkb.selenium"
driver = webdriver.Firefox(profileDir)


# 读取任务

url = 'http://coral.qq.com/1663679768'
content = '我的沙发啦'

coral = Coral(driver, url)
coral.open_brower()
if not coral.check_login():
    if not coral.login():
        print('登录失败！不能发布评论');
coral.send_comment(content)



    
driver.quit()


import pickle
class story:
    def __init__(self):
        self.hello = 12
        self.wo = '45679'
        
s = story()
with open('data.pkl', 'wb') as file:
    pickle.dump(s, file)
    

with open('data.pkl', 'rb') as file:
    s = pickle.load(file)
print(s)