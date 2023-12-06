# Description:
# This script defines the Document and Page classes to streamline the flow of information through the script.

import os
import numpy as np
import cv2
import re, json, fitz
import pytesseract
from helper import split_pages, subset, getting_textdata, approximate, getRectangle
# Global variables

class do_english:
    def __init__(self, fullPath):
        self.full_path = fullPath

    def indexFromFile(self,):
        self.refIndex = [None]*len(self.pages)
        jsonPath = os.path.join(self.doc_dir, self.doc_name+'.pdf.json')
        try:
            with open(jsonPath) as f:
                jsonInfo = json.load(f)[self.doc_name+'.pdf']
            for i, v in enumerate(jsonInfo.values()):
                try: self.refIndex[i]= (np.array(v)[:, 0]).tolist()
                except: pass
        except: pass

    def check_scan_or_digit(self):
        '''
        Check if pdf is digital or scanned.
        '''
        d = self.digit_page.get_text_words()
        if len(d) > 10:# and digit_flag:
            return True
        else:
            return False
      
    def text_inrange(self, ori_text, yxwh):
        y, x, h, w = yxwh[0], yxwh[1], yxwh[2], yxwh[3]
        text_list = [item for item in ori_text if item[0] > y-3 and item[0] < y+h]
        # text = [item[2] for item in text_list if item[1] > x-3 and item[1] < x+w]
        text_list = [item for item in text_list if item[1] > x-3 and item[1] < x+w]
        
        new_texts_1, new_texts_2 = [], []
        try: ref_y = text_list[0][0]
        except: pass
        row1, row2 = [], []
        for i, tex in enumerate(text_list):
            if tex[0] == ref_y: 
                new_tex = [tex[0], tex[1] - x, tex[2]]
                if new_tex[1] < 110:
                    row1.append(new_tex)
                else: row2.append(new_tex)
            else:
                ref_y = tex[0]
                if len(row1) > 0: 
                    row1 = [row1[0][0], ' '.join([v[2] for v in row1]), ':']
                    new_texts_1.append(row1)
                if len(row2) > 0: 
                    row2 = [row2[0][0], ' '.join([v[2] for v in row2])]
                    new_texts_2.append(row2)
                row1, row2 = [], []
                new_tex = [tex[0], tex[1] - x, tex[2]]
                if new_tex[1] < 110: row1.append(new_tex)
                else: row2.append(new_tex)

        if len(row1) > 0: 
            row1 = [row1[0][0], ' '.join([v[2] for v in row1]), ':']
            new_texts_1.append(row1)
        if len(row2) > 0: 
            row2 = [row2[0][0], ' '.join([v[2] for v in row2])]
            new_texts_2.append(row2)

        #######################################################
        y_1 = np.array([v[0] for v in new_texts_1])
        for ro2 in new_texts_2:
            ind = np.argmin(abs(y_1 - ro2[0]))
            new_texts_1[ind].append(ro2[1])
        new_texts = [' '.join(v[1:]) for v in new_texts_1]
            
        results = []  
        voterIdNo, fatherName, voterName, T_name, RowInd = '', '', '', '', None
        for i, row in enumerate(new_texts):
            if 'father' in row.lower() or 'husband' in row.lower():
                RowInd = i
                fatherName = row.split(':')[-1].strip()
                break
        if RowInd is None:
            for i, row in enumerate(new_texts):
                if 'name' in row.lower():
                    RowInd = i
                    voterName = row.split('Name')[-1].strip()
                    break  
            if RowInd is not None:
                IDRow = new_texts[RowInd-1]
                voterIdNo = IDRow.split(':')[-1].strip()
        else:
            TRow = new_texts[RowInd+1]
            T_name = TRow.split(':')[-1].strip()
            nameRow = new_texts[RowInd-1]
            voterName = nameRow.split(':')[-1].strip()
            if RowInd-2 >= 0: 
                IDRow = new_texts[RowInd-2]
                voterIdNo = IDRow.split(':')[-1].strip()
                
        return {'id':voterIdNo, 'name':voterName, 'father_name':fatherName, 'house_no':T_name, 'PageNumber':self.page_num}
        
    def get_head_page_digit(self):
        d = self.digit_page.get_text_words()
        topUnique = self.get_digit(d)
        top, left, h, w, text = self.digit_value
        H, W, _ = self.img.shape
        self.pageNumber1 = {}
        self.pageNumber1["assembly_number"] = 'N/A'
        self.pageNumber1["assembly_name"] = 'N/A'
        self.pageNumber1["part_number"] = 'N/A'
        self.pageNumber1["year"] = 'N/A'
        self.pageNumber1["main_town"] = 'N/A'
        self.pageNumber1["tehsil"] = 'N/A'
        self.pageNumber1["district"] = 'N/A'
        self.pageNumber1["pin_code"] = 'N/A'
        self.pageNumber1["address"] = 'N/A'
        self.pageNumber1["page_number"] = self.page_num
        
        self.pageNumber1["year"] = text[top.index(topUnique[1]) - 1 ]
        partTop = -1
        for i, tex in enumerate(text):
            if tex.lower() == "part":
                partTop = i
                break
        if partTop > -1:
            
            for k in range(10):
                try: 
                    self.pageNumber1["assembly_number"] = str(int(text[partTop - (k+2)]))
                    self.pageNumber1["assembly_name"] = text[partTop - (k+1)]
                    break
                except:
                    pass
            
            self.pageNumber1["part_number"] = text[top.index(topUnique[topUnique.index(top[partTop]) + 2]) - 1]
            try:
                x1 = text.index('Town')
                x2 = top.index(topUnique[topUnique.index(top[x1]) + 1])
                self.pageNumber1["main_town"] = ' '.join(text[x1:x2]).split(':')[-1].strip()
                if self.pageNumber1["main_town"] == ":": self.pageNumber1["main_town"] = ""
            except: pass
            try:
                x1 = text.index('Tehsil')
                x2 = top.index(topUnique[topUnique.index(top[x1]) + 1])
                self.pageNumber1["tehsil"] = ' '.join(text[x1:x2]).split(':')[-1].strip()
                if self.pageNumber1["tehsil"] == ":": self.pageNumber1["tehsil"] = ""
            except: pass
            try:
                x1 = text.index('District')
                x2 = top.index(topUnique[topUnique.index(top[x1]) + 1])
                self.pageNumber1["district"] = ' '.join(text[x1:x2]).split(':')[-1].strip()   
            except: pass
            try:
                try: x1 = text.index('Pincode')
                except: x1 = text.index('PIN')
                x2 = top.index(topUnique[topUnique.index(top[x1]) + 1])
                self.pageNumber1["pin_code"] = ' '.join(text[x1:x2]).split(':')[-1].strip()  
            except: pass
            try:
                x1 = text.index('Address')
                x2 = text.index('4.')
                addressRow = []
                for i in range(x1, x2):
                    if left[i] < 360/595 * W: addressRow.append(text[i])
                self.pageNumber1["address"] = ' '.join(addressRow).split(':')[-1].strip()
            except: pass
        return self.pageNumber1        
    def get_digit(self, d):
        '''
        This function gets all digital texts and their coordinates.
        '''
        digit_zoom = 1
        text, left, top, w, h, accu= [], [], [], [], [], []
        page_rot = self.digit_page.rotation
        d = np.array(d)
        text = d[:, 4].tolist()
        coor = d[:, 0:4]
        
        pdf_zoom = 3
        coor = np.apply_along_axis(np.genfromtxt, 1 ,coor)*pdf_zoom
        H, W, _ = self.img.shape

        if page_rot == 0:
            left, top, w, h = coor[:, 0], coor[:, 1], (coor[:,2]-coor[:,0]), (coor[:,3]-coor[:,1])
        elif page_rot == 90:
            left, top, w, h = (W-coor[:, 3]), coor[:, 0], (coor[:,3]-coor[:,1]), (coor[:,2]-coor[:,0])
        elif page_rot == 180:
            left, top, w, h = coor[:, 2], coor[:, 3], (coor[:,0]-coor[:,2]), (coor[:,1]-coor[:,3])
        elif page_rot == 270:left, top, w, h = coor[:,1], (H-coor[:, 2]), (coor[:,3]-coor[:,1]), (coor[:,2]-coor[:,0])
        left, top, w, h = left.astype(int), top.astype(int), w.astype(int), h.astype(int)
        left, top, w, h = left*digit_zoom, top*digit_zoom, w*digit_zoom, h*digit_zoom

        topCpy, leftCpy = top.copy(), left.copy()
        topCpy.sort()
        leftCpy.sort()
        
        topUnique, topUniqCnt = subset(np.sort(topCpy), 15, 'medi')
        # leftUnique, leftUniqCnt = subset(np.sort(leftCpy), 10, 'medi')
        top = [topUnique[np.argmin(abs(np.array(topUnique)-v))] for v in top]
        # left = [leftUnique[np.argmin(abs(np.array(leftUnique)-v))] for v in left]
        
        top, left, h, w, text = zip(*sorted(zip(top, left, h, w, text)))
        top, left, h, w, text = list(top), list(left), list(h), list(w), list(text)
        
        self.digit_value = [top, left, h, w, text]
        # self.get_digit_cen()
        return topUnique

    def get_head_page_scanned(self,):
        '''
        This function gets all digital texts and their coordinates.
        '''
        def GetParticularTexts(ref_yc):
            # get all texts which center is around ref_yc and xc > Tehsil_x1
            result = []
            for i, ycc in enumerate(yc):
                if abs(ycc - ref_yc) < 10 and xc[i] > Tehsil_x1: result.append([xc[i], text[i]])
            result.sort()
            result = [v[1] for v in result]
            return result  
        image = self.line_remove(self.img)
        text, left, top, w, h, accu, xc, yc = getting_textdata(image, '--psm 6', 1, 0)
        topCpy, leftCpy = top.copy(), left.copy()
        topCpy.sort()
        leftCpy.sort()
        H, W, _ = self.img.shape
        topUnique, topUniqCnt = subset(np.sort(topCpy), 15, 'medi')
        # leftUnique, leftUniqCnt = subset(np.sort(leftCpy), 10, 'medi')
        top = [topUnique[np.argmin(abs(np.array(topUnique)-v))] for v in top]
        # left = [leftUnique[np.argmin(abs(np.array(leftUnique)-v))] for v in left]
        
        top, left, h, w, text, yc, xc = zip(*sorted(zip(top, left, h, w, text, yc, xc)))
        top, left, h, w, text, yc, xc = list(top), list(left), list(h), list(w), list(text), list(yc), list(xc)
        strp_chars = "|^#;$`'-_=*\/‘¢[®°]"
        text = [v.strip(strp_chars).strip() for v in text]
        text = [v for v in text if v != '']
    
        self.pageNumber1 = {}
        self.pageNumber1["assembly_number"] = 'N/A'
        self.pageNumber1["assembly_name"] = 'N/A'
        self.pageNumber1["part_number"] = 'N/A'
        self.pageNumber1["year"] = 'N/A'
        self.pageNumber1["main_town"] = 'N/A'
        self.pageNumber1["tehsil"] = 'N/A'
        self.pageNumber1["district"] = 'N/A'
        self.pageNumber1["pin_code"] = 'N/A'
        self.pageNumber1["address"] = 'N/A'
        self.pageNumber1["page_number"] = self.page_num
        for i, tex in enumerate(text):
            if len(tex) == 4:
                try: 
                    int(tex)
                    self.pageNumber1["year"] = tex
                    break
                except: pass
        partTop = -1
        for i, tex in enumerate(text):
            if tex == "Part":
                partTop = i
                break                    
                
        if partTop > -1:
            self.pageNumber1["assembly_number"] = text[partTop - 2]
            self.pageNumber1["assembly_name"] = text[partTop - 1]
            self.pageNumber1["part_number"] = text[top.index(topUnique[topUnique.index(top[partTop]) + 2]) - 1]
            # Get x1 coordinate of "tehsil", y1 coordinate of "Town"
            try: Tehsil_x1 = left[text.index('Tehsil')] - 20
            except: Tehsil_x1 = self.img.shape[1]/2
            strp_chars = "|^#;$`'-_=*\/‘:¢ \n"
            try:
                ref_yc = yc[text.index('Town')]
                Rows = GetParticularTexts(ref_yc)
                self.pageNumber1["main_town"] = ' '.join(Rows).strip(strp_chars).split('Village')[-1].strip()
            except: pass
            try:
                ref_yc = yc[text.index('Tehsil')]
                Rows = GetParticularTexts(ref_yc)
                self.pageNumber1["tehsil"] = ' '.join(Rows).strip(strp_chars).split('Tehsil')[-1].strip()
            except: pass
            try:
                ref_yc = yc[text.index('District')]
                Rows = GetParticularTexts(ref_yc)
                self.pageNumber1["district"] = ' '.join(Rows).strip(strp_chars).split('District')[-1].strip()
            except: pass
            try:
                try: ref_yc = yc[text.index('Pincode')]
                except: ref_yc = yc[text.index('Pin')]
                Rows = GetParticularTexts(ref_yc)
                self.pageNumber1["pin_code"] = Rows[-1]
            except: pass
            try:
                x1 = text.index('Address')
                x2 = [i for i, v in enumerate(text) if v == '4.'][-1]
                addressRow = []
                for i in range(x1, x2):
                    if left[i] < 360/595 * W: addressRow.append(text[i])
                self.pageNumber1["address"] = ' '.join(addressRow).split('Stations')[-1].strip()
            except: pass
        return self.pageNumber1
    def get_digit_cen(self):
        '''
        This function is used digital pdf.
        Here gets location of y and x, text in every boxes.
        '''
        medi_val = [40, 20]
        top, left, h, w, text = self.digit_value
        y_c, x_c = (np.array(top)+np.array(h)/2).tolist(), (np.array(left)+np.array(w)/2).tolist()
        x_c, y_c, text_c = zip(*sorted(zip(x_c, y_c, text)))
        x_c = approximate(x_c, int(medi_val[0]*0.6))
        y_c, x_c, text_c = zip(*sorted(zip(y_c, x_c, text_c)))
        y_c = approximate(y_c, int(medi_val[1]*0.6))
        y_c, x_c, text_c = zip(*sorted(zip(y_c, x_c, text_c)))
        self.digit_cen_value = list(zip(y_c, x_c, text_c))  
        text_list = [item for item in self.digit_cen_value if item[0] > 0]
        self.digit_cen_value = [item for item in text_list if item[1] > 0]

    def line_remove(self, image):
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

    def getFromScanned(self, rects):
        results = []
        RemovedImg = self.line_remove(self.img)
        text_, left, top, w_, h_, accu, xc_, yc_ = getting_textdata(RemovedImg, '--psm 6', 1, 0)
        strp_chars = "|^#;$`-_=*\/‘¢[®°]:"
        text_temp = [v.strip(strp_chars).strip() for v in text_]     
        removeIndex = [i for i, v in enumerate(text_temp) if v == "Photo" or v == "is" or v == "Available"]
        text, xc, yc, ww, hh = [], [], [], [], []
        for i, v in enumerate(text_):
            if not i in removeIndex:
                text.append(v)
                xc.append(xc_[i])
                yc.append(yc_[i])
                ww.append(w_[i])
                hh.append(h_[i])
        for rect in rects:
            voterIdNo, voterName, TName, fatherName = "", "", "", ""
            y, x, h, w = rect
            text_list = [[yc[i], xc[i], item, hh[i], ww[i]] for i, item in enumerate(text) if yc[i] > y-3 and yc[i] < y+h]
            # text = [item[2] for item in text_list if item[1] > x-3 and item[1] < x+w]
            text_list = [item for i, item in enumerate(text_list) if item[1] > x-3 and item[1] < x+w]
            
            new_text, new_xc, new_yc, new_ww, new_hh = [], [], [], [], []
            for v in text_list:
                new_text.append(v[2])
                new_xc.append(v[1])
                new_yc.append(v[0])
                new_ww.append(v[4])
                new_hh.append(v[3])

            ycCpy = new_yc.copy()
            ycUnique, ycUniqCnt = subset(np.sort(ycCpy), 7, 'medi')
            new_yc = [ycUnique[np.argmin(abs(np.array(ycUnique)-v))] for v in new_yc]
            new_yc, new_xc, new_text = zip(*sorted(zip(new_yc, new_xc, new_text)))
            new_yc, new_xc, new_text = list(new_yc), list(new_xc), list(new_text)                
            
            new_texts = []
            try: ref_y = new_yc[0]
            except: pass
            row = []
            for i, tex in enumerate(new_text):
                if new_yc[i] == ref_y: row.append(tex)
                else:
                    ref_y = new_yc[i]
                    new_texts.append(row)
                    row = [tex]
            new_texts.append(row)
            voterIdNo, fatherName, voterName, T_name, RowInd = '', '', '', '', None
            for i, row in enumerate(new_texts):
                for ele in row:
                    if 'father' in ele.lower() or 'husband' in ele.lower():
                        RowInd = i
                        fatherName = ' '.join(row).split('Name')[-1].strip()
                        fatherName = fatherName.strip(strp_chars).strip()                            
                        break
            if RowInd is None:
                for i, row in enumerate(new_texts):
                    for ele in row:
                        if 'name' in ele.lower():
                            RowInd = i
                            voterName = ' '.join(row).split('Name')[-1].strip()
                            voterName = voterName.strip(strp_chars).strip()    
                            break  
                if RowInd is not None:
                    IDRow = new_texts[RowInd-1]
                    for ele in IDRow:
                        if len(ele) > 4: 
                            voterIdNo = ele
                            voterIdNo = voterIdNo.strip(strp_chars).strip()  
            else:
                nameRow = new_texts[RowInd-1]
                voterName = ' '.join(nameRow).split('Name')[-1].strip()
                voterName = voterName.strip(strp_chars).strip()    
                IDRow = new_texts[RowInd-2]
                for ele in IDRow:
                    if len(ele) > 4: 
                        voterIdNo = ele                    
                        voterIdNo = voterIdNo.strip(strp_chars).strip()  
            
            # print("stop")    
            try:
                try: house_index = new_text.index('Number')
                except: house_index = new_text.index('House')
                house_H, house_W, house_xc, house_yc = new_hh[house_index], new_ww[house_index], new_xc[house_index], new_yc[house_index]
                image = RemovedImg[y:y+h, x:x+w]
                T_nameImg = image[int(house_yc-y-house_H/2 -3):int(house_yc-y+house_H/2 +3), int(0.3*image.shape[1]):int(0.5*image.shape[1])]
                TName = pytesseract.image_to_string(T_nameImg, config='--psm 6').replace(':', '').strip()
                strp_chars = "|^#;$`-_=*\/‘¢[®°]:"
                TName = TName.strip(strp_chars).strip()
            except:
                pass
            results.append({'id':voterIdNo, 'name':voterName, 'father_name':fatherName, 'house_no':TName, 'PageNumber':self.page_num})
        return results
    def getFromDigital(self, rects):
        results = []
        ori_texts = []
        d = self.digit_page.get_text_words()
        _ = self.get_digit(d)
        self.get_digit_cen()
        for dcv in self.digit_cen_value:
            if not (dcv[2].lower() == 'photo' or dcv[2].lower() == 'not' or dcv[2].lower() == 'available'):
                ori_texts.append(dcv)     
        for rect in rects:
            results.append(self.text_inrange(ori_texts, rect))    
        return results    
    def parse_page(self):
        '''
        main process.
        '''
        checkDigit = self.check_scan_or_digit()
        if self.page_num == 1:
            if checkDigit:
                return self.get_head_page_digit()
            else:
                return self.get_head_page_scanned()
        else:
            rects = getRectangle(self.img, checkDigit) # get every elements region
            if checkDigit:
                return self.getFromDigital(rects)
            else:
                return self.getFromScanned(rects)

    def parse_doc(self, socketio, username):
        '''
        In a document, main process is done for all pages 
        '''
        # Split and convert pages to images
        socketio.emit('process', {'data': f"Spliting PDF into images...", 'username': username})
        result_1 = {}
        result_2 = []        
        self.digit_doc = fitz.open(self.full_path)
        past_page_ind, page_batch = 0, 50
        for i in range(len(self.digit_doc)//page_batch+1):
            next_page_ind = min(page_batch*(i+1), len(self.digit_doc))
            pages = split_pages(self.digit_doc, past_page_ind, next_page_ind)
            past_page_ind = next_page_ind
            self.pages = pages
        # entity = ['No and Name of Reservation Status', 'Part No', 'Year', 'Main Town', 'Tehsil', 'District', 'Pin code', 'Address of Polling Station']
        # entity = ['ASSEMBLY CONSTITUENCY NUMBER', 'ASSEMBLY CONSTITUENCY NAME', 'Part No', 'Year', 'Main Town', 'Tehsil', 'District', 'Pin code', 'Address of Polling Station']

        # for enti in entity:
        #     result_1[enti.upper()] = 'N/A'        
            for idx, img in enumerate(self.pages):
                try:
                    # if idx < 6:
                        if idx == 1 and i == 0: continue
                        self.digit_page = self.digit_doc[idx+i*page_batch]
                        self.page_num = idx + 1 + i*page_batch
                        print(f"Reading page {self.page_num} out of {len(self.digit_doc)}")
                        self.img = img
                        self.digit_cen_value = []
                        self.digit_value = []                      
                        result = self.parse_page()
                        if idx == 0 and i == 0: result_1 = result
                        else: result_2 += result
                        socketio.emit('process', {'data': f"Processed {str(self.page_num)} of {len(self.digit_doc)}", 'username': username})                
                except Exception as e:
                    print(f"    Page {str(idx+1)} of {self.full_path} ran into warning(some errors) in while parsing.")
        print(f"    Completed parsing {self.full_path} with no errors, ...........OK")
        result_1['DETAILS'] = result_2
        return result_1
