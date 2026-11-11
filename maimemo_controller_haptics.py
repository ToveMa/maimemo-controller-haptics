# -*- coding: utf-8 -*-
"""Windows Chrome controller haptics helper for Ma imemo, using built-in XInput.
No third-party Python packages are required. This script does not hook or modify
Chrome, the Ma imemo page, controller firmware, or keyboard mappings.
"""
import ctypes
import os
import time
import tkinter as tk
from tkinter import ttk
from ctypes import wintypes

if os.name != "nt":
    raise SystemExit("本工具只支持 Windows。")


class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ("wButtons", wintypes.WORD),
        ("bLeftTrigger", ctypes.c_ubyte),
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]


class XINPUT_STATE(ctypes.Structure):
    _fields_ = [("dwPacketNumber", wintypes.DWORD), ("Gamepad", XINPUT_GAMEPAD)]


class XINPUT_VIBRATION(ctypes.Structure):
    _fields_ = [("wLeftMotorSpeed", wintypes.WORD), ("wRightMotorSpeed", wintypes.WORD)]


xinput = None
for dll_name in ("xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll"):
    try:
        xinput = ctypes.WinDLL(dll_name)
        break
    except OSError:
        continue
if xinput is None:
    raise SystemExit("未找到 Windows XInput 组件。")

xinput.XInputGetState.argtypes = [wintypes.DWORD, ctypes.POINTER(XINPUT_STATE)]
xinput.XInputGetState.restype = wintypes.DWORD
xinput.XInputSetState.argtypes = [wintypes.DWORD, ctypes.POINTER(XINPUT_VIBRATION)]
xinput.XInputSetState.restype = wintypes.DWORD

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
user32.GetForegroundWindow.argtypes = []
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL


def foreground():
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return "", ""
    title_buffer = ctypes.create_unicode_buffer(512)
    user32.GetWindowTextW(hwnd, title_buffer, len(title_buffer))
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    process = kernel32.OpenProcess(0x1000, False, pid.value)
    process_name = ""
    if process:
        try:
            path_buffer = ctypes.create_unicode_buffer(1024)
            length = wintypes.DWORD(len(path_buffer))
            if kernel32.QueryFullProcessImageNameW(process, 0, path_buffer, ctypes.byref(length)):
                process_name = os.path.basename(path_buffer.value).lower()
        finally:
            kernel32.CloseHandle(process)
    return process_name, title_buffer.value


def controller_state(slot):
    state = XINPUT_STATE()
    if xinput.XInputGetState(slot, ctypes.byref(state)) == 0:
        return state
    return None


