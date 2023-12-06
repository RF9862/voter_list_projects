
import os
import platform
import sys, gc
from pathlib import Path
import torch
import time

from yolo_usage.models.common import DetectMultiBackend
from yolo_usage.utils.dataloaders import IMG_FORMATS, VID_FORMATS, LoadImages, LoadScreenshots, LoadStreams
from yolo_usage.utils.general import (LOGGER, Profile, check_file, check_img_size, check_imshow, check_requirements, colorstr, cv2,
                           increment_path, non_max_suppression, print_args, scale_boxes, strip_optimizer, xyxy2xywh)
from yolo_usage.utils.plots import Annotator, colors, save_one_box
from yolo_usage.utils.torch_utils import select_device, smart_inference_mode
import cv2
import numpy as np
from yolo_usage.utils.augmentations import letterbox
from memory_profiler import profile
@profile
# @smart_inference_mode()
def getTotalValue(
        weights='best.pt',  # model path or triton URL
        source=None,  # file/dir/URL/glob/screen/0(webcam)
        data='data/coco128.yaml',  # dataset.yaml path
        imgsz=(800, 800),  # inference size (height, width)
        conf_thres=0.25,  # confidence threshold
        iou_thres=0.45,  # NMS IOU threshold
        max_det=1000,  # maximum detections per image
        device='',  # cuda device, i.e. 0 or 0,1,2,3 or cpu
        view_img=False,  # show results
        save_txt=False,  # save results to *.txt
        save_conf=False,  # save confidences in --save-txt labels
        save_crop=False,  # save cropped prediction boxes
        nosave=True,  # do not save images/videos
        classes=None,  # filter by class: --class 0, or --class 0 2 3
        agnostic_nms=False,  # class-agnostic NMS
        augment=False,  # augmented inference
        visualize=False,  # visualize features
        update=False,  # update all models
        project='outputs/detect',  # save results to project/name
        name='exp',  # save results to project/name
        exist_ok=False,  # existing project/name ok, do not increment
        line_thickness=3,  # bounding box thickness (pixels)
        hide_labels=False,  # hide labels
        hide_conf=False,  # hide confidences
        half=False,  # use FP16 half-precision inference
        dnn=False,  # use OpenCV DNN for ONNX inference
        vid_stride=1,  # video frame-rate stride
        main_self = None
):
    # Load model
    device = select_device(device)
    model = DetectMultiBackend(weights, device=device, dnn=dnn, data=data, fp16=half)

    stride, names, pt = model.stride, model.names, model.pt
    imgsz = check_img_size(imgsz, s=stride)  # check image size

    # Dataloader
    bs = 1  # batch_size
    im0s = source.copy()
    im = letterbox(im0s, imgsz, stride, pt)[0]  # padded resize
    im = im.transpose((2, 0, 1))[::-1]  # HWC to CHW, BGR to RGB
    im = np.ascontiguousarray(im)  # contiguous

    # Run inference
    model.warmup(imgsz=(1 if pt or model.triton else bs, 3, *imgsz))  # warmup
    seen, windows, dt = 0, [], (Profile(), Profile(), Profile())
    result = []
    # K.clear_session()
    box, con, labels = [], [], []
    with dt[0]:
        im = torch.from_numpy(im).to(model.device)
        im = im.half() if model.fp16 else im.float()  # uint8 to fp16/32
        im /= 255  # 0 - 255 to 0.0 - 1.0
        if len(im.shape) == 3:
            im = im[None]  # expand for batch dim

    # Inference
    with dt[1]:
        # visualize = increment_path(save_dir / Path(path).stem, mkdir=False) if visualize else False
        pred = model(im, augment=augment, visualize=False)

    # NMS
    with dt[2]:
        pred = non_max_suppression(pred, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det)

    # Second-stage classifier (optional)
    # pred = utils.general.apply_classifier(pred, classifier_model, im, im0s)
    
    # Process predictions
    for i, det in enumerate(pred):  # per image
        seen += 1
        # save_path = str(save_dir / p.name)  # im.jpg
        if len(det):
            # Rescale boxes from img_size to im0 size
            det[:, :4] = scale_boxes(im.shape[2:], det[:, :4], im0s.shape).round()

            # Print results
            for c in det[:, 5].unique():
                n = (det[:, 5] == c).sum()  # detections per class

            # Write results
            for *xyxy, conf, cls in reversed(det):
                box.append([int(v) for v in xyxy])
                con.append(float(conf))
                labels.append(str(int(cls)))
    del model, im0s, im
    gc.collect()
    if update:
        strip_optimizer(weights[0])  # update model (to fix SourceChangeWarning)

    return box

