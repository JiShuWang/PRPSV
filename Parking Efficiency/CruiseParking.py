import csv
import random

import numpy
import pandas as pd
from geopy.distance import geodesic

ParkingLot = {}
ParkingSpace = {}  # 用以标记车辆到达停车位时，该停车位是否能停车
AvgSearchingTime = 3  # Seconds
SearchTime = {}
SearchingDistance = {}
StepDistance = {}
AvgSpeed = 0.75  # The speed, km/min


def NowTime(hour, minute):
    return (2 - len(str(hour))) * '0' + str(hour) + (2 - len(str(minute))) * '0' + str(minute)


# 1. Generate variables
def Generatevariables(dataset):
    global ParkingLot, SearchTime, StepDistance
    ParkingLot, SearchTime, StepDistance = {}, {}, {}
    with open("Data/ParkingLot_" + str(dataset) + "_Processed.csv", "r", encoding="utf-8") as csvreader:
        parkinglot = list(csv.reader(csvreader))[1:]
        csvreader.close()
    with open("Data/ParkingSpace_" + str(dataset) + "_Processed.csv", "r", encoding="utf-8") as csvreader:
        parkingspace = list(csv.reader(csvreader))[1:]
        csvreader.close()

    for pl in parkinglot:
        parkinglotid, capacity, pllongitude, pllatitude = pl[0], int(pl[1]), float(pl[2]), float(pl[3])
        ParkingLot.setdefault(parkinglotid,
                              {"information": [capacity, pllongitude, pllatitude]})  # key:parking lot id, value:{}
        for hour in range(8, 24):
            for minute in range(0, 60):
                nowtime = NowTime(hour, minute)
                SearchTime.setdefault(nowtime, 0)
                SearchingDistance.setdefault(nowtime, 0)
                StepDistance.setdefault(nowtime, 0)
                ParkingLot[parkinglotid].setdefault(nowtime, {"occupied": 0})  # key: nowtime, value:{}
                for ps in parkingspace:
                    plid, psid, pslongitude, pslatitude = ps[0], ps[1], float(ps[2]), float(ps[3])
                    if plid == parkinglotid:
                        ParkingLot[parkinglotid][nowtime].setdefault(psid, [pslongitude, pslatitude,
                                                                            False])  # key: parking space id, value:False (judge the parking space is whether be occupied at this time)
    print("1. Preparing has Finished!")


