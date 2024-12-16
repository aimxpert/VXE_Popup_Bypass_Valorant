import os
import psutil
import subprocess
import time
import ctypes
import sys
import json
import requests
from ctypes import wintypes
import tkinter as tk
from tkinter import messagebox
import threading
import requests
import logging
import sys

def detect_debugging_tools():
    suspicious_processes = ['ida.exe', 'ida64.exe', 'x64dbg.exe', 'x32dbg.exe', 'ollydbg.exe', 'cheatengine-x86_64.exe', 'cheatengine.exe', 'charles.exe', 'wireshark.exe', 'procmon.exe', 'de4dot.exe', 'dnspy.exe']
    for proc in psutil.process_iter(['name', 'pid']):
        if proc.info['name'] and proc.info['name'].lower() in suspicious_processes:
            print(f"Debugging tool detected: {proc.info['name']}0")
            return True
    else:
        return False

def anti_debug_check():
    if detect_debugging_tools():
        print('Terminating application due to detected debugging tool.')
        sys.exit(1)

def check_debugger():
    """Check for debugger presence."""
    if ctypes.windll.kernel32.IsDebuggerPresent() != 0:
        clear_screen()
        print('Debugger detected! Exiting.')
        sys.exit(1)

def validate_license(license_key, user_name):
    # yedim
    if license_key == 'kay1337' and user_name == 'kay1337':
        return True
        
THREAD_SUSPEND_RESUME = 2
THREAD_QUERY_INFORMATION = 64
THREAD_ALL_ACCESS = 2032639
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
kernel32.QueryThreadCycleTime.restype = wintypes.BOOL
kernel32.QueryThreadCycleTime.argtypes = [wintypes.HANDLE, ctypes.POINTER(ctypes.c_uint64)]
kernel32.SuspendThread.restype = wintypes.DWORD
kernel32.SuspendThread.argtypes = [wintypes.HANDLE]

def open_thread(thread_id):
    return kernel32.OpenThread(THREAD_SUSPEND_RESUME | THREAD_QUERY_INFORMATION, False, thread_id)

def suspend_thread(thread_id):
    handle = open_thread(thread_id)
    if handle:
        try:
            result = kernel32.SuspendThread(handle)
            if result == -1:
                raise Exception('Error suspending thread')
        finally:
            kernel32.CloseHandle(handle)

def resume_thread(thread_id):
    handle = open_thread(thread_id)
    if handle:
        try:
            result = kernel32.ResumeThread(handle)
            if result == -1:
                raise Exception('Error resuming thread')
        finally:
            kernel32.CloseHandle(handle)

def close_handle(handle):
    kernel32.CloseHandle(handle)

def get_process_id_by_name(process_name):
    for proc in psutil.process_iter(['name', 'pid']):
        if proc.info['name'] == process_name:
            return proc.info['pid']
    else:
        return None

def list_thread_cycles(process_name):
    process_id = get_process_id_by_name(process_name)
    if process_id:
        process = psutil.Process(process_id)
        threads = process.threads()
        thread_cycles = {}
        for thread in threads:
            cycle_time = get_thread_cycle_time(thread.id)
            thread_cycles[thread.id] = cycle_time
        time.sleep(1)
        for thread in threads:
            current_cycle_time = get_thread_cycle_time(thread.id)
            delta = current_cycle_time - thread_cycles[thread.id]
            if delta == 0:
                suspend_thread(thread.id)

def get_thread_cycle_time(thread_id):
    handle = open_thread(thread_id)
    if handle:
        try:
            cycle_time = ctypes.c_uint64()
            result = kernel32.QueryThreadCycleTime(handle, ctypes.byref(cycle_time))
            if not result:
                raise Exception('Error querying thread cycle time')
            return cycle_time.value
        finally:
            close_handle(handle)