def makeSquare(not_square):
    # This function takes an image and makes the dimenions square
    # It adds black pixels as the padding where needed
    
    BLACK = [0,0,0]
    img_dim = not_square.shape
    height = img_dim[0]
    width = img_dim[1]
    #print("Height = ", height, "Width = ", width)
    if (height == width):
        square = not_square
        return square
    else:
        doublesize = cv2.resize(not_square,(2*width, 2*height), interpolation = cv2.INTER_CUBIC)
        height = height * 2
        width = width * 2
        #print("New Height = ", height, "New Width = ", width)
        if (height > width):
            pad = (height - width)//2
            #print("Padding = ", pad)
            doublesize_square = cv2.copyMakeBorder(doublesize,0,0,pad,\
                                                   pad,cv2.BORDER_CONSTANT,value=BLACK)
        else:
            pad = (width - height)//2
            #print("Padding = ", pad)
            doublesize_square = cv2.copyMakeBorder(doublesize,pad,pad,0,0,\
                                                   cv2.BORDER_CONSTANT,value=BLACK)
    doublesize_square_dim = doublesize_square.shape
    #print("Sq Height = ", doublesize_square_dim[0], "Sq Width = ", doublesize_square_dim[1])
    return doublesize_square

def resize_to_pixel(dimensions, image):
    # This function then re-sizes an image to the specificied dimenions
    
    buffer_pix = 4
    dimensions  = dimensions - buffer_pix
    squared = image
    r = float(dimensions) / squared.shape[1]
    dim = (dimensions, int(squared.shape[0] * r))
    resized = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
    img_dim2 = resized.shape
    height_r = img_dim2[0]
    width_r = img_dim2[1]
    BLACK = [0,0,0]
    if (height_r > width_r):
        resized = cv2.copyMakeBorder(resized,0,0,0,1,cv2.BORDER_CONSTANT,value=BLACK)
    if (height_r < width_r):
        resized = cv2.copyMakeBorder(resized,1,0,0,0,cv2.BORDER_CONSTANT,value=BLACK)
    p = 2
    ReSizedImg = cv2.copyMakeBorder(resized,p,p,p,p,cv2.BORDER_CONSTANT,value=BLACK)
    img_dim = ReSizedImg.shape
    height = img_dim[0]
    width = img_dim[1]
    #print("Padded Height = ", height, "Width = ", width)
    return ReSizedImg
# @profile
def Recognize_Digit(image):

    gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    # img_h, img_w = gray.shape
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    try:
        roi = blurred#[yy:yy + hh, xx:xx + ww]
        ret, roi = cv2.threshold(roi, 127, 255,cv2.THRESH_BINARY_INV)
        roi = makeSquare(roi)
        roi = resize_to_pixel(28, roi)
        roi = roi / 255.0       
        roi = roi.reshape(1,28,28,1)             
        
        ## Get Prediction
        predict_x = digit_model.predict(roi, 1, verbose = 0)[0]
        final_pred=np.argmax(predict_x)
        prob = max(predict_x)
    except:
        final_pred = None    
    # del model
    return final_pred, prob
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

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