# 2.1 Simulate parking: Non-PSV Cruise Parking
def NonPSVCruiseParking(dataset, duration, strategy):
    global ParkingLot, SearchTime, SearchDistance, StepDistance

    reader = pd.read_csv("Data/ParkingRequest_" + str(dataset) + ".csv", iterator=True)

    while True:
        parkingrequest = []
        try:
            chunk = reader.get_chunk(5000)
            parkingrequest = numpy.array(chunk).tolist()
            i = 0
            while i < len(parkingrequest):
                hour, minute = int(parkingrequest[i][0]), int(parkingrequest[i][1])
                nowtime = NowTime(hour, minute)
                epl = eval(parkingrequest[i][-1])  # i.e., expected parking lots
                eplid = str(parkingrequest[i][2])
                cpo = ParkingLot[eplid][nowtime]["occupied"]  # i.e., current parking occupied
                capacity = ParkingLot[eplid]["information"][0]
                print(parkingrequest[i])
                if cpo < capacity:  # can be parking
                    nowdistance, targetdistance, nowpsid, targetpsid = 99999, 99999, '0', '0'  # 停车位和当前位置的距离，停车位和目的地的距离
                    for ps in ParkingLot[eplid][nowtime]:
                        if ps != "occupied":
                            pslongitude, pslatitude, status = ParkingLot[eplid][nowtime][ps][0], ParkingLot[eplid][nowtime][ps][
                                1], ParkingLot[eplid][nowtime][ps][2]
                            nowlongitude, nowlatitude = float(parkingrequest[i][3]), float(parkingrequest[i][4])
                            targetlongitude, targetlatitude = float(parkingrequest[i][5]), float(parkingrequest[i][6])
                            if not status and strategy == 1:  # 采用以当前位置就近停车策略
                                if geodesic(
                                        (nowlatitude, nowlongitude), (pslatitude, pslongitude)).km < nowdistance:
                                    nowdistance = geodesic(
                                        (nowlatitude, nowlongitude), (pslatitude, pslongitude)).km
                                    nowpsid = ps
                            elif not status and strategy == 2:  # 采用以目的地位置就近停车策略
                                if geodesic(
                                        (targetlatitude, targetlongitude), (pslatitude, pslongitude)).km < targetdistance:
                                    targetdistance = geodesic(
                                        (targetlatitude, targetlongitude), (pslatitude, pslongitude)).km
                                    targetpsid = ps
                    if strategy == 1:
                        SearchTime[nowtime] += nowdistance / AvgSpeed
                    elif strategy == 2:
                        SearchTime[nowtime] += targetdistance / AvgSpeed
                    SearchTime[nowtime] += (capacity * AvgSearchingTime / 60) / (1 + capacity - cpo)
                    for parkingminute in range(int(duration * 60)):  # 停车持续时段内该停车位的状态均被占用
                        nowtime = NowTime(hour, minute)
                        ParkingLot[eplid][nowtime]["occupied"] += 1
                        ParkingLot[eplid][nowtime][ps][2] = True
                        minute += 1
                        if minute == 60:
                            hour += 1
                            minute = 0
                        if hour == 24:
                            break
                    parkingrequest.pop(i)
                else:
                    if len(epl) == 1:  # 只有一个可选停车场，只能继续在当前停车场等待
                        minute += 1
                        if minute >= 60:
                            hour += 1
                            minute = 0
                        if hour == 24:
                            break
                        parkingrequest[i][0], parkingrequest[i][1] = (2 - len(str(hour))) * '0' + str(hour), (
                                2 - len(str(minute))) * '0' + str(minute)
                        SearchTime[nowtime] += 1
                    else:  # 还有可用停车场，则前往继续搜寻
                        plindex = epl.index(eplid)
                        if plindex < len(epl) - 1:
                            parkingrequest[i][2] = epl[plindex + 1]
                        else:
                            parkingrequest[i][2] = epl[0]
                        nowlongitude, nowlatitude, targetlongitude, targetlatitude = float(parkingrequest[i][3]), float(
                            parkingrequest[i][4]), float(
                            ParkingLot[eplid]["information"][1]), \
                                                                                     float(ParkingLot[eplid]["information"][2])
                        arrivetime = geodesic(
                            (nowlatitude, nowlongitude), (targetlatitude, targetlongitude)).km / AvgSpeed
                        SearchTime[nowtime] += arrivetime
                        if arrivetime < 1:
                            minute += 1
                        else:
                            minute += int(arrivetime)
                        if minute >= 60:
                            hour += 1
                            minute %= 60
                        if hour == 24:
                            break
                        parkingrequest[i][0], parkingrequest[i][1] = (2 - len(str(hour))) * '0' + str(hour), (
                                2 - len(str(minute))) * '0' + str(minute)
                        parkingrequest[i][3] = targetlongitude
                        parkingrequest[i][4] = targetlatitude
                    parkingrequest.sort(key=lambda x: (int(x[0]), int(x[1])))

            with open("Result/CummulativeSearchingTime/" + str(dataset) + "/NonPSVCP_" + str(duration) + "hour_" + str(
                    strategy) + "_strategy_SearchTime.csv", 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                time = 0
                for key in SearchTime:
                    time += SearchTime[key]
                    print(time)
                    writer.writerow([key, time])
                csvfile.close()
            print("2. Non-PSV Cruise Parking_" + str(duration) + "hour has Finished!")
        except StopIteration:
            print("Iteration is finished.")
            break


# 2.2 Simulate parking: PSV Cruise Parking
def PSVCruiseParking(dataset, duration, strategy):
    global ParkingLot, SearchTime, SearchDistance, StepDistance

    reader = pd.read_csv("Data/ParkingRequest_" + str(dataset) + ".csv", iterator=True)
    while True:
        parkingrequest = []
        try:
            chunk = reader.get_chunk(5000)
            parkingrequest = numpy.array(chunk).tolist()

            i = 0
            while i < len(parkingrequest):
                hour, minute = int(parkingrequest[i][0]), int(parkingrequest[i][1])
                nowtime = NowTime(hour, minute)
                epl = eval(parkingrequest[i][-1])  # i.e., expected parking lots
                eplid = str(parkingrequest[i][2])
                cpo = ParkingLot[eplid][nowtime]["occupied"]  # i.e., current parking occupied
                capacity = ParkingLot[eplid]["information"][0]
                if cpo < capacity:  # can be parking
                    nowdistance, targetdistance, nowpsid, targetpsid = 99999, 99999, '0', '0'  # 停车位和当前位置的距离，停车位和目的地的距离
                    for ps in ParkingLot[eplid][nowtime]:
                        if ps != "occupied":
                            pslongitude, pslatitude, status = ParkingLot[eplid][nowtime][ps][0], ParkingLot[eplid][nowtime][ps][
                                1], ParkingLot[eplid][nowtime][ps][2]
                            nowlongitude, nowlatitude = float(parkingrequest[i][3]), float(parkingrequest[i][4])
                            targetlongitude, targetlatitude = float(parkingrequest[i][5]), float(parkingrequest[i][6])
                            if not status:  # 采用以当前位置就近停车策略
                                if strategy == 1:
                                    if geodesic(
                                            (nowlatitude, nowlongitude), (pslatitude, pslongitude)).km < nowdistance:
                                        nowdistance = geodesic(
                                            (nowlatitude, nowlongitude), (pslatitude, pslongitude)).km
                                        nowpsid = ps
                                elif strategy == 2:
                                    if geodesic(
                                            (targetlatitude, targetlongitude), (pslatitude, pslongitude)).km < targetdistance:
                                        targetdistance = geodesic(
                                            (targetlatitude, targetlongitude), (pslatitude, pslongitude)).km
                                        targetpsid = ps
                    if strategy == 1:
                        SearchTime[nowtime] += nowdistance / AvgSpeed
                    elif strategy == 2:
                        SearchTime[nowtime] += targetdistance / AvgSpeed
                    for parkingminute in range(int(duration * 60)):  # 停车持续时段内该停车位的状态均被占用
                        nowtime = NowTime(hour, minute)
                        ParkingLot[eplid][nowtime]["occupied"] += 1
                        ParkingLot[eplid][nowtime][ps][2] = True
                        minute += 1
                        if minute == 60:
                            hour += 1
                            minute = 0
                        if hour == 24:
                            break
                    parkingrequest.pop(i)
                else:
                    if len(epl) == 1:  # 只有一个可选停车场，只能继续在当前停车场等待
                        minute += 1
                        if minute >= 60:
                            hour += 1
                            minute = 0
                        if hour == 24:
                            break
                        parkingrequest[i][0], parkingrequest[i][1] = (2 - len(str(hour))) * '0' + str(hour), (
                                2 - len(str(minute))) * '0' + str(minute)
                        SearchTime[nowtime] += 1
                    else:  # 还有可用停车场，则前往继续搜寻
                        plindex = epl.index(eplid)
                        if plindex < len(epl) - 1:
                            parkingrequest[i][2] = epl[plindex + 1]
                        else:
                            parkingrequest[i][2] = epl[0]
                        nowlongitude, nowlatitude, targetlongitude, targetlatitude = float(parkingrequest[i][3]), float(
                            parkingrequest[i][4]), float(
                            ParkingLot[eplid]["information"][1]), \
                                                                                     float(ParkingLot[eplid]["information"][2])
                        arrivetime = geodesic(
                            (nowlatitude, nowlongitude), (targetlatitude, targetlongitude)).km / AvgSpeed
                        SearchTime[nowtime] += arrivetime
                        if arrivetime < 1:
                            minute += 1
                        else:
                            minute += int(arrivetime)
                        if minute >= 60:
                            hour += 1
                            minute %= 60
                        if hour == 24:
                            break
                        parkingrequest[i][0], parkingrequest[i][1] = (2 - len(str(hour))) * '0' + str(hour), (
                                2 - len(str(minute))) * '0' + str(minute)
                        parkingrequest[i][3] = targetlongitude
                        parkingrequest[i][4] = targetlatitude
                    parkingrequest.sort(key=lambda x: (int(x[0]), int(x[1])))

            with open("Result/CummulativeSearchingTime/" + str(dataset) + "/PSVCP_" + str(duration) + "hour_" + str(
                    strategy) + "_strategy_SearchTime.csv", 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                time = 0
                for key in SearchTime:
                    time += SearchTime[key]
                    print(time)
                    writer.writerow([key, time])
                csvfile.close()
            print("2. PSV Cruise Parking_" + str(duration) + "hour has Finished!")
        except StopIteration:
            print("Iteration is finished.")
            break


# 2.3 Simulate parking: Mixed Cruise Parking
def MixedCruiseParking(dataset, duration, strategy):
    global ParkingLot, SearchTime, SearchDistance, StepDistance
    reader = pd.read_csv("Data/ParkingRequest_" + str(dataset) + ".csv", iterator=True)

    while True:
        parkingrequest = []
        try:
            chunk = reader.get_chunk(5000)
            parkingrequest = numpy.array(chunk).tolist()
            i, count = 0, 0
            while i < len(parkingrequest):
                hour, minute = int(parkingrequest[i][0]), int(parkingrequest[i][1])
                nowtime = NowTime(hour, minute)
                epl = eval(parkingrequest[i][-1])  # i.e., expected parking lots
                eplid = str(parkingrequest[i][2])
                cpo = ParkingLot[eplid][nowtime]["occupied"]  # i.e., current parking occupied
                capacity = ParkingLot[eplid]["information"][0]
                if cpo < capacity:  # can be parking
                    nowdistance, targetdistance, nowpsid, targetpsid = 99999, 99999, '0', '0'  # 停车位和当前位置的距离，停车位和目的地的距离
                    for ps in ParkingLot[eplid][nowtime]:
                        if ps != "occupied":
                            pslongitude, pslatitude, status = ParkingLot[eplid][nowtime][ps][0], ParkingLot[eplid][nowtime][ps][
                                1], ParkingLot[eplid][nowtime][ps][2]
                            nowlongitude, nowlatitude = float(parkingrequest[i][3]), float(parkingrequest[i][4])
                            targetlongitude, targetlatitude = float(parkingrequest[i][5]), float(parkingrequest[i][6])
                            if not status:  # 采用以当前位置就近停车策略
                                if strategy == 1:
                                    if geodesic(
                                            (nowlatitude, nowlongitude), (pslatitude, pslongitude)).km < nowdistance:
                                        nowdistance = geodesic(
                                            (nowlatitude, nowlongitude), (pslatitude, pslongitude)).km
                                        nowpsid = ps
                                elif strategy == 2:
                                    if geodesic(
                                            (targetlatitude, targetlongitude), (pslatitude, pslongitude)).km < targetdistance:
                                        targetdistance = geodesic(
                                            (targetlatitude, targetlongitude), (pslatitude, pslongitude)).km
                                        targetpsid = ps
                    if count % 2 == 0:  # PSV
                        if strategy == 1:
                            SearchTime[nowtime] += nowdistance / AvgSpeed
                        elif strategy == 2:
                            SearchTime[nowtime] += targetdistance / AvgSpeed
                    else:  # Non-PSV
                        if strategy == 1:
                            SearchTime[nowtime] += nowdistance / AvgSpeed
                        elif strategy == 2:
                            SearchTime[nowtime] += targetdistance / AvgSpeed
                        SearchTime[nowtime] += (capacity * AvgSearchingTime / 60) / (1 + capacity - cpo)
                    for parkingminute in range(int(duration * 60)):  # 停车持续时段内该停车位的状态均被占用
                        nowtime = NowTime(hour, minute)
                        ParkingLot[eplid][nowtime]["occupied"] += 1
                        ParkingLot[eplid][nowtime][ps][2] = True
                        minute += 1
                        if minute == 60:
                            hour += 1
                            minute = 0
                        if hour == 24:
                            break
                    count += 1
                    parkingrequest.pop(i)
                else:
                    if len(epl) == 1:  # 只有一个可选停车场，只能继续在当前停车场等待
                        minute += 1
                        if minute >= 60:
                            hour += 1
                            minute = 0
                        if hour == 24:
                            break
                        parkingrequest[i][0], parkingrequest[i][1] = (2 - len(str(hour))) * '0' + str(hour), (
                                2 - len(str(minute))) * '0' + str(minute)
                        SearchTime[nowtime] += 1
                    else:  # 还有可用停车场，则前往继续搜寻
                        plindex = epl.index(eplid)
                        if plindex < len(epl) - 1:
                            parkingrequest[i][2] = epl[plindex + 1]
                        else:
                            parkingrequest[i][2] = epl[0]
                        nowlongitude, nowlatitude, targetlongitude, targetlatitude = float(parkingrequest[i][3]), float(
                            parkingrequest[i][4]), float(
                            ParkingLot[eplid]["information"][1]), \
                                                                                     float(ParkingLot[eplid]["information"][2])
                        arrivetime = geodesic(
                            (nowlatitude, nowlongitude), (targetlatitude, targetlongitude)).km / AvgSpeed
                        SearchTime[nowtime] += arrivetime
                        if arrivetime < 1:
                            minute += 1
                        else:
                            minute += int(arrivetime)
                        if minute >= 60:
                            hour += 1
                            minute %= 60
                        if hour == 24:
                            break
                        parkingrequest[i][0], parkingrequest[i][1] = (2 - len(str(hour))) * '0' + str(hour), (
                                2 - len(str(minute))) * '0' + str(minute)
                        parkingrequest[i][3] = targetlongitude
                        parkingrequest[i][4] = targetlatitude
                    parkingrequest.sort(key=lambda x: (int(x[0]), int(x[1])))

            with open("Result/CummulativeSearchingTime/" + str(dataset) + "/MixedCP_" + str(duration) + "hour_" + str(
                    strategy) + "_strategy_SearchTime.csv", 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                time = 0
                for key in SearchTime:
                    time += SearchTime[key]
                    print(time)
                    writer.writerow([key, time])
                csvfile.close()
            print("2. Mixed Cruise Parking_" + str(duration) + "hour has Finished!")
        except StopIteration:
            print("Iteration is finished.")
            break



if __name__ == '__main__':
    # duration: T_D (parking duration time), [0.5, 1, 2, 3] in this experiments
    # strategy: 1: at the nearest location based on current location; 2: based on destination location and proximity
    # Generatevariables("Birmingham")
    # NonPSVCruiseParking("Birmingham", duration, strategy)
    # Generatevariables("Birmingham")
    # PSVCruiseParking("Birmingham", duration, strategy)
    # Generatevariables("Birmingham")
    # MixedCruiseParking("Birmingham", duration, strategy)
