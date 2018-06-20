import cv2 as cv
import pytesseract

img = cv.imread("captcha.jpg", 0)
cv.imwrite("captcha_gray.jpg", img)
ret,img2 = cv.threshold(img, 150, 255, cv.THRESH_BINARY_INV)
cv.imwrite("captcha_threshold.jpg", img2)
print(pytesseract.image_to_string(img2))
