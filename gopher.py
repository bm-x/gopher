import os
import time
import win32api
import win32con
import win32gui
import win32ui
import numpy as np
from bound import TimeNode, Slice
import cv2 as cv

loop = True
drawResult = False
drawCapture = False
vpt = 0.6
baseWidth = 1080
imagineFindTime = 0.02
captureFileName = "capture.bmp"
timeNodes = (
    TimeNode(15, 0.1, 0.28),
    TimeNode(30, 0.09, 0.2),
    TimeNode(60, 0.07, 0.1),
    TimeNode(90, 0.05, 0.08),
    TimeNode(120, 0.04, 0.06)
)
slices = (
    Slice("find1.bmp", "小地鼠"),
    Slice("find2.bmp", "大地鼠"),
    Slice("find3.bmp", "宝箱一"),
    Slice("find4.bmp", "宝箱二")
)


def prepareFinds():
    for slice in slices:
        img = cv.imread(slice.fileName, 0)
        x, y = img.shape[::-1]
        slice.width = int(x / ratio)
        slice.height = int(y / ratio)
        slice.img = cv.resize(img, (slice.width, slice.height), interpolation=cv.INTER_CUBIC)
        slice.centerX = int(slice.width / 2)
        slice.centerY = int(slice.height / 2)
        slice.covertName = "%s_resize_gray.png" % slice.fileName[:-4]

    # for slice in slices:
    #     cv.imwrite(slice.covertName, slice.img)


def findWindow():
    parent = win32gui.FindWindow(None, "雷电模拟器")
    if parent == 0:
        return None
    hwndChildList = []
    win32gui.EnumChildWindows(parent, lambda hwnd, param: param.append(hwnd), hwndChildList)
    return hwndChildList[0]


def capture(hwnd):
    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()
    bitmap = win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(mfcDC, ww, wh)
    saveDC.SelectObject(bitmap)
    saveDC.BitBlt((0, 0), (ww, wh), mfcDC, (0, 0), win32con.SRCCOPY)
    if drawCapture: bitmap.SaveBitmapFile(saveDC, captureFileName)
    arr = bitmap.GetBitmapBits(True)
    img = np.fromstring(arr, dtype=np.uint8)
    img.shape = (wh, ww, 4)
    mfcDC.DeleteDC()
    saveDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwndDC)
    win32gui.DeleteObject(bitmap.GetHandle())
    return cv.cvtColor(img, cv.COLOR_RGBA2GRAY)


def findLocation(capture):
    for slice in slices:
        res = cv.matchTemplate(capture, slice.img, cv.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv.minMaxLoc(res)

        if max_val < vpt: continue

        if drawResult:
            rgb = cv.imread(captureFileName)
            cv.rectangle(rgb, max_loc, (max_loc[0] + slice.width, max_loc[1] + slice.height), (0, 0, 255), 3)
            cv.rectangle(capture, max_loc, (max_loc[0] + slice.width, max_loc[1] + slice.height), (0, 0, 255), 3)
            cv.imwrite("find_gray.png", slice.img)
            cv.imwrite("res_rgb.png", rgb)
            cv.imwrite("res_gray.png", capture)

        return int(max_loc[0] + slice.centerX), int(max_loc[1] + slice.centerY), slice.name
    return None


def capture2(hwnd, name=captureFileName):
    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()
    bitmap = win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(mfcDC, ww, wh)
    saveDC.SelectObject(bitmap)
    saveDC.BitBlt((0, 0), (ww, wh), mfcDC, (0, 0), win32con.SRCCOPY)
    bitmap.SaveBitmapFile(saveDC, name)


def findLocation2():
    capture = cv.imread(captureFileName, 0)
    for slice in slices:
        res = cv.matchTemplate(capture, slice.img, cv.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv.minMaxLoc(res)

        # print("found max value ->", max_val)

        if max_val < vpt:
            continue

        if drawResult:
            rgb = cv.imread(captureFileName)
            cv.rectangle(rgb, max_loc, (max_loc[0] + slice.width, max_loc[1] + slice.height), (0, 0, 255), 3)
            cv.rectangle(capture, max_loc, (max_loc[0] + slice.width, max_loc[1] + slice.height), (0, 0, 255), 3)
            cv.imwrite("find_gray.png", slice.img)
            cv.imwrite("res_rgb.png", rgb)
            cv.imwrite("res_gray.png", capture)

        return int(max_loc[0] + slice.centerX), int(max_loc[1] + slice.centerY), slice.name
    return None


def sendTap(x, y):
    click(x, y)


# sendMessage模拟后台点击
def click(x, y):
    point = win32api.MAKELONG(int(x), int(y))
    win32gui.SendMessage(hwnd, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)
    win32gui.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, point)
    win32gui.SendMessage(hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, point)


# 通过ADB进行点击
def clickADB(x, y):
    os.system("adb shell input tap %d %d" % (int(x * ratio), int(y * ratio)))


# 移动整个电脑的鼠标进行点击
def clickMouse(x, y):
    rx = int(x) + wleft
    ry = int(y) + wtop
    win32api.SetCursorPos((rx, ry))
    time.sleep(0.04)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def runOnce():
    start = time.time()

    # do not save file
    img = capture(hwnd)
    result = findLocation(img)
    useTime = time.time() - start

    # save file mode
    # capture2(hwnd)
    # result = findLocation2()

    if result is not None:
        x, y, name = result
        print("找到 -> [%s]    位置 -> (%d,%d)    用时 -> %f" % (name, x, y, useTime))
        sendTap(x, y)
        return True, useTime
    else:
        print("未找到匹配项")
        return False, 0


def runLoop():
    while True:
        found, useTime = runOnce()

        during = time.time() - beginTime
        interval = timeNodes[0].captureInterval

        for index, node in enumerate(timeNodes):
            if index >= len(timeNodes) - 1: during = node.time
            if during <= node.time:
                interval = node.captureInterval
                if found: interval = node.captureInterval + node.foundDealy
                break

        if useTime > imagineFindTime: interval = interval - useTime + imagineFindTime

        time.sleep(interval)


beginTime = time.time()
hwnd = findWindow()
if hwnd is None:
    print("未找到雷电模拟器")
    exit()
wleft, wtop, wright, wbotton = win32gui.GetWindowRect(hwnd)
ww = wright - wleft
wh = wbotton - wtop
ratio = baseWidth / ww

prepareFinds()

if loop:
    runLoop()
else:
    runOnce()

print("end")
