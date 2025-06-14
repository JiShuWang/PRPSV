import csv
import pickle

DataField = ["filepath", "weather", "date", "cameraid", "time", "parkingspaceid", "Ground Truth", "Prediction"]


def Split():  # Step 1: Processing the string from original object classification result dataset
    data = []
    datapath = "Data_Redid/"
    datafile = "ViT.csv"
    with open(datapath + datafile, "r+", newline='') as csvfile:  # 1. read data
        data = list(csv.reader(csvfile))[1:]
        # print(Data[0])

    for i in range(len(data)):  # 2. processing
        filepath = data[i][0]
        split = []  # the index of /
        divide = []  # the index of _
        end = ""  # the index of .
        for s in range(len(filepath)):
            if filepath[s] == "/":
                split.append(s)
            elif filepath[s] == "_":
                divide.append(s)
            elif filepath[s] == ".":
                end = s
        # print(split)
        # print(divide)
        weather = filepath[split[1] + 1:split[2]]
        date = filepath[split[2] + 1:split[3]]
        cameraid = filepath[split[3] + 1:split[4]]
        time = filepath[divide[1] + 1:divide[2]]
        parkingspaceid = filepath[divide[3] + 1:end]
        # print(weather, date, cameraid, time, parkingspaceid)
        data[i] = [filepath, weather, date, cameraid, str(time), parkingspaceid, data[i][1], data[i][2]]

    with open(datapath + "Split_" + datafile, 'w', newline='') as csvfile:  # 3. write data
        writer = csv.writer(csvfile)
        writer.writerow(DataField)
        for row in data:
            writer.writerow(row)
        csvfile.close()
        print("Write Finished.")


def LoadData():
    data = []
    with open("Data_Redid/vit.pkl", 'rb') as file:
        data = pickle.load(file)
        file.close()
    with open("Data_Redid/ViT.csv", "w", newline="") as file:
        for content in data:
            filepath = content["img_path"]
            filepath = filepath.replace("/car", "")
            groundtruth = content["gt_label"][0].item()
            prediction = content["pred_label"][0].item()
            csvwriter = csv.writer(file)
            csvwriter.writerow([filepath, groundtruth, prediction])


def PSVUpdate(gamma):  # Step 2: Finishing the PSV update from the processed dataset, gamma is γ in this paper
    data = []
    datapath = "Data_Redid/"
    datafile = "Split_ViT.csv"

    with open(datapath + datafile, "r+", newline='') as csvfile:  # 1. read data
        data = list(csv.reader(csvfile))[:]
    data.sort(key=lambda x: (x[2], x[5], x[4]))

    parkingspace = {}
    for content in data:  # 2. create the dict for every parkingspace
        if content[-3] not in parkingspace:
            parkingspace.setdefault(content[-3],
                                    [0, 0])  # parkingspaceid, the number of total status, the number of correct status

    V_V, V_O, O_O, O_V = 0, 0, 0, 0

    statuscount = {
        1: [0, 0],
        2: [0, 0],
        3: [0, 0],
        4: [0, 0]
    }
    i = 0
    while i < len(data) - 1:
        parkingspace[data[i][-3]][
            0] += 1  # the number of total status, the number of correct status, for this parkingspace
        status = False  # judge the parking space whether is monitored by 2 cameras at least
        n = 1  # the parking space were monitored by n cameras
        vacant, occupied = 0, 0  # the number of vacant status, and the number of occpied status for the parking space at this period
        if data[i][-1] == '0':  # the monitored status by first camera
            vacant = 1
        else:
            occupied = 1
        for j in range(i + 1, len(data)):
            if data[j][2] == data[i][2] and data[j][-3] == data[i][-3] and data[j][-2] == data[i][-2] and float(
                    data[j][4]) - float(
                data[i][
                    4]) < 0.05:  # The date, the parkingspaceid, and the true status are all same, and the time difference is less than 5 minutes
                status = True  # the parking space were monitored by 2 cameras at least
                n += 1
                if data[j][-1] == '0':  # the predictive status is vacant
                    vacant += 1
                else:  # the predictive status is occupied
                    occupied += 1
            else:
                if not status:  # n = 1
                    if data[i][-2] == "0":
                        if data[i][-1] == "0":
                            parkingspace[data[i][-3]][1] += 1
                            statuscount[1][1] += 1
                            V_V += 1
                        else:
                            V_O += 1
                    elif data[i][-2] in ["1", "2"]:
                        if data[i][-1] in ["1", "2"]:
                            parkingspace[data[i][-3]][1] += 1
                            statuscount[1][1] += 1
                            O_O += 1
                        else:
                            O_V += 1
                elif status and (vacant == 0 or occupied == 0):
                    if vacant != 0 and data[i][-2] == '0':
                        parkingspace[data[i][-3]][1] += 1
                        statuscount[n][1] += 1
                        V_V += 1
                    elif occupied != 0 and (data[i][-2] in ["1", "2"]):
                        parkingspace[data[i][-3]][1] += 1
                        statuscount[n][1] += 1
                        O_O += 1
                elif status and vacant >= 1 and occupied >= 1:
                    if vacant >= occupied * gamma:
                        if data[i][-2] == '0':  # the correct status and the predictive status are all vacant
                            parkingspace[data[i][-3]][1] += 1
                            statuscount[n][1] += 1
                            V_V += 1
                        else:
                            O_V += 1
                    else:
                        if data[i][-2] in ["1", "2"]:  # the correct status and the predictive status are all occupied
                            parkingspace[data[i][-3]][1] += 1
                            statuscount[n][1] += 1
                            O_O += 1
                        else:
                            V_O += 1

                statuscount[n][0] += 1
                i = j
                break

    totalstatus, correctstatus = 0, 0  # calculate the experiment results

    for key in parkingspace:
        totalstatus += parkingspace[key][0]
        correctstatus += parkingspace[key][1]

    print("γ=" + str(gamma) + ". The accuracy of PSV Update: " + str(format(correctstatus / totalstatus, ".4f")))
    print("The accuracy of PSV Update 1: " + str(format(statuscount[1][1] / statuscount[1][0], ".4f")))
    print("The accuracy of PSV Update 2: " + str(format(statuscount[2][1] / statuscount[2][0], ".4f")))
    print("The accuracy of PSV Update 3: " + str(format(statuscount[3][1] / statuscount[3][0], ".4f")))
    print("V_V", V_V, "O_O", O_O, "V_O", V_O, "O_V", O_V)  # Confusion Matrix
    # print("The accuracy of PSV Update 4: " + str(format(statuscount[4][1] / statuscount[4][0], ".4f")))


if __name__ == '__main__':
    LoadData()
    Split()
    for gamma in range(0, 3):
        PSVUpdate(gamma)
