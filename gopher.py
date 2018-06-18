import os
import time
import win32api
import win32con
import win32gui
import win32ui

import cv2 as cv

loop = False
drawResult = False
intervals = [0.15, 0.1, 0.6]
vpt = 0.6
captureFileName = "capture.bmp"
baseWidth = 1080


class Cut:
    pass


findsName = ("find1.bmp", "find2.bmp", "find3.bmp", "find4.bmp")
findsSet = {"find1.bmp": "小地鼠", "find2.bmp": "大地鼠", "find3.bmp": "宝箱一", "find4.bmp": "宝箱二"}
finds = []


def prepareFinds():
    for findName in findsName:
        cut = Cut()
        img = cv.imread(findName, 0)
        x, y = img.shape[::-1]
        cut.name = findsSet[findName]
        cut.filePath = findName
        cut.width = int(x / ratio)
        cut.height = int(y / ratio)
        cut.img = cv.resize(img, (cut.width, cut.height), interpolation=cv.INTER_CUBIC)
        cut.centerX = int(cut.width / 2)
        cut.centerY = int(cut.height / 2)
        cut.covertName = "%s_resize_gray.png" % findName[:-4]
        finds.append(cut)

    # for cut in finds:
    #     cv.imwrite(cut.covertName, cut.img)


def findWindow():
    parent = win32gui.FindWindow(None, "雷电模拟器")
    if parent == 0:
        return None
    hwndChildList = []
    win32gui.EnumChildWindows(parent, lambda hwnd, param: param.append(hwnd), hwndChildList)
    return hwndChildList[0]


def capture(hwnd, name=captureFileName):
    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()
    bitmap = win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(mfcDC, ww, wh)
    saveDC.SelectObject(bitmap)
    saveDC.BitBlt((0, 0), (ww, wh), mfcDC, (0, 0), win32con.SRCCOPY)
    bitmap.SaveBitmapFile(saveDC, name)


def findLocation():
    capture = cv.imread(captureFileName, 0)
    for cut in finds:
        res = cv.matchTemplate(capture, cut.img, cv.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv.minMaxLoc(res)

        # print("found max value ->", max_val)

        if max_val < vpt:
            continue

        if drawResult:
            rgb = cv.imread(captureFileName)
            cv.rectangle(rgb, max_loc, (max_loc[0] + cut.width, max_loc[1] + cut.height), (0, 0, 255), 3)
            cv.rectangle(capture, max_loc, (max_loc[0] + cut.width, max_loc[1] + cut.height), (0, 0, 255), 3)
            cv.imwrite("find_gray.png", cut.img)
            cv.imwrite("res_rgb.png", rgb)
            cv.imwrite("res_gray.png", capture)

        return int(max_loc[0] + cut.centerX), int(max_loc[1] + cut.centerY), cut.name
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
    capture(hwnd)
    result = findLocation()
    if result is not None:
        x, y, name = result
        print("找到 -> [%s]    位置 -> (%d,%d)    用时 -> %f" % (name, x, y, (time.time() - start)))
        sendTap(x, y)
    else:
        print("未找到匹配项")


def runLoop():
    while True:
        start = time.time()
        capture(hwnd)
        result = findLocation()
        now = time.time()
        if result is not None:
            x, y, name = result
            sendTap(x, y)
            print("找到 -> [%s]    位置 -> (%d,%d)  用时 -> %f" % (name, x, y, (now - start)))

        during = now - beginTime

        if during < 15:
            interval = intervals[0]
        elif during < 30:
            interval = intervals[1]
        else:
            interval = intervals[2]

        # else:
        #     pass
        print("未找到匹配项")

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
