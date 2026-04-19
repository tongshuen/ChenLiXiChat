import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
import requests
import threading
import json
import os
import time
from datetime import datetime, timedelta
import random
import math
from io import BytesIO
from PIL import Image, ImageTk
import base64
import sys
import traceback

class ChenLiXiChat:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("陈丽希聊天器")
        self.root.geometry("900x700")
        
        self.user_name = ""
        self.user_avatar_path = ""
        self.api_key = ""
        self.settings_file = "chat_settings.json"
        self.resources_file = "chat_resources.json"
        self.chat_history_file = "chat_history.json"
        
        self.chat_history = []
        self.message_queue = []
        self.is_typing = False
        
        self.message_timestamps = []
        
        self.styles = {
            "font_size": 12,
            "clx_bubble_color": "#E3F2FD",
            "user_bubble_color": "#C8E6C9",
            "clx_name_color": "#1976D2",
            "user_name_color": "#388E3C",
            "send_button_color": "#2196F3",
            "bg_color": "#F5F5F5",
            "time_color": "#757575"
        }
        
        self.resource_url = "http://www.tongshunham.top/clxZiYuan/index.json"
        self.local_resources = {}
        self.is_downloading = False
        self.download_progress = 0
        self.online = True
        
        self.load_settings()
        self.load_chat_history()
        
        if not self.user_name or not self.api_key:
            self.show_setup_window()
        else:
            self.initialize_chat_interface()
            threading.Thread(target=self.check_and_download_resources_async, daemon=True).start()
    
    def load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.user_name = settings.get('user_name', '')
                    self.user_avatar_path = settings.get('user_avatar_path', '')
                    self.api_key = settings.get('api_key', '')
                    
                    if 'styles' in settings:
                        self.styles.update(settings['styles'])
        except Exception as e:
            print(f"加载设置失败: {e}")
    
    def save_settings(self):
        try:
            settings = {
                'user_name': self.user_name,
                'user_avatar_path': self.user_avatar_path,
                'api_key': self.api_key,
                'styles': self.styles
            }
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存设置失败: {e}")
    
    def load_chat_history(self):
        try:
            if os.path.exists(self.chat_history_file):
                with open(self.chat_history_file, 'r', encoding='utf-8') as f:
                    self.chat_history = json.load(f)
        except Exception as e:
            print(f"加载聊天记录失败: {e}")
            self.chat_history = []
    
    def save_chat_history(self):
        try:
            with open(self.chat_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.chat_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存聊天记录失败: {e}")
    
    def clear_chat_history(self):
        self.chat_history = []
        self.save_chat_history()
        self.update_chat_display()
    
    def show_setup_window(self):
        self.setup_window = tk.Toplevel(self.root)
        self.setup_window.title("初始设置")
        self.setup_window.geometry("500x400")
        self.setup_window.resizable(False, False)
        
        self.setup_window.transient(self.root)
        self.setup_window.grab_set()
        
        tk.Label(self.setup_window, text="欢迎使用陈丽希聊天器", 
                font=("Microsoft YaHei", 16, "bold")).pack(pady=20)
        
        tk.Label(self.setup_window, text="您的名字:", 
                font=("Microsoft YaHei", 11)).pack(anchor='w', padx=50)
        self.name_entry = tk.Entry(self.setup_window, width=40, font=("Microsoft YaHei", 11))
        self.name_entry.pack(pady=(0, 15), padx=50)
        
        avatar_frame = tk.Frame(self.setup_window)
        avatar_frame.pack(fill='x', padx=50, pady=5)
        
        tk.Label(avatar_frame, text="头像路径:", 
                font=("Microsoft YaHei", 11)).pack(side='left')
        
        self.avatar_path_var = tk.StringVar()
        tk.Entry(avatar_frame, textvariable=self.avatar_path_var, 
                width=30, font=("Microsoft YaHei", 11)).pack(side='left', padx=10)
        
        tk.Button(avatar_frame, text="选择头像", command=self.select_avatar,
                 font=("Microsoft YaHei", 10)).pack(side='left')
        
        tk.Label(self.setup_window, text="DeepSeek API Key:", 
                font=("Microsoft YaHei", 11)).pack(anchor='w', padx=50, pady=(10, 0))
        
        self.api_entry = tk.Entry(self.setup_window, width=40, font=("Microsoft YaHei", 11))
        self.api_entry.pack(pady=(0, 20), padx=50)
        
        tk.Button(self.setup_window, text="下一步", command=self.finish_setup,
                 font=("Microsoft YaHei", 12, "bold"), bg="#4CAF50", fg="white",
                 padx=20, pady=5).pack(pady=20)
    
    def select_avatar(self):
        filename = filedialog.askopenfilename(
            title="选择头像",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if filename:
            self.avatar_path_var.set(filename)
    
    def finish_setup(self):
        self.user_name = self.name_entry.get().strip()
        self.user_avatar_path = self.avatar_path_var.get().strip()
        self.api_key = self.api_entry.get().strip()
        
        if not self.user_name:
            messagebox.showerror("错误", "请输入您的名字")
            return
        
        if not self.api_key:
            messagebox.showerror("错误", "请输入DeepSeek API Key")
            return
        
        self.save_settings()
        
        self.setup_window.destroy()
        self.initialize_chat_interface()
        threading.Thread(target=self.check_and_download_resources_async, daemon=True).start()
    
    def initialize_chat_interface(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.configure(bg=self.styles['bg_color'])
        
        self.title_label = tk.Label(self.root, text="陈丽希", 
                                   font=("Microsoft YaHei", 20, "bold"),
                                   bg=self.styles['bg_color'], fg="#333")
        self.title_label.pack(pady=10)
        
        chat_frame = tk.Frame(self.root, bg=self.styles['bg_color'])
        chat_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        chat_container = tk.Frame(chat_frame, bg='white', relief='sunken', bd=1)
        chat_container.pack(fill='both', expand=True)
        
        scrollbar = tk.Scrollbar(chat_container)
        scrollbar.pack(side='right', fill='y')
        
        self.chat_text = tk.Text(chat_container, wrap='word', yscrollcommand=scrollbar.set,
                               font=("Microsoft YaHei", self.styles['font_size']),
                               state='disabled', bg='white', bd=0)
        self.chat_text.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.chat_text.yview)
        
        input_frame = tk.Frame(chat_frame, bg=self.styles['bg_color'])
        input_frame.pack(fill='x', pady=(10, 0))
        
        self.input_entry = tk.Text(input_frame, height=3, font=("Microsoft YaHei", 12),
                                 wrap='word', bd=1, relief='solid')
        self.input_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        self.send_button = tk.Button(input_frame, text="发送", command=self.send_message,
                                   font=("Microsoft YaHei", 12, "bold"),
                                   bg=self.styles['send_button_color'], fg="white",
                                   padx=20, pady=5)
        self.send_button.pack(side='right')
        
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="设置", menu=settings_menu)
        settings_menu.add_command(label="调整样式", command=self.show_style_settings)
        settings_menu.add_command(label="修改API Key", command=self.show_api_settings)
        settings_menu.add_command(label="检查更新", command=self.manual_check_update)
        chat_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="聊天", menu=chat_menu)
        chat_menu.add_command(label="清空聊天记录", command=self.clear_chat_history)
        chat_menu.add_command(label="导出聊天记录", command=self.export_chat_history)
        settings_menu.add_separator()
        settings_menu.add_command(label="退出", command=self.root.quit)
        
        self.input_entry.bind('<Return>', self.on_enter_pressed)
        self.input_entry.bind('<Shift-Return>', lambda e: 'break')
        
        self.update_chat_display()
        self.check_network_connection_async()
    
    def on_enter_pressed(self, event):
        if not event.state & 0x1:
            self.send_message()
            return 'break'
        return None
    
    def send_message(self):
        if not self.online:
            self.add_system_message("网络连接失败，无法发送消息")
            return
            
        message = self.input_entry.get("1.0", "end-1c").strip()
        if not message:
            return
        
        current_time = time.time()
        self.message_timestamps.append(current_time)
        
        five_minutes_ago = current_time - 300
        self.message_timestamps = [t for t in self.message_timestamps if t > five_minutes_ago]
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.chat_history.append({
            "sender": "user",
            "message": message,
            "time": timestamp
        })
        
        self.input_entry.delete("1.0", "end")
        self.update_chat_display()
        self.save_chat_history()
        
        if self.should_reply():
            self.show_typing_indicator(True)
            threading.Thread(target=self.get_reply, args=(message,), daemon=True).start()
    
    def calculate_reply_probability(self):
        now = datetime.now()
        current_hour = now.hour + now.minute / 60.0
        
        is_summer_time = self.is_summer_time(now)
        
        if is_summer_time:
            wake_mean = 8.0
            wake_std = 0.5
            
            nap_start_mean = 12.0
            nap_end_mean = 12.5
            nap_std = 5/60.0
            
            sleep_mean = 22.0
            sleep_std = 1.0
        else:
            wake_mean = 9.0
            wake_std = 0.5
            
            nap_start_mean = 12.0
            nap_end_mean = 12.5
            nap_std = 5/60.0
            
            sleep_mean = 21.5
            sleep_std = 1.0
        
        wake_prob = self.normal_pdf(current_hour, wake_mean, wake_std)
        
        if 12.0 <= current_hour <= 12.5:
            nap_prob = 1.0
        else:
            nap_start_prob = self.normal_pdf(current_hour, nap_start_mean, nap_std)
            nap_end_prob = self.normal_pdf(current_hour, nap_end_mean, nap_std)
            nap_prob = max(nap_start_prob, nap_end_prob)
        
        sleep_prob = self.normal_pdf(current_hour, sleep_mean, sleep_std)
        
        total_prob = wake_prob + nap_prob + sleep_prob
        if total_prob > 0:
            wake_weight = wake_prob / total_prob
            nap_weight = nap_prob / total_prob
            sleep_weight = sleep_prob / total_prob
        else:
            wake_weight = nap_weight = sleep_weight = 0
        
        recent_count = len(self.message_timestamps)
        
        if wake_weight > nap_weight and wake_weight > sleep_weight:
            if recent_count <= 5:
                base_prob = 0.8
                std_prob = 0.2
            else:
                base_prob = 0.95
                std_prob = 0.05
        
        elif nap_weight > wake_weight and nap_weight > sleep_weight:
            if recent_count <= 5:
                base_prob = 0.7
                std_prob = 0.05
            else:
                base_prob = 0.8
                std_prob = 0.05
        
        elif sleep_weight > wake_weight and sleep_weight > nap_weight:
            if recent_count <= 5:
                base_prob = 0.05
                std_prob = 0.05
            else:
                base_prob = 0.2
                std_prob = 0.1
        
        else:
            return 1.0
        
        final_prob = random.normalvariate(base_prob, std_prob)
        return max(0.0, min(1.0, final_prob))
    
    def normal_pdf(self, x, mean, std):
        if std == 0:
            return 0
        return (1.0 / (std * math.sqrt(2 * math.pi))) * math.exp(-0.5 * ((x - mean) / std) ** 2)
    
    def is_summer_time(self, date):
        month = date.month
        if 4 <= month <= 9:
            return True
        return False
    
    def should_reply(self):
        reply_prob = self.calculate_reply_probability()
        return random.random() < reply_prob
    
    def get_reply(self, user_message):
        try:
            system_prompt = ""
            if os.path.exists(self.resources_file):
                try:
                    with open(self.resources_file, 'r', encoding='utf-8') as f:
                        resources = json.load(f)
                        if 'prompt' in resources:
                            prompt_path = resources.get('prompt_local', 'prompt.txt')
                            if os.path.exists(prompt_path):
                                with open(prompt_path, 'r', encoding='utf-8') as pf:
                                    system_prompt = pf.read()
                except Exception as e:
                    print(f"加载提示词失败: {e}")
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            for msg in self.chat_history:
                if msg['sender'] == 'user':
                    messages.append({"role": "user", "content": msg['message']})
                elif msg['sender'] == 'clx':
                    messages.append({"role": "assistant", "content": msg['message']})
            
            data = {
                "model": "deepseek-chat",
                "messages": messages,
                "stream": False
            }
            
            response = requests.post(
                "https://api.deepseek.com/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                reply = result['choices'][0]['message']['content']
                
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.chat_history.append({
                    "sender": "clx",
                    "message": reply,
                    "time": timestamp
                })
                
                self.root.after(0, self.show_typing_indicator, False)
                self.root.after(0, self.update_chat_display)
                self.save_chat_history()
            else:
                error_msg = f"API请求失败: {response.status_code}"
                if response.text:
                    try:
                        error_data = response.json()
                        error_msg += f" - {error_data.get('error', {}).get('message', 'Unknown error')}"
                    except:
                        error_msg += f" - {response.text[:100]}"
                raise Exception(error_msg)
                
        except Exception as e:
            print(f"获取回复失败: {e}")
            self.root.after(0, self.show_typing_indicator, False)
            self.root.after(0, self.add_system_message, f"获取回复失败: {str(e)}")
            self.save_chat_history()
    
    def export_chat_history(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.chat_history, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("导出成功", f"聊天记录已导出到: {filename}")
            except Exception as e:
                messagebox.showerror("导出失败", f"导出聊天记录失败: {e}")
    
    def show_typing_indicator(self, is_typing):
        self.is_typing = is_typing
        if is_typing:
            self.title_label.config(text="对方正在输入...")
        else:
            self.title_label.config(text="陈丽希")
    
    def add_system_message(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.chat_history.append({
            "sender": "system",
            "message": message,
            "time": timestamp
        })
        self.update_chat_display()
        self.save_chat_history()
    
    def update_chat_display(self):
        self.chat_text.config(state='normal')
        self.chat_text.delete('1.0', 'end')
        
        for msg in self.chat_history:
            if msg['sender'] == 'user':
                self.add_message_to_display(
                    msg['message'], 
                    msg['time'], 
                    self.user_name,
                    'right',
                    self.styles['user_bubble_color'],
                    self.styles['user_name_color']
                )
            elif msg['sender'] == 'clx':
                self.add_message_to_display(
                    msg['message'],
                    msg['time'],
                    "陈丽希",
                    'left',
                    self.styles['clx_bubble_color'],
                    self.styles['clx_name_color']
                )
            else:
                self.add_system_message_to_display(msg['message'])
        
        self.chat_text.see('end')
        self.chat_text.config(state='disabled')
    
    def add_message_to_display(self, message, timestamp, sender, align, bubble_color, name_color):
        frame = tk.Frame(self.chat_text, bg='white')
        self.chat_text.window_create('end', window=frame)
        self.chat_text.insert('end', '\n')
        
        bubble_frame = tk.Frame(frame, bg=bubble_color, bd=1, relief='solid')
        
        if align == 'right':
            bubble_frame.pack(anchor='e', padx=10, pady=5, fill='x')
        else:
            bubble_frame.pack(anchor='w', padx=10, pady=5, fill='x')
        
        text_widget = tk.Text(bubble_frame, wrap='word', height=1, width=40,
                            bg=bubble_color, bd=0, font=("Microsoft YaHei", self.styles['font_size']))
        text_widget.pack(side='top', fill='both', expand=True, padx=10, pady=5)
        
        text_widget.insert('1.0', message)
        
        lines = int(text_widget.index('end-1c').split('.')[0])
        text_widget.config(height=min(lines, 10))
        text_widget.config(state='disabled')
        
        info_frame = tk.Frame(bubble_frame, bg=bubble_color)
        info_frame.pack(side='bottom', fill='x', padx=10, pady=(0, 5))
        
        if align == 'right':
            tk.Label(info_frame, text=timestamp, font=("Microsoft YaHei", 9), 
                    fg=self.styles['time_color'], bg=bubble_color).pack(side='left')
            tk.Label(info_frame, text=sender, font=("Microsoft YaHei", 9, 'bold'), 
                    fg=name_color, bg=bubble_color).pack(side='right')
        else:
            tk.Label(info_frame, text=sender, font=("Microsoft YaHei", 9, 'bold'), 
                    fg=name_color, bg=bubble_color).pack(side='left')
            tk.Label(info_frame, text=timestamp, font=("Microsoft YaHei", 9), 
                    fg=self.styles['time_color'], bg=bubble_color).pack(side='right')
    
    def add_system_message_to_display(self, message):
        frame = tk.Frame(self.chat_text, bg='white')
        self.chat_text.window_create('end', window=frame)
        self.chat_text.insert('end', '\n')
        
        label = tk.Label(frame, text=message, font=("Microsoft YaHei", 10, 'italic'),
                        fg='#666', bg='white')
        label.pack(pady=5)
    
    def check_and_download_resources_async(self):
        if self.is_downloading:
            return
        
        self.is_downloading = True
        try:
            response = requests.get(self.resource_url, timeout=10)
            response.raise_for_status()
            resources = response.json()
            
            need_update = False
            if os.path.exists(self.resources_file):
                with open(self.resources_file, 'r', encoding='utf-8') as f:
                    local_resources = json.load(f)
                    if resources.get('version') != local_resources.get('version'):
                        need_update = True
            else:
                need_update = True
            
            if need_update:
                self.root.after(0, self.ask_download_update, resources)
            else:
                with open(self.resources_file, 'r', encoding='utf-8') as f:
                    self.local_resources = json.load(f)
                
        except Exception as e:
            print(f"检查更新失败: {e}")
        
        self.is_downloading = False
    
    def manual_check_update(self):
        if self.is_downloading:
            messagebox.showinfo("提示", "正在检查更新，请稍候...")
            return
        
        self.is_downloading = True
        threading.Thread(target=self._manual_check_update, daemon=True).start()
    
    def _manual_check_update(self):
        try:
            response = requests.get(self.resource_url, timeout=10)
            response.raise_for_status()
            resources = response.json()
            
            need_update = False
            update_info = ""
            
            if os.path.exists(self.resources_file):
                with open(self.resources_file, 'r', encoding='utf-8') as f:
                    local_resources = json.load(f)
                    if resources.get('version') != local_resources.get('version'):
                        need_update = True
                        update_info = f"发现新版本: {resources.get('version')}\n"
                        
                        if resources.get('prompt_md5') != local_resources.get('prompt_md5'):
                            update_info += f"• 提示词有更新\n"
                        if resources.get('avatar_md5') != local_resources.get('avatar_md5'):
                            update_info += f"• 头像有更新\n"
                        if resources.get('app_version') != local_resources.get('app_version'):
                            update_info += f"• 软件有新版本: {resources.get('app_version')}\n"
                            update_info += f"  下载链接: {resources.get('app_url', '')}\n"
            else:
                need_update = True
                update_info = f"首次下载资源\n版本: {resources.get('version')}\n大小: {self.format_size(resources.get('total_size', 0))}"
            
            if need_update:
                self.root.after(0, self.ask_download_update, resources, update_info)
            else:
                self.root.after(0, lambda: messagebox.showinfo("检查更新", "当前已是最新版本"))
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("检查更新失败", f"无法连接到服务器: {e}"))
        
        self.is_downloading = False
    
    def ask_download_update(self, resources, update_info=None):
        if not update_info:
            update_info = f"版本: {resources.get('version', '未知')}\n大小: {self.format_size(resources.get('total_size', 0))}"
        
        result = messagebox.askyesno(
            "检查到更新",
            f"{update_info}\n\n是否下载更新？"
        )
        
        if result:
            threading.Thread(target=self.download_resources, args=(resources,), daemon=True).start()
    
    def download_resources(self, resources):
        try:
            total_size = resources.get('total_size', 0)
            downloaded = 0
            
            progress_win = tk.Toplevel(self.root)
            progress_win.title("下载资源")
            progress_win.geometry("300x150")
            progress_win.resizable(False, False)
            
            tk.Label(progress_win, text="正在下载资源...", 
                    font=("Microsoft YaHei", 12)).pack(pady=20)
            
            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(progress_win, variable=progress_var, maximum=100)
            progress_bar.pack(fill='x', padx=20, pady=10)
            
            speed_label = tk.Label(progress_win, text="速度: 0 B/s", 
                                  font=("Microsoft YaHei", 10))
            speed_label.pack()
            
            progress_win.update()
            
            if 'prompt_url' in resources and resources.get('prompt_url'):
                start_time = time.time()
                response = requests.get(resources['prompt_url'], stream=True)
                response.raise_for_status()
                
                with open('prompt.txt', 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            progress = (downloaded / total_size) * 100
                            speed = len(chunk) / (time.time() - start_time)
                            start_time = time.time()
                            
                            self.root.after(0, self.update_progress_window, 
                                         progress_win, progress_var, speed_label, progress, speed)
            
            if 'avatar_url' in resources and resources.get('avatar_url'):
                start_time = time.time()
                response = requests.get(resources['avatar_url'], stream=True)
                response.raise_for_status()
                
                with open('clx_avatar.png', 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            progress = (downloaded / total_size) * 100
                            speed = len(chunk) / (time.time() - start_time)
                            start_time = time.time()
                            
                            self.root.after(0, self.update_progress_window, 
                                         progress_win, progress_var, speed_label, progress, speed)
            
            resources['last_updated'] = time.time()
            with open(self.resources_file, 'w', encoding='utf-8') as f:
                json.dump(resources, f, ensure_ascii=False, indent=2)
            
            self.local_resources = resources
            
            progress_win.destroy()
            self.root.after(0, lambda: messagebox.showinfo("下载完成", "资源下载完成，重启后生效"))
            
        except Exception as e:
            print(f"下载失败: {e}")
            self.root.after(0, lambda: messagebox.showerror("下载失败", f"下载资源失败: {e}"))
    
    def update_progress_window(self, window, progress_var, speed_label, progress, speed):
        progress_var.set(progress)
        speed_label.config(text=f"速度: {self.format_speed(speed)}/s")
        window.title(f"下载资源 {progress:.1f}%")
        window.update()
    
    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def format_speed(self, speed):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if speed < 1024.0:
                return f"{speed:.1f} {unit}"
            speed /= 1024.0
        return f"{speed:.1f} TB"
    
    def check_network_connection_async(self):
        def check():
            try:
                requests.get("http://www.baidu.com", timeout=5)
                self.online = True
                return True
            except:
                try:
                    requests.get("http://www.qq.com", timeout=5)
                    self.online = True
                    return True
                except:
                    self.online = False
                    self.root.after(0, self.show_network_error)
                    return False
        
        threading.Thread(target=check, daemon=True).start()
    
    def show_network_error(self):
        if not hasattr(self, 'send_button') or not self.send_button:
            return
            
        self.add_system_message("资源下载错误，可能是服务器或网络问题")
        self.send_button.config(state='disabled')
        self.input_entry.config(state='disabled')
    
    def show_style_settings(self):
        settings_win = tk.Toplevel(self.root)
        settings_win.title("调整样式")
        settings_win.geometry("400x500")
        
        tk.Label(settings_win, text="字体大小 (px):", 
                font=("Microsoft YaHei", 11)).pack(anchor='w', padx=20, pady=(20, 5))
        
        font_size_var = tk.IntVar(value=self.styles['font_size'])
        tk.Scale(settings_win, from_=8, to=24, variable=font_size_var, 
                orient='horizontal').pack(fill='x', padx=20)
        
        colors = [
            ("陈丽希气泡颜色", "clx_bubble_color"),
            ("用户气泡颜色", "user_bubble_color"),
            ("陈丽希用户名颜色", "clx_name_color"),
            ("用户用户名颜色", "user_name_color"),
            ("发送按钮颜色", "send_button_color"),
            ("背景颜色", "bg_color"),
            ("时间颜色", "time_color")
        ]
        
        color_vars = {}
        
        for i, (label, key) in enumerate(colors):
            tk.Label(settings_win, text=label + ":", 
                    font=("Microsoft YaHei", 10)).pack(anchor='w', padx=20, pady=(10, 0))
            
            color_frame = tk.Frame(settings_win)
            color_frame.pack(fill='x', padx=20, pady=2)
            
            color_var = tk.StringVar(value=self.styles[key])
            color_vars[key] = color_var
            
            tk.Entry(color_frame, textvariable=color_var, width=10).pack(side='left')
            tk.Button(color_frame, text="选择颜色", 
                     command=lambda k=key, v=color_var: self.choose_color(k, v, settings_win)).pack(side='left', padx=5)
        
        btn_frame = tk.Frame(settings_win)
        btn_frame.pack(fill='x', padx=20, pady=20)
        
        tk.Button(btn_frame, text="应用", command=lambda: self.apply_styles(
            font_size_var.get(), color_vars, settings_win),
                 font=("Microsoft YaHei", 11), bg="#4CAF50", fg="white").pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="取消", command=settings_win.destroy,
                 font=("Microsoft YaHei", 11)).pack(side='left', padx=5)
    
    def choose_color(self, key, var, parent):
        color = colorchooser.askcolor(title=f"选择{key}颜色", parent=parent)
        if color[1]:
            var.set(color[1])
    
    def apply_styles(self, font_size, color_vars, window):
        self.styles['font_size'] = font_size
        for key, var in color_vars.items():
            self.styles[key] = var.get()
        
        self.save_settings()
        self.initialize_chat_interface()
        window.destroy()
    
    def show_api_settings(self):
        api_win = tk.Toplevel(self.root)
        api_win.title("修改API Key")
        api_win.geometry("400x200")
        
        tk.Label(api_win, text="DeepSeek API Key:", 
                font=("Microsoft YaHei", 11)).pack(anchor='w', padx=20, pady=(30, 5))
        
        api_var = tk.StringVar(value=self.api_key)
        tk.Entry(api_win, textvariable=api_var, 
                width=40, font=("Microsoft YaHei", 11)).pack(padx=20)
        
        btn_frame = tk.Frame(api_win)
        btn_frame.pack(fill='x', padx=20, pady=30)
        
        tk.Button(btn_frame, text="保存", command=lambda: self.save_api_key(api_var.get(), api_win),
                 font=("Microsoft YaHei", 11), bg="#4CAF50", fg="white").pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="取消", command=api_win.destroy,
                 font=("Microsoft YaHei", 11)).pack(side='left', padx=5)
    
    def save_api_key(self, api_key, window):
        self.api_key = api_key
        self.save_settings()
        window.destroy()
        messagebox.showinfo("成功", "API Key已更新")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ChenLiXiChat()
    app.run()
