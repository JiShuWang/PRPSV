import csv
import math
import random

import numpy
import pandas as pd
from geopy.distance import geodesic

ParkingLot = {}
ParkingSpace = {}  # Determine the parking space is whether to park
AvgSearchingTime = 3  # Seconds
SearchTime = {}
SearchingDistance = {}
StepDistance = {}
PeriodDrivingDistance = {}
ExtraDrivingDistance = {}
MisjudgementFlag = {}
OptimalPS = {}
AvgSpeed = 0.75  # The speed, km/min


def NowTime(hour, minute):
    return (2 - len(str(hour))) * '0' + str(hour) + (2 - len(str(minute))) * '0' + str(minute)


# 1. Generate variables
def Generatevariables(dataset):
    global ParkingLot, SearchTime, StepDistance, PeriodDrivingDistance, ExtraDrivingDistance, MisjudgementFlag, OptimalPS
    ParkingLot, SearchTime, StepDistance, PeriodDrivingDistance, ExtraDrivingDistance, MisjudgementFlag, OptimalPS = {}, {}, {}, {}, {}, {}, {}
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
                PeriodDrivingDistance.setdefault(nowtime, 0)
                ParkingLot[parkinglotid].setdefault(nowtime, {"occupied": 0})  # key: nowtime, value:{}
                for ps in parkingspace:
                    plid, psid, pslongitude, pslatitude = ps[0], ps[1], float(ps[2]), float(ps[3])
                    if plid == parkinglotid:
                        ParkingLot[parkinglotid][nowtime].setdefault(psid, [pslongitude, pslatitude,
                                                                            False])  # key: parking space id, value:False (judge the parking space is whether be occupied at this time)
    print("1. Preparing has Finished!")


def calculate_current_position(lat1, lon1, lat2, lon2, distance):
    R = 6371

    phi1 = math.radians(lat1)
    lambda1 = math.radians(lon1)
    phi2 = math.radians(lat2)
    lambda2 = math.radians(lon2)

    delta_lambda = lambda2 - lambda1

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    theta = math.atan2(y, x)

    d_over_R = distance / R
    sin_phi1 = math.sin(phi1)
    cos_phi1 = math.cos(phi1)
    sin_d = math.sin(d_over_R)
    cos_d = math.cos(d_over_R)

    new_phi = math.asin(sin_phi1 * cos_d + cos_phi1 * sin_d * math.cos(theta))

    delta_lambda_new = math.atan2(math.sin(theta) * sin_d * cos_phi1,
                                  cos_d - sin_phi1 * math.sin(new_phi))
    new_lambda = lambda1 + delta_lambda_new

    new_lambda = (new_lambda + 3 * math.pi) % (2 * math.pi) - math.pi

    current_lat = math.degrees(new_phi)
    current_lon = math.degrees(new_lambda)

    return (current_lat, current_lon)


