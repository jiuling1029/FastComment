# -*- coding: utf-8 -*-
"""
Created on Sun Nov 27 16:56:25 2016

@author: zero
"""

from urllib.parse import urlparse
import time
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException,WebDriverException

class Coral:
    """
    属性：url 快速评论的链接
        coral_id 快速评论的ID
        page 当前的页数
        programme_name 节目名称
        coral_name 快速评论节目名字
        lastComments 提取出来的评论列表
    DOM元素
        more_btn 加载更多评论按钮
        login_btn 登录按钮
        send_btn 发送评论按钮
        comment_area 评论输入框
    """
    def __init__(self, driver, url):
        self.driver = driver
        self.url = url
        self.coral_id = urlparse(self.url).path[1:]
        self.page = 0 
        # self.programme_name = programme_name 考虑到要讲类定义的更加明确，所以取消该属性
        # 定义存储评论的结构
        self.comments = []
        # 设置frame为默认，避免之前一个已经失效的frame
        self.driver.switch_to.default_content()
        # 记录当前的frame
        self.current_frame = 'root'
        
    # 打开浏览器，获取常用的页面元素
    def open_brower(self):
        self.driver.implicitly_wait(5)
        self.driver.get(self.url)
        # 获取快速评论节目名称
        self.coral_name = self.driver.title.encode('utf-8')

    def login(self, **user):
        # 切换到评论的frame
        self.switch_frame_comment()
        # 登录按钮
        btn = self.driver.find_element_by_id('top_post_btn')
        # 判断是否登录
        if btn.text == '发表评论':
            return True
        btn.click()
        # 切换到登录的frame
        self.switch_frame_login()
        # 传入用户名和密码的就是用账号密码登录。 1 快速登录，2 账号密码登录
        if 'username' in user:
            # 设置等待登录窗口加载完成
            locator = (By.ID, 'switcher_plogin')
            WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable(locator))
            #获取“账号密码登录”按钮，并点击
            self.driver.find_element_by_id('switcher_plogin').click()
            # 获取账号输入框，清空默认值，并输入账号
            u_btn = self.driver.find_element_by_id('u')
            u_btn.clear()
            u_btn.send_keys(user['username'])

            p_edit = self.driver.find_element_by_id('p')
            # 判断是否输入传入密码，没有传入密码等待用户手动输入
            if 'password' in user:
                # 获取密码输入框，并输入密码
                p_edit.send_keys(user['password'])
                # 获取登录按钮，并且点击
                time.sleep(1)
                submit_btn = self.driver.find_element_by_class_name('submit')
                try:
                    while(True):
                        submit_btn.tag_name
                        submit_btn.click()
                        time.sleep(1)
                        '''这里的检测页面刷新不好，后期调整'''
                except WebDriverException: #StaleElementReferenceException: # 表示提交成功，可能直接登录，也可能会输入验证码
                    pass
                   # print("点击登录成功！\n")
                else:
                   # print("点击登录失败！\n")
                    return False
            else:
                # 将密码框设置焦点
                p_edit.send_keys('')
                # 检查是否登录成功
       # print('开始检查是否登录成功...', "\n")
        self.switch_frame_default()
        locator = (By.CLASS_NAME, 'logined')
        try:
            WebDriverWait(self.driver, 60).until(EC.visibility_of_element_located(locator))
        except:
           # print u"登录失败！\n"
           return False
        else:
           # print u"登录成功！\n"
            return True
        
    # 判断用户是否登录
    def check_login(self):
        self.switch_frame_default()
        locator = (By.CLASS_NAME, 'logined')
        try:
            WebDriverWait(self.driver, 15).until(EC.visibility_of_element_located(locator))
        except Exception as e:
            print(e)
            return False
        else:
            return True

    # 发送评论，需要先登录
    def send_comment(self, content):
        self.switch_frame_comment()
        self.driver.find_element_by_id('top_textarea').send_keys(content)
        self.driver.find_element_by_id('top_post_btn').click()
        time.sleep(1)
        locator = (By.CLASS_NAME, 'np-btn-submit-loading')
        try:
            WebDriverWait(self.driver, 30).until_not(EC.presence_of_element_located(locator))
        except:
            print("发表评论失败！\n")
            return False
        else:
            print("发表评论成功！\n")
            return True
                    
    # 退出登陆
    def logout(self):
        # 删除所有cookie相当于等出了
        self.driver.delete_all_cookies()
        # 切换frame到根frame，防止frame不在根frame造成不是全新打开
        self.switch_frame_default()
        # 重新打开该页面
        # self.driver.get(self.url)
        
    # 打开一个链接
    def brower_get(self, url):
        if url:
            self.driver.get(url)
        else:
            print("The parameter url is missing")
           
    # 切换到根frame
    def switch_frame_default(self):
        if self.current_frame == 'root':
            pass
        else:
            # 切换到默认frame(也就是根的frame)
            self.driver.switch_to.default_content()
            # 设置当前的frame
            self.current_frame = 'root'
           
    # 切换到评论的frame
    def switch_frame_comment(self):
        if self.current_frame == 'comment':
            pass
        else:
            # 切换到默认frame(也就是根的frame)
            self.driver.switch_to.default_content()
            # 切换到评论的iframe
            self.driver.switch_to.frame('commentIframe')
            # 设置当前的frame
            self.current_frame = 'comment'
        
    # 切换到登录的frame
    def switch_frame_login(self):
        if self.current_frame == 'login':
            pass
        else:
            # 切换到默认frame(也就是根的frame)
            self.driver.switch_to.default_content()
            # 切换到登录的frame
            self.driver.switch_to.frame('login_one_frame')
            # 设置当前的frame
            self.current_frame = 'login'