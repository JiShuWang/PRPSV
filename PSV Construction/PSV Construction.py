import copy
import json
import cv2

Images_Oringinal = {}
Annotations_Oringinal = {}
Annotations_Detection = {}
Annotations_Constructed = {}
Annotations_Oringinal_iou = [[] for i in range(500)]
Annotations_Detection_iou = [[] for i in range(500)]
Annotations_Flitered = [[] for i in range(500)]
ScoreThreshold = 0.6
psviou, psvcount, deiou, decount = 0, 0, 0, 0


def CalculateIoU(box1, box2):
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    left_top = (max(x1, x2), max(y1, y2))
    right_bottom = (min(x1 + w1, x2 + w2), min(y1 + h1, y2 + h2))
    intersection_area = max(0, right_bottom[0] - left_top[0]) * max(0, right_bottom[1] - left_top[1])
    union_area = w1 * h1 + w2 * h2 - intersection_area
    iou = intersection_area / union_area
    return iou


def LoadImages(model):
    global Images_Oringinal, Annotations_Oringinal, Annotations_Detection, Annotations_Constructed, Annotations_Detection_iou, Annotations_Oringinal_iou
    with open("Data/test_annotations.json", "r") as jsonfile:
        data = json.load(jsonfile)
        Images_Oringinal = data["images"]
        Annotations_Oringinal = data["annotations"]
        jsonfile.close()
    with open("Data/" + model + ".json", "r") as jsonfile:
        data = json.load(jsonfile)
        Annotations_Detection = data
        jsonfile.close()

    index = 0
    for content in Annotations_Oringinal:
        element = content["bbox"]
        element.append(index)
        Annotations_Oringinal_iou[content["image_id"]].append(element)
        index += 1

    index = 0
    for content in Annotations_Detection:
        if content["score"] >= ScoreThreshold:
            element = content["bbox"][:]
            element.append(index)
            Annotations_Detection_iou[content["image_id"]].append(element)
            index += 1

    index = 0
    Annotations_Constructed = copy.deepcopy(Annotations_Detection)
    for content in Annotations_Constructed:
        if content["score"] >= ScoreThreshold:
            element = content["bbox"]
            element.append(content["score"])
            element.append(index)
            element.append(content["category_id"])
            Annotations_Flitered[content["image_id"]].append(element)
            index += 1
    for index in range(len(Annotations_Flitered)):
        Annotations_Flitered[index].sort(key=lambda x: (x[0], x[1]))


def ShowAnnotationImages(imageid):
    global Images_Oringinal, Annotations_Oringinal, Annotations_Detection, Annotations_Constructed, ScoreThreshold
    path = "Data/Dataset_Standard/" + str(imageid) + ".jpg"
    image_oringinal = cv2.imread(path)
    for annotations in Annotations_Oringinal:
        if annotations["image_id"] == imageid:
            left_top = [annotations["bbox"][0], annotations["bbox"][1]]
            right_bottom = [annotations["bbox"][0] + annotations["bbox"][2],
                            annotations["bbox"][1] + annotations["bbox"][3]]
            category = annotations["category_id"]
            if category == 1:  # occupied
                cv2.rectangle(image_oringinal, left_top, right_bottom, (0, 0, 255), 2)  # red
            else:  # vacant
                cv2.rectangle(image_oringinal, left_top, right_bottom, (255, 0, 0), 2)  # blue
    image_detection = cv2.imread(path)
    for annotations in Annotations_Detection:
        if annotations["image_id"] == imageid:
            left_top = [int(annotations["bbox"][0]), int(annotations["bbox"][1])]
            right_bottom = [int(annotations["bbox"][0]) + int(annotations["bbox"][2]),
                            int(annotations["bbox"][1]) + int(annotations["bbox"][3])]
            category = annotations["category_id"]
            if annotations["score"] >= ScoreThreshold:
                if category == 1:  # occupied
                    cv2.rectangle(image_detection, left_top, right_bottom, (0, 0, 255), 2)  # red
                else:  # vacant
                    cv2.rectangle(image_detection, left_top, right_bottom, (255, 0, 0), 2)  # blue
    image_constructed = cv2.imread(path)
    for index, annotations in enumerate(Annotations_Flitered[imageid]):
        left_top = [int(annotations[0]), int(annotations[1])]
        right_bottom = [int(annotations[0]) + int(annotations[2]), int(annotations[1]) + int(annotations[3])]
        category = annotations[-1]
        if category == 1:  # occupied
            cv2.rectangle(image_constructed, left_top, right_bottom, (0, 0, 255), 2)  # red
        else:  # vacant
            cv2.rectangle(image_constructed, left_top, right_bottom, (255, 0, 0), 2)  # blue
        # cv2.putText(image_constructed, str(index), left_top, cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 1)
    # cv2.imshow("Oringinal" + str(imageid) + ".jpg", cv2.resize(image_oringinal, None, fx=1, fy=1))
    # cv2.imshow("Detection" + str(imageid) + ".jpg", cv2.resize(image_detection, None, fx=1, fy=1))
    # cv2.imshow("Constructed" + str(imageid) + ".jpg", cv2.resize(image_constructed, None, fx=1, fy=1))
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()