# 2.2 Simulate parking: PSV Cruise Parking
def PSVCruiseParking(dataset, duration, strategy, misjudgmentrate1, misjudgmentrate2, method):
    global ParkingLot, SearchTime, SearchDistance, StepDistance, PeriodDrivingDistance, ExtraDrivingDistance, MisjudgementFlag, OptimalPS

    reader = pd.read_csv("Data/ParkingRequest_" + str(dataset) + ".csv", iterator=True)
    while True:
        try:
            chunk = reader.get_chunk(5000)
            parkingrequest = numpy.array(chunk).tolist()
            i = 0
            while i < len(parkingrequest):
                id, hour, minute = parkingrequest[i][0], int(parkingrequest[i][1]), int(parkingrequest[i][2])
                nowtime = NowTime(hour, minute)
                epl = eval(parkingrequest[i][-1])  # i.e., expected parking lots
                eplid = str(parkingrequest[i][3])
                cpo = ParkingLot[eplid][nowtime]["occupied"]  # i.e., current parking occupied
                capacity = ParkingLot[eplid]["information"][0]
                startlongitude, startlatitude = float(parkingrequest[i][4]), float(parkingrequest[i][5])
                currentlongitude, currentlatitude = float(parkingrequest[i][6]), float(parkingrequest[i][7])
                targetlongitude, targetlatitude = float(parkingrequest[i][-3]), float(parkingrequest[i][-2])
                if id not in OptimalPS:
                    ExtraDrivingDistance.setdefault(id, 0)
                    MisjudgementFlag.setdefault(id, False)
                    OptimalPS.setdefault(id, [])
                if cpo < capacity:  # can be parking
                    startdistance, currentdistance, targetdistance, nowpsid, targetpsid = 99999, 99999, 99999, '0', '0'  # 停车位和起点的距离，停车位和当前位置的距离，停车位和目的地的距离
                    optimalps = []  # The optimal parking spaces, location: [psid, longitude, latitude, distance]
                    for ps in ParkingLot[eplid][nowtime]:
                        if ps != "occupied":
                            randomnumber1 = random.randint(1, 10000)
                            randomnumber2 = random.randint(1, 10000)
                            if (randomnumber1 <= misjudgmentrate1 * 10000 and ParkingLot[eplid][nowtime][ps][2]) or (
                                    not ParkingLot[eplid][nowtime][ps][2] and randomnumber2 > misjudgmentrate2 * 10000):
                                pslongitude, pslatitude = ParkingLot[eplid][nowtime][ps][0], \
                                                          ParkingLot[eplid][nowtime][ps][
                                                              1]
                                if strategy == 1:  # Parking Strategy 1
                                    if geodesic(
                                            (currentlatitude, currentlongitude),
                                            (pslatitude, pslongitude)).km < currentdistance:
                                        currentdistance = geodesic(
                                            (currentlatitude, currentlongitude), (pslatitude, pslongitude)).km
                                        optimalps.append([ps, pslongitude, pslatitude, currentdistance])
                                elif strategy == 2:# Parking Strategy 2
                                    if geodesic(
                                            (targetlatitude, targetlongitude),
                                            (pslatitude, pslongitude)).km < targetdistance:
                                        targetdistance = geodesic(
                                            (targetlatitude, targetlongitude), (pslatitude, pslongitude)).km
                                        optimalps.append([ps, pslongitude, pslatitude, targetdistance])
                    optimalps.sort(key=lambda x: x[3])
                    OptimalPS[id] = optimalps
                    if ParkingLot[eplid][nowtime][OptimalPS[id][0][0]][2]:
                        MisjudgementFlag[id] = True
                    SearchTime[nowtime] += 1
                    currentdistance = OptimalPS[id][0][3]
                    arrivetime = currentdistance / AvgSpeed
                    if arrivetime <= 1:  # Parking
                        if ParkingLot[eplid][nowtime][OptimalPS[id][0][0]][2]:
                            if MisjudgementFlag[id]:
                                ExtraDrivingDistance[id] += currentdistance
                            minute += 1
                            if minute == 60:
                                hour += 1
                                minute = 0
                            if hour == 24:
                                break
                            parkingrequest[i][6], parkingrequest[i][7] = OptimalPS[id][0][1], OptimalPS[id][0][2]
                            parkingrequest[i][1], parkingrequest[i][2] = (2 - len(str(hour))) * '0' + str(hour), (
                                    2 - len(str(minute))) * '0' + str(minute)
                        else:
                            if MisjudgementFlag[id]:
                                # ExtraDrivingDistance[id] -= geodesic(
                                #     (startlatitude, startlongitude), (OptimalPS[id][0][2], OptimalPS[id][0][1])).km
                                PeriodDrivingDistance[nowtime] += ExtraDrivingDistance[id]
                            for parkingminute in range(int(duration * 60)):  # The parking space will be occupied at this duration
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
                        minute += 1
                        if minute == 60:
                            hour += 1
                            minute = 0
                        if hour == 24:
                            break
                        if MisjudgementFlag[id]:
                            ExtraDrivingDistance[id] += AvgSpeed
                        currentposition = calculate_current_position(currentlatitude, currentlongitude,
                                                                     OptimalPS[id][0][2],
                                                                     OptimalPS[id][0][1], AvgSpeed)
                        parkingrequest[i][6], parkingrequest[i][7] = currentposition[0], currentposition[1]
                        parkingrequest[i][1], parkingrequest[i][2] = (2 - len(str(hour))) * '0' + str(hour), (
                                2 - len(str(minute))) * '0' + str(minute)
                else:
                    SearchTime[nowtime] += 1
                    if len(epl) == 1:  # Only one parking lot and will wait
                        minute += 1
                        if minute >= 60:
                            hour += 1
                            minute = 0
                        if hour == 24:
                            break
                        parkingrequest[i][1], parkingrequest[i][2] = (2 - len(str(hour))) * '0' + str(hour), (
                                2 - len(str(minute))) * '0' + str(minute)
                    else: # Keeping search in other optional parking lots
                        plindex = epl.index(eplid)
                        if plindex < len(epl) - 1:
                            parkingrequest[i][3] = epl[plindex + 1]
                        else:
                            parkingrequest[i][3] = epl[0]
                        targetlongitude, targetlatitude = float(
                            ParkingLot[eplid]["information"][1]), float(
                            ParkingLot[eplid][
                                "information"][
                                2])
                        minute += 1
                        if minute >= 60:
                            hour += 1
                            minute %= 60
                        if hour == 24:
                            break
                        parkingrequest[i][1], parkingrequest[i][2] = (2 - len(str(hour))) * '0' + str(hour), (
                                2 - len(str(minute))) * '0' + str(minute)
                parkingrequest.sort(key=lambda x: (int(x[1]), int(x[2])))

            with open("Result/CummulativeSearchingTime/" + str(dataset) + "/PSVCP_" + str(duration) + "hour_" + str(
                    strategy) + "_strategy_SearchTime.csv", 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                time = 0
                for key in SearchTime:
                    time += SearchTime[key]
                    print(time)
                    writer.writerow([key, time])
                csvfile.close()
            with open("Result/CummulativeExtraDrivingDistance/" + str(dataset) + "/PSVCP_" + str(
                    duration) + "hour_" + str(
                strategy) + "_strategy_" + str(method) + ".csv", 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                extradistance = 0
                for key in PeriodDrivingDistance:
                    extradistance += PeriodDrivingDistance[key]
                    print(extradistance)
                    writer.writerow([key, extradistance])
                csvfile.close()
            print("2. PSV Cruise Parking_" + str(duration) + "hour has Finished!")
        except StopIteration:
            print("Iteration is finished.")
            break


if __name__ == '__main__':
    # duration: T_D (parking duration time), [0.5, 1, 2, 3] in this experiments
    # strategy: 1: at the nearest location based on current location; 2: based on destination location and proximity
    for strategy in [1, 2]:
        for duration in [0.5, 1, 2, 3]:
            Generatevariables("Birmingham")
            PSVCruiseParking("Birmingham", duration, strategy, 0.0012, 0.0032,
                             "ResNet")  # Two misjudgment conditions and its misjudgment rate: Vacant -> Occupied and Occupied -> Vacant
