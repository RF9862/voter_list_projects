# Description:
# This script defines the Document and Page classes to streamline the flow of information through the script.

import numpy as np
import re, os
import pytesseract
from helper import split_pages, subset, getting_textdata, getRectangle, getTextAndCoorFromPaddle

# dotenv.load_dotenv()
# Global variables

class do_marathi:
    def __init__(self, fullPath):
        self.full_path = fullPath
      
    def check_scan_or_digit(self):
        '''
        Check if pdf is digital or scanned.
        '''
        d = self.digit_page.get_text_words()
        if len(d) > 10:# and digit_flag:
            return True
        else:
            return False
    def remove_unwanted_characters(self, text):
        # Define the unwanted characters or patterns to remove
        unwanted_chars = ['\n', '\x0c', '<', '>']

        # Remove unwanted characters or patterns
        for char in unwanted_chars:
            text = text.replace(char, '')

        # Remove leading and trailing whitespaces
        text = text.strip()

        return text
    def get_index(self, text, word, limit):
        try: return text.index(word)
        except:
            for i, tex in enumerate(text):
                if word in tex and i > limit:
                    return i
        return None
    def get_head_page_digit(self):
        final_json={}
        final_json["assembly_number"] = 'N/A'
        final_json["assembly_name"] = 'N/A'
        final_json["part_number"] = 'N/A'
        final_json["year"] = 'N/A'
        final_json["main_town"] = 'N/A'
        final_json["tehsil"] = 'N/A'
        final_json["district"] = 'N/A'
        final_json["pin_code"] = 'N/A'
        final_json["address"] = 'N/A'
        final_json["page_number"] = self.page_num

        results = self.process_page()
        pastY, pastX = results[0][1][1], results[0][1][0]
        Cy_list, Cx_list, text = [pastY],[pastX],[results[0][0]]
        for i in range(1, len(results)):
            if not(abs(results[i][1][1]-pastY)<5 and abs(results[i][1][0]-pastX)<5):
                Cy_list.append(results[i][1][1])
                Cx_list.append(results[i][1][0])
                text.append(results[i][0])
                pastY, pastX = results[i][1][1], results[i][1][0]

        CyCpy = Cy_list.copy()
        CyUnique, _ = subset(np.sort(CyCpy), 5, 'medi')

        Cy_list = [CyUnique[np.argmin(abs(np.array(CyUnique)-v))] for v in Cy_list]
        Cy_list, Cx_list, text = zip(*sorted(zip(Cy_list, Cx_list, text)))

        try: final_json["year"] = re.findall('\d+', text[Cy_list.index(CyUnique[1]) - 1 ])[0]
        except: pass
        partTop = -1
        for i, tex in enumerate(text):
            if "भाग" in tex:
                partTop = i
                break
        if partTop > -1:
            
            for k in range(10):
                    t = text[partTop - (k+1)]
                    if len(re.findall('\d+', t)) > 0: 
                        t = t.split()
                        if len(t) > 1: final_json["assembly_number"], final_json["assembly_name"] = t[0], t[1]
                        else:
                            final_json["assembly_number"] = t[0]
                            final_json["assembly_name"] = text[partTop - (k)]
                    else: continue
                    break
            
            final_json["part_number"] = text[Cy_list.index(CyUnique[CyUnique.index(Cy_list[partTop]) + 2]) - 1]
            try:
                x1 = self.get_index(text, 'मूळ शहर', 1)
                x2 = Cy_list.index(CyUnique[CyUnique.index(Cy_list[x1]) + 1])
                final_json["main_town"] = ' '.join(text[x1+1:x2]).split(':')[-1].strip()
                if final_json["main_town"] == ":": final_json["main_town"] = ""
            except: pass
            try:
                x1 = self.get_index(text, 'तालुका', 1)
                x2 = Cy_list.index(CyUnique[CyUnique.index(Cy_list[x1]) + 1])
                final_json["tehsil"] = ' '.join(text[x1:x2]).split(':')[-1].strip()
                if final_json["tehsil"] == ":": final_json["tehsil"] = ""
            except: pass
            try:
                x1 = self.get_index(text, 'जिल्हा', 1)
                x2 = Cy_list.index(CyUnique[CyUnique.index(Cy_list[x1]) + 1])
                final_json["district"] = ' '.join(text[x1+1:x2]).split(':')[-1].strip()   
            except: pass
            try:
                x1 = self.get_index(text, 'पिन कोड', 1)
                if x1 is None: x1 = self.get_index(text, 'कोड', 1)
                x2 = Cy_list.index(CyUnique[CyUnique.index(Cy_list[x1]) + 1])
                final_json["pin_code"] = ' '.join(text[x1+1:x2]).split(':')[-1].strip()  
            except: pass
            try:
                x1 = [i for i, v in enumerate(text) if 'पत्ता' in v][0]
                # x1 = text.index('पत्ता')
                x2 = self.get_index(text, '4.', x1)
                addressRow = []
                for i in range(x1, x2):
                    if Cx_list[i] < 0.5*self.img.shape[1]/3: addressRow.append(text[i])
                final_json["address"] = ' '.join(addressRow).split(':')[-1].strip()
            except: pass
                         
        return final_json    
    def get_head_page_scanned(self,):
        '''
        This function gets all digital texts and their coordinates.
        '''

        final_json={}
        final_json["assembly_number"] = 'N/A'
        final_json["assembly_name"] = 'N/A'
        final_json["part_number"] = 'N/A'
        final_json["year"] = 'N/A'
        final_json["main_town"] = 'N/A'
        final_json["tehsil"] = 'N/A'
        final_json["district"] = 'N/A'
        final_json["pin_code"] = 'N/A'
        final_json["address"] = 'N/A'
        final_json["page_number"] = self.page_num        
        text, _, _, _, _, accu, Cx_list, Cy_list = getting_textdata(self.img, '--psm 6', 1, 0, lang='mar')

        H, W, _ = self.img.shape
        CyCpy = Cy_list.copy()
        CyUnique, _ = subset(np.sort(CyCpy), 15, 'medi')

        Cy_list = [CyUnique[np.argmin(abs(np.array(CyUnique)-v))] for v in Cy_list]
        Cy_list, Cx_list, text = zip(*sorted(zip(Cy_list, Cx_list, text)))
        
        strp_chars = "|^#;$`'-_=*\/‘¢[®°]"
        text = [v.strip(strp_chars).strip() for v in text]
        # text = [v for v in text if v != '']
    
        try: 
            secondRowInd = Cy_list.index(CyUnique[1])
            temp = []
            for i in range(secondRowInd): temp += re.findall('\d+', text[i])
            for tem in temp:
                if len(tem) == 4: 
                    final_json["year"] = tem
                    break
        except: pass
        partTop = -1
        for i, tex in enumerate(text):
            if "भाग" in tex:
                partTop = i
                break
        if partTop > -1:
            
            for k in range(10):
                    t = text[partTop - (k+1)]
                    if len(re.findall('\d+', t)) > 0: 
                        t = t.split()
                        if len(t) > 1: final_json["assembly_number"], final_json["assembly_name"] = t[0], t[1]
                        else:
                            final_json["assembly_number"] = t[0]
                            final_json["assembly_name"] = text[partTop - (k)]
                    else: continue
                    break
            
            partNum = text[Cy_list.index(CyUnique[CyUnique.index(Cy_list[partTop]) + 2]) - 1]
            try:
                int(partNum)
                final_json["part_number"] = partNum
            except: final_json["part_number"] = "1"
            
            try:
                try: x1 = self.get_index(text, 'मूळ शहर', 1)
                except: x1 = self.get_index(text, 'शहर', 1)
                x2 = Cy_list.index(CyUnique[CyUnique.index(Cy_list[x1]) + 1])
                final_json["main_town"] = ' '.join(text[x1+1:x2]).split(':')[-1].strip()
                if final_json["main_town"] == ":": final_json["main_town"] = ""
            except: pass
            try:
                x1 = self.get_index(text, 'तालुका', 1)
                x2 = Cy_list.index(CyUnique[CyUnique.index(Cy_list[x1]) + 1])
                final_json["tehsil"] = ' '.join(text[x1:x2]).split(':')[-1].strip()
                if final_json["tehsil"] == ":": final_json["tehsil"] = ""
            except: pass
            try:
                x1 = self.get_index(text, 'जिल्हा', 1)
                x2 = Cy_list.index(CyUnique[CyUnique.index(Cy_list[x1]) + 1])
                final_json["district"] = ' '.join(text[x1+1:x2]).split(':')[-1].strip()   
            except: pass
            try:
                x1 = self.get_index(text, 'पिन कोड', 1)
                if x1 is None: x1 = self.get_index(text, 'कोड', 1)
                x2 = Cy_list.index(CyUnique[CyUnique.index(Cy_list[x1]) + 1])
                final_json["pin_code"] = ' '.join(text[x1+1:x2]).split(':')[-1].strip()  
            except: pass
            try:
                x1 = [i for i, v in enumerate(text) if 'पत्ता' in v][0]
                # x1 = text.index('पत्ता')
                x2 = self.get_index(text, '4.', x1)
                addressRow = []
                for i in range(x1, x2):
                    if Cx_list[i] < 0.5*self.img.shape[1]/3: addressRow.append(text[i])
                final_json["address"] = ' '.join(addressRow).split(':')[-1].strip()
            except: pass

        return final_json
    def get_head_page_scanned_paddle(self,):
        '''
        This function gets all digital texts and their coordinates.
        '''

        final_json={}
        final_json["assembly_number"] = 'N/A'
        final_json["assembly_name"] = 'N/A'
        final_json["part_number"] = 'N/A'
        final_json["year"] = 'N/A'
        final_json["main_town"] = 'N/A'
        final_json["tehsil"] = 'N/A'
        final_json["district"] = 'N/A'
        final_json["pin_code"] = 'N/A'
        final_json["address"] = 'N/A'
        final_json["page_number"] = self.page_num        
        Cy_list, Cx_list, text = getTextAndCoorFromPaddle(self.img, lang='mar')
        Cy_list, Cx_list, text = list(Cy_list), list(Cx_list), list(text)
        CyCpy = Cy_list.copy()
        CyUnique, _ = subset(np.sort(CyCpy), 15, 'medi')

        Cy_list = [CyUnique[np.argmin(abs(np.array(CyUnique)-v))] for v in Cy_list]
        Cy_list, Cx_list, text = zip(*sorted(zip(Cy_list, Cx_list, text)))  
        H, W, _ = self.img.shape
        TextByLine = []
        past_v, line = Cy_list[0], ''
        for i in range(len(Cy_list)):
            if past_v == Cy_list[i]:
                line += ' ' + text[i]
            else:
                TextByLine.append(line)
                line = ' ' + text[i]
                past_v = Cy_list[i]
        if len(line)>0: TextByLine.append(line)

        past_ind = -1
        try: 
            for i, v in enumerate(text):
                temp = re.findall('\d+', v)
                for tem in temp: 
                    if len(tem)==4: 
                        final_json["year"], past_ind = tem, i
                        break
                if past_ind != -1: break
                
        except: pass
        # get assemply name an number
        try:
            temp_text = TextByLine[past_ind+1]
            temp = re.findall('\d+', temp_text)
            final_json["assembly_number"] = temp[0]
            temp = temp_text[temp_text.index(temp[0]):].split()
            for i in range(1, len(temp)):
                if len(temp[i]) > 2:
                    final_json["assembly_name"] = temp[i]
                    break
        except: pass
        # get part no
        tesseract_Path = os.getenv("TESSERACT_PATH")
        for i, tex in enumerate(text):
            if "भाग" in tex:
                partImg = self.img[Cy_list[i]+30:Cy_list[i]+80, Cx_list[i]-50:Cx_list[i]+50]
                pytesseract.pytesseract.tesseract_cmd = tesseract_Path
                temp_text = pytesseract.image_to_string(partImg, lang='eng', config='--psm 6')   
                final_json["part_number"] = re.findall('\d+', temp_text)[0]
                break
        town_check, tehsil_check, district_check, pin_check, address_check = True, True, True, True, True
        for i, tex in enumerate(text):
            if town_check and ('मूळ शहर' in tex or 'नगर' in tex):
                temp_text = ''
                for k in range(1,5):
                    if Cx_list[i+k] < Cx_list[i]+50:
                        if len(temp_text)>0: 
                            final_json["main_town"] = temp_text
                        town_check = False
                        break
                    else:
                        temp_text += text[i+k]
            if tehsil_check and ('तालुका' in tex):
                temp_text = ''
                for k in range(1,5):
                    if Cx_list[i+k] < Cx_list[i]+50:
                        if len(temp_text)>0: 
                            final_json["tehsil"] = temp_text
                        tehsil_check = False
                        break
                    else:
                        temp_text += text[i+k]
            if district_check and ('जिल्हा' in tex):
                temp_text = ''
                for k in range(1,5):
                    if Cx_list[i+k] < Cx_list[i]+50:
                        if len(temp_text)>0: 
                            final_json["district"] = temp_text
                        district_check = False
                        break
                    else:
                        temp_text += text[i+k]  
            if pin_check and ('कोड' in tex):
                temp_text = ''
                codeImg = self.img[Cy_list[i]-25:Cy_list[i]+25, Cx_list[i]+50:Cx_list[i]+500]
                pytesseract.pytesseract.tesseract_cmd = tesseract_Path
                temp_text = pytesseract.image_to_string(codeImg, lang='eng', config='--psm 6')  
                pin_check = False 
                try: final_json["pin_code"] = re.findall('\d+', temp_text)[0]                                                               
                except: pass
            if address_check and 'पत्ता' in tex:
                addressRow = []
                for k in range(1,8):
                    if Cx_list[i+k] < 360/595 * W: addressRow.append(text[i+k])  
                    final_json['address'] = ' '.join(addressRow[0:2])
                address_check = False             

        return final_json
    def process_page(self):
        tesseract_Path = os.getenv("TESSERACT_PATH")
        page_results = []
        custom_config =  "--oem 3 --psm 6"
        blocks = self.digit_page.get_text("dict")["blocks"]
        pdf_zoom = 3
        for block in blocks:
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"]
                    x0, y0, x1, y1 = span["bbox"]

                    # Crop the image based on the coordinates
                    cropped_image = self.img[int(y0)*pdf_zoom:int(y1)*pdf_zoom, int(x0)*pdf_zoom:int(x1)*pdf_zoom]
                    # Perform OCR on the cropped image
                    pytesseract.pytesseract.tesseract_cmd = tesseract_Path
                    
                    ocr_text = pytesseract.image_to_string(cropped_image, lang='mar', config=custom_config)

                    # Remove unwanted characters from the OCR text
                    cleaned_text = self.remove_unwanted_characters(ocr_text)

                    # Append the cleaned text and page number to the list
                    page_results.append([cleaned_text, (int(x1/2+x0/2), int(y1/2+y0/2)), text])           

        
        return page_results
            
    def getFromImg(self, rects):
        custom_config =  "--oem 3 --psm 6"
        results = []
        for rect in rects:
            y,x,H,W = rect
            cropped_image = self.img[y:y+H, x:x+W]
            text, _, _, w, h, accu, xc, yc= getting_textdata(cropped_image, custom_config, 1, 0, lang='mar', ths=0) 
            CyCpy = yc
            CyUnique, _ = subset(np.sort(CyCpy), 15, 'medi')
            yc = [CyUnique[np.argmin(abs(np.array(CyUnique)-v))] for v in yc]
            yc, xc, text = zip(*sorted(zip(yc, xc, text)))
            new = []
            try: ref_y = yc[0]
            except: pass
            row = []
            ka = 0.9
            for i, tex in enumerate(text):
                if xc[i] > ka*W: continue
                if yc[i] == ref_y: row.append([tex, xc[i], yc[i]])
                else:
                    ref_y = yc[i]
                    new.append(row)
                    row = [[tex, xc[i], yc[i]]]
                    ka = 0.75
            new.append(row)
            # new = [v for v in new if len(v) > 1]

            #########
            strp_chars = "|^#;$`-_=*\/‘¢[®°]:"
            voterIdNo, fatherName, voterName, T_name = '', '', '', ''
            for i, row in enumerate(new):
                for ele in row:
                    if 'वडीलांचे'in ele[0] or 'बडीलांचे' in ele[0] or 'पतीचे' in ele[0] or 'आईचे' in ele[0] or 'वडलांचे' in ele[0]:
                        f_ind = i
                        fatherName = ' '.join([v[0] for v in row if v[1]>0.3*W]).strip()
                        fatherName = fatherName.strip(strp_chars).strip()                            
                        break

            for i, row in enumerate(new):
                for ele in row:
                    if 'मतदाराचे' in ele[0] or 'नाव' in ele[0]:
                        ka = 0.15 if 'नाव' in ele[0] else 0.3
                        n_ind = i
                        voterName = ' '.join([v[0] for v in row if v[1]>ka*W]).strip()
                        voterName = voterName.strip(strp_chars).strip()    
                        break  
                if voterName != '': break
            try:
                id_ind = n_ind-1
                if f_ind - n_ind == 2:
                    voterName += ' '.join([v[0] for v in new[n_ind+1] if v[1]>0.3*W]).strip()
                    house_ind = n_ind + 3
                else:
                    house_ind = n_ind + 2
            except:
                id_ind = 0
                house_ind = 3

            IdRow = new[id_ind]
            for ele in IdRow:
                if len(ele[0]) > 3: Id_xc, Id_yc = ele[1], ele[2]
            try: 
                IDImg = cropped_image[max(Id_yc-14, 0):Id_yc+15, max(Id_xc-80, 0):Id_xc+100]
                txt = [v for v in pytesseract.image_to_string(IDImg, config='--psm 6').strip().split() if len(v)>3]
                voterIdNo = txt[0] if len(txt) > 0 else "" 
            except: pass

            # House No
            for i, row in enumerate(new):
                for ele in row:
                    if 'घर' in ele[0]:
                        if len(row) > 3: T_name = ' '.join([v[0] for v in row[1:]])
                        else:
                            houseImg = cropped_image[max(ele[2]-14, 0):ele[2]+14, 10:int(0.5*W)]
                            T_name = pytesseract.image_to_string(houseImg, lang='eng+mar', config='--psm 6').strip()
                            T_name = T_name.replace('घर', '')
                        T_name = T_name.replace('क्रमाक', '').replace('क्रमांक', '').split(':')[-1].strip()
                        break
            if T_name == '':
                houseRow = new[house_ind]
                houseImg = cropped_image[max(houseRow[0][2]-14, 0):houseRow[0][2]+14, int(0.3*W):int(0.5*W)]
                T_name = pytesseract.image_to_string(houseImg, config='--psm 6').strip()

            results.append({'id':voterIdNo, 'name':voterName, 'father_name':fatherName, 'house_no':T_name, 'PageNumber':self.page_num})
        return results

    def old_getFromDigital(self):
        
        results = self.process_page()
        
        text_list, coord_list, photo_coord_list, output = [], [], [], []

        for text, coordinates, _ in results:
            text_list.append(text)
            coord_list.append(coordinates)            
            if 'मतदाराचे' in text:#'मतदाराचे'#'मतदनरनच'#मतदतरतच
                photo_coord_list.append(coordinates)  
        pdf_zoom = 3
        for cen in photo_coord_list:
            element = {}
            v = [coord_list[i] for i, item in enumerate(coord_list) if 20<abs(item[0]-cen[0])<100 and \
                 10<cen[1]-item[1]<20 and text_list[i].strip() != '']
            if len(v) > 0: 
                coor = v[0]
                cropImg = self.img[coor[1]*pdf_zoom-20:coor[1]*pdf_zoom+20, max(coor[0]*pdf_zoom-150, 0):coor[0]*pdf_zoom+150]
                txt = [v for v in pytesseract.image_to_string(cropImg, config='--psm 6').strip().split() if len(v)>3]
                element['id'] = txt[0] if len(txt) > 0 else ""
            else: element['id'] = 'N/A'

            v = [text_list[i] for i, item in enumerate(coord_list) if abs(item[1]-cen[1]) < 10 and \
                         24<item[0]-cen[0]<100 and text_list[i].strip() != '']
            if len(v) > 0: element['name'] = v[0]
            else: element['name'] = 'N/A'

            v = [text_list[i] for i, item in enumerate(coord_list) if 24<item[0]-cen[0]<100 and \
                 10<item[1]-cen[1]<27 and text_list[i].strip() != '']
            if len(v) > 0: element['father_name'] = v[0]
            else: element['father_name'] = 'N/A'

            v = [text_list[i] for i, item in enumerate(coord_list) if 24<abs(item[0]-cen[0])<100 and \
                 27<item[1]-cen[1]<40 and text_list[i].strip() != '']
            if len(v) > 0: 
                houseD = re.findall('\d+', v[0])
                try: element['house_no'] = 'त-'+houseD[0]
                except: element['house_no'] = 'त-'
            else: element['house_no'] = 'N/A'
            element['PageNumber'] = self.page_num

            output.append(element)

        return output    
    def parse_page(self):
        '''
        main process.
        '''
        checkDigit = self.check_scan_or_digit()
        if self.page_num == 1:
            if checkDigit:
                return self.get_head_page_digit()
            else:
                return self.get_head_page_scanned_paddle()
        else:
            rects = getRectangle(self.img) # get every elements region
            return self.getFromImg(rects)

    def parse_doc(self):
        '''
        In a document, main process is done for all pages 
        '''
        # Split and convert pages to images
        pages = split_pages(self.full_path)
        # self.indexFromFile()
        if pages == "01":
            err = "PDF file is damaged"
        else:
            self.pages, self.digit_doc = pages
        # entity = ['No and Name of Reservation Status', 'Part No', 'Year', 'Main Town', 'Tehsil', 'District', 'Pin code', 'Address of Polling Station']
        # entity = ['ASSEMBLY CONSTITUENCY NUMBER', 'ASSEMBLY CONSTITUENCY NAME', 'Part No', 'Year', 'Main Town', 'Tehsil', 'District', 'Pin code', 'Address of Polling Station']
        result_1 = {}
        result_2 = []
        # for enti in entity:
        #     result_1[enti.upper()] = 'N/A'        
        for idx, img in enumerate(self.pages):
            try:
                # if idx < 6:
                    if idx == 1: continue
                    print(f"Reading page {idx + 1} out of {len(self.pages)}")
                    self.digit_page = self.digit_doc[idx]
                    self.page_num = idx + 1
                    self.img = img
                    self.digit_cen_value = []
                    self.digit_value = []                      
                    result = self.parse_page()
                    
                    if idx == 0: result_1 = result
                    else: result_2 += result
                
            except Exception as e:
                print(f"    Page {str(idx+1)} of {self.full_path} ran into warning(some errors) in while parsing.")
        print(f"    Completed parsing {self.full_path} with no errors, ...........OK")
        result_1['DETAILS'] = result_2
        return result_1