def CalculateEffect(imageid):
    global Images_Oringinal, Annotations_Constructed, psviou, psvcount, deiou, decount

    Annotations_Oringinal_iou[imageid].sort(key=lambda x: (x[1], x[0]))
    Annotations_Detection_iou[imageid].sort(key=lambda x: (x[1], x[0]))
    Annotations_Flitered[imageid].sort(key=lambda x: (x[1], x[0]))

    countdeiou = 0
    countde = 0
    for content in Annotations_Oringinal_iou[imageid]:
        maxiou = 0
        for recontent in Annotations_Detection_iou[imageid]:
            nowiou = CalculateIoU(content[:4], recontent[:4])
            if nowiou > maxiou:
                maxiou = nowiou
        if maxiou > 0.5:
            countde += 1
            countdeiou += maxiou
    countdeiou /= countde
    deiou += countdeiou
    decount += 1

    countpsviou = 0
    countpsv = 0
    for content in Annotations_Oringinal_iou[imageid]:
        maxiou = 0
        for recontent in Annotations_Flitered[imageid]:
            nowiou = CalculateIoU(content[:4], recontent[:4])
            if nowiou > maxiou:
                maxiou = nowiou
        if maxiou > 0.5:
            countpsv += 1
            countpsviou += maxiou
    countpsviou /= countpsv
    psviou += countpsviou
    psvcount += 1

    print(imageid, countdeiou, countpsviou)


def PSVConstruct(model):
    global Images_Oringinal, Annotations_Constructed
    for content in Images_Oringinal:
        imageid = content["id"]
        UnifyPosition(imageid, 0.9)
        UnifySpacing(imageid, 20, 0)
        ShowAnnotationImages(imageid)
        CalculateEffect(imageid)
    print("-------------------------")
    print(deiou / decount, psviou / psvcount)


