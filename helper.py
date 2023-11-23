import numpy as np
from io import BytesIO
import cv2
import fitz
import pytesseract
from pytesseract import Output
import os
from paddleocr import PaddleOCR
from dotenv import load_dotenv
load_dotenv()

Pocr = PaddleOCR(use_angle_cls=True)

tesseract_Path = os.getenv("TESSERACT_PATH")
def subset(set, lim, loc):
        '''
        set: one or multi list or array, lim: size, loc:location(small, medi, large)
        This function reconstructs set according to size of lim in location of loc.
        '''
        cnt, len_set = 0, len(set)        
        v_coor_y1, index_ = [], []
        pop = []
        for i in range(len_set):
            if i < len_set-1:
                try:
                    condition = set[i+1][0] - set[i][0]
                except:
                    condition = set[i+1] - set[i]
                if condition < lim:
                    cnt = cnt + 1
                    pop.append(set[i])
                else:
                    cnt = cnt + 1
                    pop.append(set[i])
                    pop = np.asarray(pop)
                    try:
                        if loc == "small": v_coor_y1.append([min(pop[:, 0]), min(pop[:, 1]), max(pop[:, 2])])
                        elif loc == "medi": v_coor_y1.append([int(np.median(pop[:, 0])), min(pop[:, 1]), max(pop[:, 2])])
                        else: v_coor_y1.append([max(pop[:, 0]), min(pop[:, 1]), max(pop[:, 2])])
                    except:
                        if loc == "small": v_coor_y1.append(min(pop))
                        elif loc == "medi": v_coor_y1.append(int(np.median(pop)))
                        else: v_coor_y1.append(max(pop))  
                    index_.append(cnt)
                    cnt = 0
                    pop = []
            else:
                cnt += 1
                pop.append(set[i])
                pop = np.asarray(pop)
                try:
                    if loc == "small": v_coor_y1.append([min(pop[:, 0]), min(pop[:, 1]), max(pop[:, 2])])
                    elif loc == "medi": v_coor_y1.append([int(np.median(pop[:, 0])), min(pop[:, 1]), max(pop[:, 2])])
                    else: v_coor_y1.append([max(pop[:, 0]), min(pop[:, 1]), max(pop[:, 2])])
                except:
                    if loc == "small": v_coor_y1.append(min(pop))
                    elif loc == "medi": v_coor_y1.append(int(np.median(pop)))
                    else: v_coor_y1.append(max(pop))                    
                index_.append(cnt)

        return v_coor_y1, index_ 

def split_pages(full_path):
    '''
    1. Splits the input pdf into pages
    2. Writes a temporary image for each page to a byte buffer
    3. Loads the image as a numpy array using cv2.imread()
    4. Appends the page image/array to self.pages

    Notes:
    PyMuPDF's get_pixmap() has a default output of 96dpi, while the desired
    resolution is 300dpi, hence the zoom factor of 300/96 = 3.125 ~ 3.
    '''
    if (full_path.split('.')[-1]).lower() == 'pdf':  
        print("Splitting PDF into pages")
        digit_doc = fitz.open(full_path)
        pages = []
        try:
            zoom_factor = 3
            for i in range(len(digit_doc)):
                # Load page and get pixmap
                page = digit_doc.load_page(i)
                pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom_factor, zoom_factor))

                # Initialize bytes buffer and write PNG image to buffer
                buffer = BytesIO()
                buffer.write(pixmap.tobytes())
                buffer.seek(0)

                # Load image from buffer as array, append to pages, close buffer
                img_array = np.asarray(bytearray(buffer.read()), dtype=np.uint8)
                page_img = cv2.imdecode(img_array, 1)
                pages.append(page_img)
                buffer.close()
        except:
            pass
    if len(pages) == 0:
        val = "01"
    else:
        val = [pages, digit_doc]
    return val

def approximate(li, limit):
    pre_l = li[0]
    new_li = []
    for l in li:
        if abs(l - pre_l) < limit:
            l = pre_l
        else:
            pre_l = l
        new_li.append(l)
    return new_li

def getting_textdata(img, config, zoom_fac, split_val, lang='eng', ths=30):
    '''
    img: soucr image to process.
    conf: tesseract conf (--psm xx)
    zoom_fac: image resize factor.
    split_val: factor to consider for coordinate of texts when image is splited into two parts
    '''

    # gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    # bin_img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1] 
    pytesseract.pytesseract.tesseract_cmd = tesseract_Path
    d = pytesseract.image_to_data(img, output_type=Output.DICT, lang=lang, config=config)
    text_ori = d['text']
    left_coor, top_coor, wid, hei, conf = d['left'], d['top'], d['width'], d['height'], d['conf']        
    ### removing None element from text ###
    text, left, top, w, h, accu, xc, yc= [], [], [], [], [], [], [], []
    for cnt, te in enumerate(text_ori):
        if te.strip() != '' and wid[cnt] > 10 and hei[cnt] > 10:
            if conf[cnt] >= ths:
                text.append(te)
                left.append(int((left_coor[cnt]+split_val)/zoom_fac))
                top.append(int(top_coor[cnt]/zoom_fac))
                w.append(int(wid[cnt]/zoom_fac))
                h.append(int(hei[cnt]/zoom_fac))
                accu.append(conf[cnt])    
                xc.append(int((left_coor[cnt]+wid[cnt]/2+split_val)/zoom_fac))
                yc.append(int((top_coor[cnt]+hei[cnt]/2)/zoom_fac))
    return text, left, top, w, h, accu, xc, yc
