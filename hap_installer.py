#!/usr/bin/env python3
"""
HarmonyOS 设备工具
使用 CustomTkinter 实现 Apple 设计风格，内置深色/浅色主题
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import subprocess
import threading
import os
import platform
import re
import sys

ctk.set_appearance_mode("system")  # 默认跟随系统
ctk.set_default_color_theme("blue")  # Apple Blue 主题


class AppConfig:
    """应用配置 - 支持 hdc 内置打包"""

    @staticmethod
    def get_hdc_path():
        """获取 hdc 工具路径，优先使用内置版本"""
        is_windows = platform.system() == "Windows"
        hdc_name = "hdc.exe" if is_windows else "hdc"

        # 打包后：检查内置 hdc
        if getattr(sys, 'frozen', False):
            meipass = sys._MEIPASS
            possible_paths = [
                os.path.join(meipass, 'hdc', hdc_name),
                os.path.join(meipass, hdc_name),
            ]
            for path in possible_paths:
                if os.path.exists(path) and os.path.isfile(path):
                    return path

        # 开发模式：检查本地 hdc 目录
        base_dir = os.path.dirname(__file__)
        if is_windows:
            local_hdc = os.path.join(base_dir, 'hdc', 'windows', hdc_name)
        else:
            local_hdc = os.path.join(base_dir, 'hdc', hdc_name)
        if os.path.exists(local_hdc):
            return local_hdc

        # DevEco Studio 默认路径
        if platform.system() == "Darwin":
            default = "/Applications/DevEco-Studio.app/Contents/sdk/default/openharmony/toolchains/hdc"
        elif platform.system() == "Windows":
            default = "C:/Program Files/DevEco-Studio/sdk/default/openharmony/toolchains/hdc.exe"
        else:
            default = "/opt/DevEco-Studio/sdk/default/openharmony/toolchains/hdc"

        if os.path.exists(default):
            return default

        env_path = os.environ.get("HDC_PATH")
        if env_path and os.path.exists(env_path):
            return env_path

        return None


class HdcTool:
    """封装 hdc 命令执行"""

    def __init__(self):
        self.hdc_path = AppConfig.get_hdc_path()
        self.current_device = None

    def _run_command(self, args, timeout=30):
        """执行 hdc 命令"""
        if not self.hdc_path:
            return "", "hdc 工具未找到", -1

        cmd = [self.hdc_path]
        if self.current_device:
            cmd.extend(["-t", self.current_device])
        cmd.extend(args)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return result.stdout.strip(), result.stderr.strip(), result.returncode
        except subprocess.TimeoutExpired:
            return "", "命令执行超时", -1
        except FileNotFoundError:
            return "", f"hdc 工具未找到: {self.hdc_path}", -1

    def list_devices(self):
        stdout, stderr, code = self._run_command(["list", "targets"])
        if code == 0 and stdout:
            return [d.strip() for d in stdout.split("\n") if d.strip()]
        return []

    def get_udid(self):
        stdout, stderr, code = self._run_command(["shell", "bm", "get", "--udid"])
        if code == 0 and stdout:
            match = re.search(r"udid of current device is :\s*(\S+)", stdout)
            if match:
                return match.group(1)
            return stdout.strip()
        return stderr or "获取 UDID 失败"

    def install_hap(self, hap_path, replace=False):
        args = ["install"]
        if replace:
            args.append("-r")
        args.append(hap_path)
        stdout, stderr, code = self._run_command(args, timeout=120)
        return stdout, stderr, code == 0

    def uninstall_app(self, package_name, keep_data=False):
        args = ["uninstall"]
        if keep_data:
            args.append("-k")
        args.append(package_name)
        stdout, stderr, code = self._run_command(args)
        return stdout, stderr, code == 0

    def list_installed_apps(self):
        stdout, stderr, code = self._run_command(["shell", "bm", "dump", "-a"])
        if code == 0 and stdout:
            apps = []
            for line in stdout.split("\n"):
                if "com." in line or "ohos." in line:
                    match = re.search(r"(\S+)", line.strip())
                    if match:
                        apps.append(match.group(1))
            return apps
        return []

    def get_app_info(self, package_name):
        stdout, stderr, code = self._run_command(["shell", "bm", "dump", "-n", package_name])
        return stdout if code == 0 else stderr


class MainWindow(ctk.CTk):
    """主窗口 - 使用 CustomTkinter 实现 Apple 设计风格"""

    def __init__(self):
        super().__init__()

        self.title("HarmonyOS Device Tool")
        self.geometry("650x550")

        self.hdc = HdcTool()
        self.log_process = None
        self.log_running = False

        self._create_widgets()
        self._refresh_devices()

    def _create_widgets(self):
        """创建所有界面组件"""
        # 标题栏
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 10))

        ctk.CTkLabel(
            header,
            text="HarmonyOS Device Tool",
            font=("Helvetica", 18, "bold"),
            text_color="#0071e3"
        ).pack(side="left")

        # 主题切换按钮
        self.theme_btn = ctk.CTkButton(
            header,
            text="🌙",
            width=40,
            command=self._toggle_theme,
            fg_color="transparent",
            text_color=("gray10", "#DCE4EE"),
            hover_color=("gray70", "gray25")
        )
        self.theme_btn.pack(side="right")

        # 设备选择栏
        device_frame = ctk.CTkFrame(self, fg_color="transparent")
        device_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(device_frame, text="设备:", font=("Helvetica", 11)).pack(side="left")

        self.device_combo = ctk.CTkComboBox(device_frame, width=280, state="readonly")
        self.device_combo.pack(side="left", padx=5)
        self.device_combo.set("无设备")

        ctk.CTkButton(device_frame, text="刷新", width=80, command=self._refresh_devices).pack(side="left", padx=5)

        # UDID 区域
        udid_frame = ctk.CTkFrame(self, fg_color="transparent")
        udid_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(udid_frame, text="UDID:", font=("Helvetica", 11)).pack(side="left")

        self.udid_var = tk.StringVar(value="点击「获取 UDID」按钮")
        self.udid_entry = ctk.CTkEntry(udid_frame, textvariable=self.udid_var, width=350, state="readonly")
        self.udid_entry.pack(side="left", padx=5, fill="x", expand=True)

        ctk.CTkButton(udid_frame, text="获取 UDID", width=100, command=self._get_udid).pack(side="left", padx=5)

        self.copy_btn = ctk.CTkButton(udid_frame, text="📋 复制", width=70, command=self._copy_udid)
        self.copy_btn.pack(side="left")

        # 标签页
        self.notebook = ctk.CTkTabview(self, width=600)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=10)

        self.install_tab = self.notebook.add("应用安装")
        self.apps_tab = self.notebook.add("已安装应用")
        self.log_tab = self.notebook.add("设备日志")

        self._create_install_tab()
        self._create_apps_tab()
        self._create_log_tab()

        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        self.status_label = ctk.CTkLabel(self, textvariable=self.status_var, font=("Helvetica", 9), text_color="gray")
        self.status_label.pack(fill="x", side="bottom", padx=10, pady=5)

    def _create_install_tab(self):
        """安装标签页"""
        tab = self.install_tab

        # 安装区域
        install_frame = ctk.CTkFrame(tab)
        install_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(install_frame, text="安装 HAP", font=("Helvetica", 12, "bold")).pack(pady=(5, 10))

        hap_row = ctk.CTkFrame(install_frame, fg_color="transparent")
        hap_row.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(hap_row, text="HAP 文件:", font=("Helvetica", 11)).pack(side="left")

        self.hap_path_var = tk.StringVar()
        ctk.CTkEntry(hap_row, textvariable=self.hap_path_var, width=300).pack(side="left", padx=5, fill="x", expand=True)

        ctk.CTkButton(hap_row, text="选择文件", width=80, command=self._select_hap_file).pack(side="left")

        option_row = ctk.CTkFrame(install_frame, fg_color="transparent")
        option_row.pack(fill="x", padx=10, pady=10)

        self.replace_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(option_row, text="替换安装 (-r)", variable=self.replace_var).pack(side="left")

        self.install_btn = ctk.CTkButton(option_row, text="安装", width=80, command=self._install_hap)
        self.install_btn.pack(side="right")

        # 卸载区域
        uninstall_frame = ctk.CTkFrame(tab)
        uninstall_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(uninstall_frame, text="卸载应用", font=("Helvetica", 12, "bold")).pack(pady=(5, 10))

        pkg_row = ctk.CTkFrame(uninstall_frame, fg_color="transparent")
        pkg_row.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(pkg_row, text="包名:", font=("Helvetica", 11)).pack(side="left")

        self.package_var = tk.StringVar()
        ctk.CTkEntry(pkg_row, textvariable=self.package_var, width=300).pack(side="left", padx=5, fill="x", expand=True)

        ctk.CTkButton(pkg_row, text="从列表选择", width=80, command=self._select_package).pack(side="left")

        option_row2 = ctk.CTkFrame(uninstall_frame, fg_color="transparent")
        option_row2.pack(fill="x", padx=10, pady=10)

        self.keep_data_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(option_row2, text="保留数据 (-k)", variable=self.keep_data_var).pack(side="left")

        self.uninstall_btn = ctk.CTkButton(option_row2, text="卸载", width=80, fg_color="#ff3b30", hover_color="#cc2f26", command=self._uninstall_app)
        self.uninstall_btn.pack(side="right")

        # 结果显示
        result_frame = ctk.CTkFrame(tab)
        result_frame.pack(fill="both", expand=True, padx=10)

        ctk.CTkLabel(result_frame, text="执行结果", font=("Helvetica", 12, "bold")).pack(pady=(5, 5))

        self.result_text = ctk.CTkTextbox(result_frame, height=150)
        self.result_text.pack(fill="both", expand=True, padx=5, pady=5)

    def _create_apps_tab(self):
        """已安装应用标签页"""
        tab = self.apps_tab

        control_frame = ctk.CTkFrame(tab, fg_color="transparent")
        control_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkButton(control_frame, text="刷新列表", width=100, command=self._refresh_apps).pack(side="left")

        ctk.CTkLabel(control_frame, text="搜索:", font=("Helvetica", 10)).pack(side="left", padx=(15, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._filter_apps)
        ctk.CTkEntry(control_frame, textvariable=self.search_var, width=150).pack(side="left")

        list_frame = ctk.CTkFrame(tab)
        list_frame.pack(fill="both", expand=True, padx=10)

        self.apps_listbox = tk.Listbox(list_frame, font=("Helvetica", 10), borderwidth=0, selectbackground="#0071e3")
        self.apps_listbox.pack(fill="both", expand=True, side="left")

        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self.apps_listbox.yview)
        scrollbar.pack(fill="y", side="right")
        self.apps_listbox.config(yscrollcommand=scrollbar.set)

        self.apps_listbox.bind("<Double-Button-1>", self._show_app_info)
        self.apps_listbox.bind("<Button-3>", self._show_apps_menu)

        self.apps_menu = tk.Menu(self, tearoff=0)
        self.apps_menu.add_command(label="卸载此应用", command=self._uninstall_selected)
        self.apps_menu.add_command(label="复制包名", command=self._copy_package)

    def _create_log_tab(self):
        """设备日志标签页"""
        tab = self.log_tab

        control_frame = ctk.CTkFrame(tab, fg_color="transparent")
        control_frame.pack(fill="x", pady=10, padx=10)

        self.start_log_btn = ctk.CTkButton(control_frame, text="▶ 开始", width=80, fg_color="#34c759", hover_color="#28a745", command=self._start_log)
        self.start_log_btn.pack(side="left")

        self.stop_log_btn = ctk.CTkButton(control_frame, text="■ 停止", width=80, fg_color="#ff3b30", hover_color="#cc2f26", command=self._stop_log, state="disabled")
        self.stop_log_btn.pack(side="left", padx=5)

        ctk.CTkButton(control_frame, text="清空", width=60, command=self._clear_log).pack(side="left", padx=5)

        ctk.CTkLabel(control_frame, text="过滤:", font=("Helvetica", 10)).pack(side="left", padx=(15, 5))

        self.log_filter_var = tk.StringVar()
        ctk.CTkEntry(control_frame, textvariable=self.log_filter_var, width=100).pack(side="left")

        self.log_text = ctk.CTkTextbox(tab, height=200)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)

    def _toggle_theme(self):
        """切换深色/浅色主题"""
        current = ctk.get_appearance_mode()
        new_mode = "Dark" if current == "Light" else "Light"
        ctk.set_appearance_mode(new_mode)
        self.theme_btn.configure(text="☀️" if new_mode == "Dark" else "🌙")

    def _refresh_devices(self):
        """刷新设备列表"""
        if not self.hdc.hdc_path:
            self._show_warning("hdc 工具未找到")
            self.status_var.set("hdc 工具未找到")
            return

        devices = self.hdc.list_devices()
        self.device_combo.configure(values=devices if devices else ["无设备"])

        if devices:
            self.device_combo.set(devices[0])
            self.hdc.current_device = devices[0]
            self.status_var.set(f"已连接 {len(devices)} 个设备")
        else:
            self.device_combo.set("无设备")
            self.hdc.current_device = None
            self.status_var.set("未检测到设备")

    def _get_udid(self):
        if not self.hdc.current_device:
            self._show_warning("请先选择设备")
            return
        self.status_var.set("正在获取 UDID...")
        threading.Thread(target=self._get_udid_thread, daemon=True).start()

    def _get_udid_thread(self):
        udid = self.hdc.get_udid()
        self.after(0, lambda: self.udid_var.set(udid))
        self.after(0, lambda: self.status_var.set("UDID 已获取"))

    def _copy_udid(self):
        udid = self.udid_var.get()
        if udid and udid != "点击「获取 UDID」按钮" and "未获取" not in udid:
            self.clipboard_clear()
            self.clipboard_append(udid)
            self.status_var.set("UDID 已复制到剪贴板")
        else:
            self._show_warning("请先获取 UDID")

    def _select_hap_file(self):
        file_path = filedialog.askopenfilename(
            title="选择 HAP 文件", filetypes=[("HAP files", "*.hap *.app"), ("All files", "*.*")]
        )
        if file_path:
            self.hap_path_var.set(file_path)

    def _install_hap(self):
        hap_path = self.hap_path_var.get()
        if not hap_path or not self.hdc.current_device:
            self._show_warning("请选择 HAP 文件和设备")
            return
        self.status_var.set("正在安装...")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("end", f"安装文件: {hap_path}\n")
        threading.Thread(target=self._install_thread, args=(hap_path,), daemon=True).start()

    def _install_thread(self, hap_path):
        stdout, stderr, success = self.hdc.install_hap(hap_path, self.replace_var.get())
        result = stdout + "\n" + stderr if stderr else stdout
        self.after(0, lambda: self._update_result(result, success))

    def _uninstall_app(self):
        package = self.package_var.get()
        if not package or not self.hdc.current_device:
            self._show_warning("请输入包名并选择设备")
            return
        self.status_var.set("正在卸载...")
        threading.Thread(target=self._uninstall_thread, args=(package,), daemon=True).start()

    def _uninstall_thread(self, package):
        stdout, stderr, success = self.hdc.uninstall_app(package, self.keep_data_var.get())
        result = stdout + "\n" + stderr if stderr else stdout
        self.after(0, lambda: self._update_result(result, success))

    def _update_result(self, result, success):
        self.result_text.delete("1.0", "end")
        self.result_text.insert("end", result)
        self.status_var.set("安装成功" if success else "安装失败")

    def _refresh_apps(self):
        if not self.hdc.current_device:
            self._show_warning("请先选择设备")
            return
        self.status_var.set("正在获取应用列表...")
        threading.Thread(target=self._refresh_apps_thread, daemon=True).start()

    def _refresh_apps_thread(self):
        apps = self.hdc.list_installed_apps()
        self.after(0, lambda: self._update_apps_list(apps))

    def _update_apps_list(self, apps):
        self.apps_listbox.delete(0, "end")
        self.all_apps = apps
        for app in apps:
            self.apps_listbox.insert("end", app)
        self.status_var.set(f"已加载 {len(apps)} 个应用")

    def _filter_apps(self, *args):
        if not hasattr(self, "all_apps"):
            return
        keyword = self.search_var.get().lower()
        self.apps_listbox.delete(0, "end")
        for app in self.all_apps:
            if keyword in app.lower():
                self.apps_listbox.insert("end", app)

    def _select_package(self):
        self.notebook.set("已安装应用")
        if self.apps_listbox.size() == 0:
            self._refresh_apps()

    def _show_app_info(self, event):
        selection = self.apps_listbox.curselection()
        if not selection:
            return
        package = self.apps_listbox.get(selection[0])
        info = self.hdc.get_app_info(package)
        self.result_text.delete("1.0", "end")
        self.result_text.insert("end", info)
        self.notebook.set("应用安装")

    def _show_apps_menu(self, event):
        self.apps_listbox.selection_clear(0, "end")
        self.apps_listbox.select_set(self.apps_listbox.nearest(event.y))
        self.apps_menu.tk_popup(event.x_root, event.y_root)

    def _uninstall_selected(self):
        selection = self.apps_listbox.curselection()
        if not selection:
            return
        package = self.apps_listbox.get(selection[0])
        self.package_var.set(package)
        self.notebook.set("应用安装")

    def _copy_package(self):
        selection = self.apps_listbox.curselection()
        if not selection:
            return
        package = self.apps_listbox.get(selection[0])
        self.clipboard_clear()
        self.clipboard_append(package)
        self.status_var.set("包名已复制")

    def _start_log(self):
        if not self.hdc.current_device or not self.hdc.hdc_path:
            self._show_warning("请先选择设备")
            return

        self.log_running = True
        self.start_log_btn.configure(state="disabled")
        self.stop_log_btn.configure(state="normal")

        cmd = [self.hdc.hdc_path, "-t", self.hdc.current_device, "hilog"]
        self.log_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                             text=True, bufsize=1)
        threading.Thread(target=self._read_log_thread, daemon=True).start()
        self.status_var.set("正在查看日志...")

    def _read_log_thread(self):
        while self.log_running and self.log_process:
            try:
                line = self.log_process.stdout.readline()
                if not line:
                    break
                filter_kw = self.log_filter_var.get().lower()
                if filter_kw and filter_kw not in line.lower():
                    continue
                self.after(0, lambda l=line: self._append_log(l))
            except:
                break

    def _append_log(self, line):
        self.log_text.insert("end", line)
        self.log_text.see("end")

    def _stop_log(self):
        self.log_running = False
        if self.log_process:
            self.log_process.terminate()
            self.log_process = None
        self.start_log_btn.configure(state="normal")
        self.stop_log_btn.configure(state="disabled")
        self.status_var.set("日志已停止")

    def _clear_log(self):
        self.log_text.delete("1.0", "end")

    def _show_warning(self, message):
        """显示警告对话框"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("提示")
        dialog.geometry("300x120")
        dialog.resizable(False, False)

        ctk.CTkLabel(dialog, text=message, font=("Helvetica", 11)).pack(pady=20)
        ctk.CTkButton(dialog, text="确定", width=80, command=dialog.destroy).pack()


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()