def set_rumble(slot, power):
    speed = round(max(0, min(100, power)) * 65535 / 100)
    effect = XINPUT_VIBRATION(speed, speed)
    return xinput.XInputSetState(slot, ctypes.byref(effect)) == 0


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("墨墨背单词 · 手柄触觉反馈")
        self.root.geometry("540x340")
        self.root.minsize(500, 320)
        self.enabled = tk.BooleanVar(value=True)
        self.scope = tk.StringVar(value="墨墨标签页（窗口标题）")
        self.duration = tk.IntVar(value=120)
        self.status = tk.StringVar(value="正在检测 Windows XInput 手柄...")
        self.foreground_status = tk.StringVar(value="前台窗口：待检测")
        self.count = 0
        self.slot = None
        self.last_buttons = None
        self.rumble_end = 0.0
        self.last_scan = 0.0
        self.last_status = 0.0
        self.last_foreground = ("", "")
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(20, self.tick)

    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=16)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="手柄按键触觉反馈", font=("Microsoft YaHei UI", 16, "bold")).pack(anchor="w")
        ttk.Label(outer, text="独立于网页运行，不改动墨墨、Chrome 或手柄按键映射。", wraplength=500).pack(anchor="w", pady=(4, 10))
        ttk.Checkbutton(outer, text="开启按键震动", variable=self.enabled, command=self.set_enabled).pack(anchor="w")
        row = ttk.Frame(outer)
        row.pack(fill="x", pady=7)
        ttk.Label(row, text="生效范围：").pack(side="left")
        ttk.Combobox(row, textvariable=self.scope, state="readonly", width=27,
                     values=["墨墨标签页（窗口标题）", "所有 Chrome 标签页"]).pack(side="left", padx=5)
        row2 = ttk.Frame(outer)
        row2.pack(fill="x", pady=5)
        ttk.Label(row2, text="震动强度：").pack(side="left")
        ttk.Label(row2, text="固定最大（100%，左右马达全开）").pack(side="left", padx=4)
        row3 = ttk.Frame(outer)
        row3.pack(fill="x", pady=5)
        ttk.Label(row3, text="震动时长：").pack(side="left")
        ttk.Scale(row3, from_=50, to=300, variable=self.duration, orient="horizontal", length=210).pack(side="left", padx=4)
        ttk.Label(row3, textvariable=self.duration, width=4).pack(side="left")
        ttk.Label(row3, text="ms").pack(side="left")
        ttk.Button(outer, text="测试震动 0.5 秒", command=self.test_rumble).pack(anchor="w", pady=(10, 8))
        ttk.Label(outer, textvariable=self.status, foreground="#205887", wraplength=500).pack(anchor="w")
        ttk.Label(outer, textvariable=self.foreground_status, wraplength=500).pack(anchor="w", pady=5)
        ttk.Label(outer, text="提示：蓝牙模式如果不提供 XInput，请使用手柄原配 2.4G 接收器或 USB 数据线。", wraplength=500).pack(anchor="w", pady=4)

    def set_enabled(self):
        self.last_buttons = None
        if not self.enabled.get() and self.slot is not None:
            set_rumble(self.slot, 0)
            self.rumble_end = 0

    def scope_active(self):
        process, title = self.last_foreground
        if process != "chrome.exe":
            return False
        if self.scope.get() == "所有 Chrome 标签页":
            return True
        lower = title.lower()
        return any(key in lower for key in ("墨墨", "maimemo", "背单词"))

    def scan(self, now):
        if self.slot is not None and controller_state(self.slot) is not None:
            return
        if self.slot is not None:
            set_rumble(self.slot, 0)
        self.slot = None
        self.last_buttons = None
        self.rumble_end = 0
        if now - self.last_scan < 1.0:
            return
        self.last_scan = now
        for candidate in range(4):
            if controller_state(candidate) is not None:
                self.slot = candidate
                break

    def start_pulse(self, now, milliseconds):
        if self.slot is None:
            return False
        success = set_rumble(self.slot, 100)
        if success:
            self.rumble_end = now + milliseconds / 1000.0
        return success

    def test_rumble(self):
        now = time.monotonic()
        self.scan(now)
        if not self.start_pulse(now, 500):
            self.status.set("没有检测到可控制的 XInput 手柄；当前蓝牙模式可能不支持。")
        else:
            self.status.set("已发送 0.5 秒最大档位测试震动，请确认是否真的有震感。")

    def tick(self):
        now = time.monotonic()
        self.scan(now)
        if now - self.last_status >= 0.30:
            self.last_status = now
            self.last_foreground = foreground()
            process, title = self.last_foreground
            self.foreground_status.set("前台窗口：" + (title[:65] or "（无标题）") + ("  [Chrome]" if process == "chrome.exe" else ""))
            if self.slot is None:
                self.status.set("未检测到 XInput 手柄（蓝牙可能只提供其他输入协议）。")
            elif not self.enabled.get():
                self.status.set("震动已关闭，已检测到 XInput 手柄 %s。" % self.slot)
            else:
                state = "处于指定页面" if self.scope_active() else "等待指定 Chrome 页面"
                self.status.set(f"XInput 手柄 {self.slot}｜{state}｜已反馈 {self.count} 次")
        if self.slot is not None:
            if self.rumble_end and now >= self.rumble_end:
                set_rumble(self.slot, 0)
                self.rumble_end = 0
            state = controller_state(self.slot)
            if state is not None:
                pad = state.Gamepad
                buttons = pad.wButtons
                if pad.bLeftTrigger >= 40:
                    buttons |= 0x10000
                if pad.bRightTrigger >= 40:
                    buttons |= 0x20000
                if self.last_buttons is not None:
                    rising = buttons & ~self.last_buttons
                    if rising and self.enabled.get() and self.scope_active():
                        if self.start_pulse(now, self.duration.get()):
                            self.count += 1
                self.last_buttons = buttons
        self.root.after(12, self.tick)

    def close(self):
        if self.slot is not None:
            set_rumble(self.slot, 0)
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