def UnifyPosition(imageid, alpha):  # 1. Position Alignment
    global Annotations_Flitered
    for index, content in enumerate(Annotations_Flitered[imageid]):
        current = content
        for reindex, recontent in enumerate(Annotations_Flitered[imageid][:index]):  
            if index != reindex:
                compare = recontent
                overlapx, overlapy = 0, 0
                if compare[0] <= current[0] <= compare[0] + compare[2] or current[0] <= compare[0] <= current[0] + \
                        current[2]:  # The X-axis is existing overlap
                    overlapx = [current[0], current[0] + current[2], compare[0], compare[0] + compare[2]]
                    overlapx.sort()  
                    overlapx = overlapx[2] - overlapx[1] # The overlap part
                if compare[1] <= current[1] <= compare[1] + compare[3] or current[1] <= compare[1] <= current[1] + \
                        current[3]:  # The Y-axis is existing overlap
                    overlapy = [current[1], current[1] + current[3], compare[1], compare[1] + compare[3]]
                    overlapy.sort()
                    overlapy = overlapy[2] - overlapy[1] # The overlap part
                maxbox = max(current[2], compare[2])
                if overlapx >= alpha * maxbox:  # The percent of overlap is high enough, and i and j can be thinked that is a same column
                    yspacing = [current[1], current[1] + current[3], compare[1], compare[1] + compare[3]]
                    yspacing.sort()
                    yspacing = yspacing[2] - yspacing[1]
                    if yspacing <= 50:
                        Annotations_Flitered[imageid][index][0] = recontent[0]
                        Annotations_Flitered[imageid][index][2] = recontent[2]
                maxbox = max(current[3], compare[3])
                if overlapy >= alpha * maxbox:  # The percent of overlap is high enough, and i and j can be thinked that is a same row
                    xspacing = [current[0], current[0] + current[2], compare[0], compare[0] + compare[2]]
                    xspacing.sort()
                    xspacing = xspacing[2] - xspacing[1]
                    if xspacing <= 50:
                        Annotations_Flitered[imageid][index][1] = recontent[1]
                        Annotations_Flitered[imageid][index][3] = recontent[3]
        Annotations_Flitered[imageid].sort(key=lambda x: (x[1], x[0])) # Ensure the loop order


def UnifySpacing(imageid, beta, epsilon):  # 2. Overlap Removal (Spacing Uniform)
    global Annotations_Flitered
    Xspacing, Yspacing = epsilon, epsilon
    for index, content in enumerate(Annotations_Flitered[imageid]):
        current = content
        Xdistance, Ydistance = beta, beta
        for reindex, recontent in enumerate(Annotations_Flitered[imageid][:index]):  
            Xoindex, Yoindex, Xsindex, Ysindex = None, None, None, None
            compare = recontent
            overlapx, overlapy, spacingx, spacingy = 0, 0, 0, 0
            if index != reindex and current[1] == compare[1]:  
                overlapx = (compare[0] + compare[2]) - current[0]
                spacingx = current[0] - (compare[0] + compare[2])
                if compare[0] < current[0]:  
                    if 0 < spacingx <= Xdistance:  
                        Xdistance = overlapx
                        Xsindex = reindex
                    if overlapx > 0:  
                        Xoindex = reindex
            if index != reindex and current[0] == compare[0]:  
                overlapy = (compare[1] + compare[3]) - current[1]
                spacingy = current[1] - (compare[1] + compare[3])
                if compare[1] < current[1]:  
                    if 0 < spacingy <= Ydistance:
                        Ydistance = spacingy
                        Ysindex = reindex
                    if overlapy > 0:
                        Yoindex = reindex
            if Xsindex is not None and compare[0] + compare[2] < current[0]:  # X-axis spacing
                Annotations_Flitered[imageid][Xsindex][2] += spacingx / 2
                Annotations_Flitered[imageid][index][0] -= spacingx / 2
            if Xoindex is not None and compare[0] + compare[2] > current[0]:  # X-axis overlap
                Annotations_Flitered[imageid][Xoindex][2] -= overlapx / 2
                Annotations_Flitered[imageid][index][0] += overlapx / 2
            if Ysindex is not None and current[1] > compare[1] + compare[3]:  # Y-axis spacing
                Annotations_Flitered[imageid][Ysindex][3] += spacingy / 2
                Annotations_Flitered[imageid][index][1] -= spacingy / 2
            if Yoindex is not None and current[1] < compare[1] + compare[3]:  # Y-axis overlap
                Annotations_Flitered[imageid][Yoindex][3] -= overlapy / 2
                Annotations_Flitered[imageid][index][1] += overlapy / 2
        UnifyPosition(imageid, 0.8)


if __name__ == '__main__':
    LoadImages("yolo6.bbox")
    PSVConstruct("yolo6.bbox")
