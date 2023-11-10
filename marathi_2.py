# Description:
# This script defines the Document and Page classes to streamline the flow of information through the script.

import numpy as np
import re, os
import pytesseract
from helper import split_pages, subset, getTextAndCoorFromPaddle
from dotenv import load_dotenv
load_dotenv()
# Global variables

class do_marathi_format2:
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
            if town_check and ('मूळ शहर' in tex or 'नगर ' in tex):
                temp_text = ''
                for k in range(1,5):
                    if Cx_list[i+k] < Cx_list[i]+50:
                        if len(temp_text)>0: 
                            final_json["main_town"] = temp_text.replace(':', '').strip()
                        town_check = False
                        break
                    else:
                        temp_text += text[i+k]
            if tehsil_check and ('तालुका' in tex):
                temp_text = ''
                for k in range(1,5):
                    if Cx_list[i+k] < Cx_list[i]+50:
                        if len(temp_text)>0: 
                            final_json["tehsil"] = temp_text.replace(':', '').strip()
                        tehsil_check = False
                        break
                    else:
                        temp_text += text[i+k]
            if district_check and ('जिल्हा' in tex):
                temp_text = ''
                for k in range(1,5):
                    if Cx_list[i+k] < Cx_list[i]+50:
                        if len(temp_text)>0: 
                            final_json["district"] = temp_text.replace(':', '').strip()
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
            if "भाग" in tex.lower():
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
                x1 = text.index('मूळ शहर')
                x2 = Cy_list.index(CyUnique[CyUnique.index(Cy_list[x1]) + 1])
                final_json["main_town"] = ' '.join(text[x1+1:x2]).split(':')[-1].strip()
                if final_json["main_town"] == ":": final_json["main_town"] = ""
            except: pass
            try:
                x1 = text.index('तालुका')
                x2 = Cy_list.index(CyUnique[CyUnique.index(Cy_list[x1]) + 1])
                final_json["tehsil"] = ' '.join(text[x1:x2]).split(':')[-1].strip()
                if final_json["tehsil"] == ":": final_json["tehsil"] = ""
            except: pass
            try:
                x1 = text.index('जिल्हा')
                x2 = Cy_list.index(CyUnique[CyUnique.index(Cy_list[x1]) + 1])
                final_json["district"] = ' '.join(text[x1+1:x2]).split(':')[-1].strip()   
            except: pass
            try:
                try: x1 = text.index('पिन कोड')
                except: x1 = text.index('कोड')
                x2 = Cy_list.index(CyUnique[CyUnique.index(Cy_list[x1]) + 1])
                final_json["pin_code"] = ' '.join(text[x1+1:x2]).split(':')[-1].strip()  
            except: pass
            try:
                x1 = [i for i, v in enumerate(text) if 'पत्ता' in v][0]
                # x1 = text.index('पत्ता')
                try: x2 = text.index('4.')
                except: x2 = text.index('4')
                addressRow = []
                for i in range(x1, x2):
                    if Cx_list[i] < 0.5*self.img.shape[1]/3: addressRow.append(text[i])
                final_json["address"] = ' '.join(addressRow).split(':')[-1].strip()
            except: pass                
                         
        return final_json   

    def process_page(self):
        tesseract_path = os.getenv("TESSERACT_PATH")
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
                    
                    pytesseract.pytesseract.tesseract_cmd = tesseract_path
                    ocr_text = pytesseract.image_to_string(cropped_image, lang='mar', config=custom_config)

                    # Remove unwanted characters from the OCR text
                    cleaned_text = self.remove_unwanted_characters(ocr_text)

                    # Append the cleaned text and page number to the list
                    page_results.append([cleaned_text, (int(x1/2+x0/2), int(y1/2+y0/2)), text])           

        
        return page_results
     
    def get_head_page_scanned(self,):

        return None


    def getFromScanned(self):
        Cy_list, Cx_list, text = getTextAndCoorFromPaddle(self.img, lang='mar')
        table, preYC = [], Cy_list[0]
        row = []
        for k, tex in enumerate(text):
            if abs(Cy_list[k]-preYC)<8: row.append([Cx_list[k], Cy_list[k], tex])
            else: 
                preYC = Cy_list[k]
                table.append(row)
                row = [[Cx_list[k], Cy_list[k], tex]]
        table.append(row)

        RelationX, SexX, HouseX, AgeX = None, None, None, None
        if len(table[1]) == 8:
            RelationX = int(table[1][3][0])
            SexX = int(table[1][5][0])
            HouseX = int(table[1][1][0])
            AgeX = int(table[1][6][0])
        else:
            for tab in table[1]:
                if 'नाते' in tab[2].lower(): RelationX = int(tab[0])
                elif 'लिंग' in tab[2].lower(): SexX = int(tab[0])
                elif 'घर' in tab[2].lower(): HouseX = int(tab[0])
                elif 'वय' in tab[2].lower(): AgeX = int(tab[0])        
        print("stop")
        mainTable = table[5:-1]
        output = []        
        for k, tab in enumerate(mainTable):
            if k > 0 and len(tab) == 2:
                output[-1]['name'] = output[-1]['name'] + ' ' + tab[0][2]
                output[-1]['father_name'] = output[-1]['father_name'] + ' ' + tab[1][2]
            elif k > 0 and len(tab) == 1: output[-1]['name'] = output[-1]['name'] + ' ' + tab[0][2]
            else:
                vote_name = ' '.join([v[2] for v in tab if HouseX+10<v[0]<RelationX-10])
                father_name = ' '.join([v[2] for v in tab if RelationX+10<v[0]<SexX-10])
                house_no = ' '.join([v[2] for v in tab if abs(v[0]-HouseX)<50])
                idC = [[v[0], v[1]] for v in tab if AgeX+20<v[0]]
                if len(idC)>0: 
                    idC = idC[0]
                    cropImg = self.img[idC[1]-20:idC[1]+20, max(idC[0]-150, 0):idC[0]+150]
                    txt = [v for v in pytesseract.image_to_string(cropImg, config='--psm 6').strip().split() if len(v)>3]
                    vote_id = txt[0] if len(txt) > 0 else ""  
                else: vote_id = 'N/A'                  
                output.append({'id':vote_id, 'name':vote_name, 'father_name':father_name, 'house_no':house_no, 'PageNumber':self.page_num})
                    
        return output    
        
    def getFromDigital(self):
        
        results = self.process_page()
        results = [[v[1][1], v[1][0], v[0], v[2]] for v in results] # cy, cx, ocr_text, digit_text
        results.sort()
        table, preYC = [], results[0][0]
        row = []
        for dcv in results:
            if abs(dcv[0]-preYC)<8: row.append([dcv[1], dcv[0], dcv[2], dcv[3]])
            else: 
                preYC = dcv[0]
                row.sort()
                table.append(row)
                row = [[dcv[1], dcv[0], dcv[2], dcv[3]]]
        row.sort()
        table.append(row)

        RelationX, SexX, HouseX, AgeX = None, None, None, None
        if len(table[1]) == 8:
            RelationX = int(table[1][3][0])
            SexX = int(table[1][5][0])
            HouseX = int(table[1][1][0])
            AgeX = int(table[1][6][0])
        else:
            for tab in table[1]:
                if 'नाते' in tab[2].lower(): RelationX = int(tab[0])
                elif 'लिंग' in tab[2].lower(): SexX = int(tab[0])
                elif 'घर' in tab[2].lower(): HouseX = int(tab[0])
                elif 'वय' in tab[2].lower(): AgeX = int(tab[0])
        mainTable = table[5:-1]
        output = []
        pdf_zoom = 3
        for k, tab in enumerate(mainTable):
            if k > 0 and len(tab) == 2:
                output[-1]['name'] = output[-1]['name'] + ' ' + tab[0][2]
                output[-1]['father_name'] = output[-1]['father_name'] + ' ' + tab[1][2]
            elif k > 0 and len(tab) == 1: output[-1]['name'] = output[-1]['name'] + ' ' + tab[0][2]
            else:
                house_noD = re.findall('\d+', ''.join([v[3] for v in tab if abs(v[0]-HouseX)<11]))
                if len(house_noD)>0: house_no = 'त-' + house_noD[0]
                else: house_no = 'त-'
                vote_name = ' '.join([v[2] for v in tab if HouseX+10<v[0]<RelationX-10])
                father_name = ' '.join([v[2] for v in tab if RelationX+10<v[0]<SexX-10])
                idC = [[v[0], v[1]] for v in tab if AgeX+16<v[0]]
                if len(idC)>0: 
                    idC = idC[0]
                    cropImg = self.img[idC[1]*pdf_zoom-20:idC[1]*pdf_zoom+20, max(idC[0]*pdf_zoom-150, 0):idC[0]*pdf_zoom+150]
                    txt = [v for v in pytesseract.image_to_string(cropImg, config='--psm 6').strip().split() if len(v)>3]
                    vote_id = txt[0] if len(txt) > 0 else ""  
                else: vote_id = 'N/A'                  
                output.append({'id':vote_id, 'name':vote_name, 'father_name':father_name, 'house_no':house_no, 'PageNumber':self.page_num})
                    
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
            if checkDigit:
                return self.getFromDigital()
            else:
                return self.getFromScanned()

    def parse_doc(self, socketio, username):
        '''
        In a document, main process is done for all pages 
        '''
        # Split and convert pages to images
        socketio.emit('process', {'data': f"Spliting PDF into images...", 'username': username})
        pages = split_pages(self.full_path)
        # self.indexFromFile()
        if pages == "01": err = "PDF file is damaged"
        else: self.pages, self.digit_doc = pages
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
                    socketio.emit('process', {'data': f"Processing {str(self.page_num)} of {len(self.digit_doc)}", 'username': username})  
                
            except Exception as e:
                print(f"    Page {str(idx+1)} of {self.full_path} ran into warning(some errors) in while parsing.")
        print(f"    Completed parsing {self.full_path} with no errors, ...........OK")
        result_1['DETAILS'] = result_2
        return result_1