def stop_service(service_name):
    subprocess.run(['sc', 'stop', service_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def start_service_and_wait(service_name):
    subprocess.run(['sc', 'start', service_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5)

def suspend_threads_by_index(process_name):
    suspended_threads = []
    process_id = get_process_id_by_name(process_name)
    if process_id:
        process = psutil.Process(process_id)
        threads = process.threads()
        thread_cycles = {thread.id: get_thread_cycle_time(thread.id) for thread in threads}
        time.sleep(1)
        deltas = {}
        for thread in threads:
            current_cycle_time = get_thread_cycle_time(thread.id)
            delta = current_cycle_time - thread_cycles[thread.id]
            deltas[thread.id] = delta
        highest_delta_threads = sorted(deltas.items(), key=lambda x: x[1], reverse=True)[:2]
        for thread_id, _ in highest_delta_threads:
            suspend_thread(thread_id)
            suspended_threads.append(thread_id)
    return suspended_threads

def is_user_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def run_as_admin():
    script = sys.argv[0]
    params = ' '.join(sys.argv[1:])
    ctypes.windll.shell32.ShellExecuteW(None, 'runas', sys.executable, f'"{script}0" {params}0', None, 1)

def get_resource_path(relative_path):
    """Get the absolute path to a resource, works for dev and PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)

def inject_dll():
    """Inject the DLL using kernelOS.exe."""

    def injection_process():
        exe_path = get_resource_path('kernelOS.exe')
        dll_path = get_resource_path('VXEWARE.dll')
        try:
            if not os.path.exists(exe_path):
                self.update_status('Injector not found!', '#FF3333')
                return
            if not os.path.exists(dll_path):
                self.update_status('DLL not found!', '#FF3333')
            else:
                subprocess.run([exe_path, dll_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.update_status('DLL Injected Successfully!', '#00FF00')
        except Exception as e:
            self.update_status(f'Injection Failed: {str(e)}0', '#FF3333')
    threading.Thread(target=injection_process, daemon=True).start()

class App:

    def __init__(self, root):
        self.root = root
        self.root.title('VXE Bypass')
        self.root.geometry('500x450')
        self.root.resizable(False, False)
        self.root.configure(bg='#121212')
        self.status_label = tk.Label(self.root, text='Ready', font=('Arial', 12), fg='#00FF00', bg='#121212')
        self.status_label.pack(pady=(20, 5))
        self.info_label = tk.Label(self.root, text='Waiting for Valorant...', font=('Arial', 10), fg='#FF3333', bg='#121212')
        self.info_label.place(x=190, y=420)
        self.button_frame = tk.Frame(self.root, bg='#121212')
        self.button_frame.pack(pady=20)
        self.auto_bypass_enabled = False
        self.create_button('Bypass Popup', self.bypass_popup)
        self.create_button('Restart Game', self.restart_game)
        self.create_button('Auto Bypass: OFF', self.toggle_auto_bypass, is_auto_bypass=True)
        self.create_button('Unlock all', inject_dll)
        threading.Thread(target=self.check_valorant_status, daemon=True).start()

    def create_button(self, text, command, is_auto_bypass=False):
        button = tk.Button(self.button_frame, text=text, command=command, font=('Arial', 14), width=20, height=2, bg='#333333', fg='white', relief='flat', activebackground='#555555', activeforeground='white')
        button.pack(pady=10)
        if is_auto_bypass:
            self.auto_bypass_button = button

    def update_status(self, message, color='#00FF00'):
        self.status_label.config(text=message, fg=color)

    def bypass_popup(self):
        process_name = 'vgc.exe'
        list_thread_cycles(process_name)
        self.update_status('Popup Bypassed!', '#00FF00')

    def toggle_auto_bypass(self):
        self.auto_bypass_enabled = not self.auto_bypass_enabled
        status = 'ON' if self.auto_bypass_enabled else 'OFF'
        self.update_status(f'Auto Bypass: {status}0', '#FFFF00')
        self.auto_bypass_button.config(text=f'Auto Bypass: {status}0')
        if self.auto_bypass_enabled:
            threading.Thread(target=self.wait_for_valorant_and_bypass, daemon=True).start()

    def wait_for_valorant_and_bypass(self):
        process_name = 'VALORANT-Win64-Shipping.exe'
        self.update_status('Waiting for Valorant...', '#FFFF00')
        while self.auto_bypass_enabled and (not get_process_id_by_name(process_name)):
            time.sleep(1)
            if not self.auto_bypass_enabled:
                self.update_status('Auto Bypass Disabled', '#FF3333')
                return
        if self.auto_bypass_enabled:
            self.update_status('Valorant detected!', '#00FF00')
            countdown = 28
            while countdown > 0 and self.auto_bypass_enabled:
                self.update_status(f'Auto Bypass: {countdown}s', '#FFFF00')
                time.sleep(1)
                countdown -= 1
            if self.auto_bypass_enabled:
                self.bypass_popup()

    def restart_game(self):
        self.update_status('Restarting Game...', '#FFFF00')
        service_name = 'vgc'
        stop_service(service_name)
        suspended_threads = suspend_threads_by_index('VALORANT-Win64-Shipping.exe')
        start_service_and_wait(service_name)
        for thread_id in suspended_threads:
            resume_thread(thread_id)
            time.sleep(1)
        self.update_status('Game Restarted!', '#00FF00')

    def check_valorant_status(self):
        process_name = 'VALORANT-Win64-Shipping.exe'
        while True:
            if get_process_id_by_name(process_name):
                self.info_label.config(text='Valorant Found', fg='#00FF00')
            else:
                self.info_label.config(text='Waiting for Valorant...', fg='#FF3333')
            time.sleep(1)

def main():
    check_debugger()
    anti_debug_check()
    license_key = input('Enter your license key: ').strip()
    user_name = input('Enter your username: ').strip()
    if not validate_license(license_key, user_name):
        print('License validation failed. Exiting the program.')
        sys.exit(1)
    if not is_user_admin():
        run_as_admin()
        return
    threading.Thread(target=periodic_anti_debug_check, daemon=True).start()
    root = tk.Tk()
    app = App(root)
    root.mainloop()

def periodic_anti_debug_check():
    """Periodically run anti-debugging checks to prevent tampering."""
    while True:
        check_debugger()
        anti_debug_check()
        time.sleep(10)
if __name__ == '__main__':
    main()