def line_remove(image):
    result = image.copy()
    gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # Remove vertical lines
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1,15))
    remove_vertical = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
    cnts = cv2.findContours(remove_vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    for c in cnts:
        cv2.drawContours(result, [c], -1, (255,255,255), 5)

    # Remove horizontal lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40,1))
    remove_horizontal = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    cnts = cv2.findContours(remove_horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    for c in cnts:
        cv2.drawContours(result, [c], -1, (255,255,255), 5)

    return result
def border_set(img_, coor, tk, color):
    '''
    coor: [x0, x1, y0, y1] - this denotes border locations.
    tk: border thickness, color: border color.
    '''
    img = img_.copy()
    if coor[0] != None:
        img[:, coor[0]:coor[0]+tk] = color # left vertical
    if coor[1] != None:
        img[:, coor[1]-tk:coor[1]] = color # right vertical
    if coor[2] != None:                    
        img[coor[2]:coor[2]+tk,:] = color # up horizontal
    if coor[3] != None:
        img[coor[3]-tk:coor[3],:] = color # down horizontal          
    return img  

def strengthBorder(img):
    H, W = img.shape[0:2]
    img = cv2.dilate(img, np.ones((1,10)), iterations=1)     
    kernel_hor = cv2.getStructuringElement(cv2.MORPH_RECT, (int(W/5), 1)) # vertical
    kernel_ver = cv2.getStructuringElement(cv2.MORPH_RECT, (1, int(H/5))) # vertical
    hor_temp = cv2.erode(img, kernel_hor, iterations=1)     
    ver_temp = cv2.erode(img, kernel_ver, iterations=1)   
    hor_temp = cv2.dilate(hor_temp, np.ones((1,W)), iterations=2)     
    ver_temp = cv2.dilate(ver_temp, np.ones((H,1)), iterations=2)       
    img_vh = cv2.addWeighted(ver_temp, 0.5, hor_temp, 0.5, 0.0)
    _, img_vh = cv2.threshold(img_vh, 50, 255, cv2.THRESH_BINARY) 
    img_vh = border_set(img_vh, [0, W, 0, H], 20, 0)
    return img_vh   
def getRectangle(im):
    img = im.copy()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgH, imgW = gray.shape
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    # thresh = strengthBorder(thresh)
    contours,hierarchy = cv2.findContours(thresh, 1, 2)
    # print("Number of contours detected:", len(contours))
    rects = []
    for cnt in contours:
        x1,y1 = cnt[0][0]
        approx = cv2.approxPolyDP(cnt, 0.01*cv2.arcLength(cnt, True), True)
        # if len(approx) < 5:
        x, y, w, h = cv2.boundingRect(cnt)
        # img = cv2.drawContours(img, [cnt], -1, (0,255,255), 3)
        if w > imgW/4 and w < imgW/3 and h <300 and h >180:
            img = cv2.drawContours(img, [cnt], -1, (0,255,255), 3)
            rects.append([y, x, h, w])
    rects.sort()
    if len(rects) > 0:
        # if not checkDigit: rects[0][3] = 400
        new_rects = [rects[0]]
        for i in range(1, len(rects)):
            rect = rects[i]
            if not ((abs(rect[0] - new_rects[-1][0]) < 10) and (abs(rect[1] - new_rects[-1][1]) < 10)):
                # if not checkDigit: rect[3] = 400
                new_rects.append(rect)
    return new_rects
def getTextAndCoorFromPaddle(img, lang='eng'):
    strp_chars = "|^#;$`'-_\/*‘ \n"
    Boxes = Pocr.ocr(img,rec=False)[0]
    image = img.copy()
    newBoxes, Cy_list, Cx_list = [], [], []
    for box in Boxes:
        x0, x1 = int(min(np.array(box)[:, 0])), int(max(np.array(box)[:, 0]))
        y0, y1 = int(min(np.array(box)[:, 1])), int(max(np.array(box)[:, 1]))
        cx, cy = int(x1/2+x0/2), int(y1/2+y0/2)
        image = cv2.rectangle(image, (x0, y0), (x1, y1), (0, 0, 255), 2)
        newBoxes.append([x0, y0, x1, y1])
        Cy_list.append(cy)
        Cx_list.append(cx)
    
    CyCpy = Cy_list.copy()
    CyUnique, _ = subset(np.sort(CyCpy), 15, 'medi')                

    Cy_list = [CyUnique[np.argmin(abs(np.array(CyUnique)-v))] for v in Cy_list]
    Cy_list, Cx_list, newBoxes = zip(*sorted(zip(Cy_list, Cx_list, newBoxes)))
    all_text = []
    for k, box in enumerate(newBoxes):
        pytesseract.pytesseract.tesseract_cmd = tesseract_Path
        text = pytesseract.image_to_string(img[box[1]:box[3], box[0]:box[2]], lang=lang, config='--psm 6')
        text = text.strip(strp_chars)
        all_text.append(text)
    return Cy_list, Cx_list, all_text
        