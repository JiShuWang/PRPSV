import csv
import random

import numpy
import pandas as pd
from geopy.distance import geodesic

ParkingLot = {}
ParkingSpace = {}
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


def GeneratevariablesSingle():
    global ParkingLot, SearchTime, StepDistance
    with open("Data/ParkingSpace_Beijing_Largest.csv", "r", encoding="utf-8") as csvreader:
        parkingspace = list(csv.reader(csvreader))[1:]
        csvreader.close()

    for pl in [["1", "322", "116.28040", "39.93484"]]:
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


# 3.1 Simulate parking: Non-PSV Reservation Parking
def NonPSVReserveParking(dataset, duration):
    global ParkingLot, SearchTime, SearchingDistance, StepDistance
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
                    selectableps = []
                    for ps in ParkingLot[eplid][nowtime]:
                        if ps != "occupied":
                            pslongitude, pslatitude, status = ParkingLot[eplid][nowtime][ps][0], ParkingLot[eplid][nowtime][ps][
                                1], ParkingLot[eplid][nowtime][ps][2]
                            targetlongitude, targetlatitude = float(parkingrequest[i][5]), float(parkingrequest[i][6])
                            if not status:
                                distance = geodesic(
                                    (pslatitude, pslongitude), (targetlatitude, targetlongitude)).km
                                selectableps.append([ps, distance])
                    randomindex = random.randint(0, len(selectableps) - 1)
                    StepDistance[nowtime] += selectableps[randomindex][1]
                    for parkingminute in range(int(duration * 60)):
                        nowtime = NowTime(hour, minute)
                        ParkingLot[eplid][nowtime]["occupied"] += 1
                        ParkingLot[eplid][nowtime][selectableps[randomindex][0]][2] = True
                        minute += 1
                        if minute == 60:
                            hour += 1
                            minute = 0
                        if hour == 24:
                            break
                    parkingrequest.pop(i)
                else:
                    if len(epl) == 1:
                        minute += 1
                        if minute >= 60:
                            hour += 1
                            minute = 0
                        if hour == 24:
                            break
                        parkingrequest[i][0], parkingrequest[i][1] = (2 - len(str(hour))) * '0' + str(hour), (
                                2 - len(str(minute))) * '0' + str(minute)
                        SearchTime[nowtime] += 1
                    else:
                        plindex = epl.index(eplid)
                        if plindex < len(epl) - 1:
                            parkingrequest[i][2] = epl[plindex + 1]
                        else:
                            parkingrequest[i][2] = epl[0]
                        nowlongitude, nowlatitude, targetlongitude, targetlatitude = float(parkingrequest[i][3]), float(
                            parkingrequest[i][4]), float(
                            ParkingLot[eplid]["information"][1]), float(ParkingLot[eplid]["information"][2])
                        minute += 1
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

            with open("Result/WalkingDistance/" + str(dataset) + "/NonPSVRP_" + str(duration) + "hour_WalkingDistance.csv", 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                walkingdistance = 0
                for key in StepDistance:
                    walkingdistance += StepDistance[key]
                    print(walkingdistance)
                    writer.writerow([key, walkingdistance])
                csvfile.close()
            print("2. Non-PSV Reserve Parking_" + str(duration) + "hour has Finished!")
        except StopIteration:
            print("Iteration is finished.")
            break


# 3.2 Simulate parking: PSV Reservation Parking
def PSVReserveParking(dataset, duration):
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
                    targetdistance, targetpsid = 99999, '0'
                    for ps in ParkingLot[eplid][nowtime]:
                        if ps != "occupied":
                            pslongitude, pslatitude, status = ParkingLot[eplid][nowtime][ps][0], ParkingLot[eplid][nowtime][ps][
                                1], ParkingLot[eplid][nowtime][ps][2]
                            targetlongitude, targetlatitude = float(parkingrequest[i][5]), float(parkingrequest[i][6])
                            if not status:
                                if geodesic(
                                        (targetlatitude, targetlongitude), (pslatitude, pslongitude)).km < targetdistance:
                                    targetdistance = geodesic(
                                        (targetlatitude, targetlongitude), (pslatitude, pslongitude)).km
                                    targetpsid = ps
                    StepDistance[nowtime] += targetdistance
                    for parkingminute in range(int(duration * 60)):
                        nowtime = NowTime(hour, minute)
                        ParkingLot[eplid][nowtime]["occupied"] += 1
                        ParkingLot[eplid][nowtime][targetpsid][2] = True
                        minute += 1
                        if minute == 60:
                            hour += 1
                            minute = 0
                        if hour == 24:
                            break
                    parkingrequest.pop(i)
                else:
                    if len(epl) == 1:
                        minute += 1
                        if minute >= 60:
                            hour += 1
                            minute = 0
                        if hour == 24:
                            break
                        parkingrequest[i][0], parkingrequest[i][1] = (2 - len(str(hour))) * '0' + str(hour), (
                                2 - len(str(minute))) * '0' + str(minute)
                        SearchTime[nowtime] += 1
                    else:
                        plindex = epl.index(eplid)
                        if plindex < len(epl) - 1:
                            parkingrequest[i][2] = epl[plindex + 1]
                        else:
                            parkingrequest[i][2] = epl[0]
                        nowlongitude, nowlatitude, targetlongitude, targetlatitude = float(parkingrequest[i][3]), float(
                            parkingrequest[i][4]), float(
                            ParkingLot[eplid]["information"][1]), float(ParkingLot[eplid]["information"][2])
                        minute += 1
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

            with open("Result/WalkingDistance/" + str(dataset) + "/PSVRP_" + str(duration) + "hour_WalkingDistance.csv", 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                walkingdistance = 0
                for key in StepDistance:
                    walkingdistance += StepDistance[key]
                    print(walkingdistance)
                    writer.writerow([key, walkingdistance])
                csvfile.close()
            print("2. PSV Reserve Parking_" + str(duration) + "hour has Finished!")
        except StopIteration:
            print("Iteration is finished.")
            break


# 3.3 Simulate parking: Mixed Reservation Parking
def MixedReserveParking(dataset, duration):
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
                    if count % 2 == 0:  # PSV
                        targetdistance, targetpsid = 99999, '0'
                        for ps in ParkingLot[eplid][nowtime]:
                            if ps != "occupied":
                                pslongitude, pslatitude, status = ParkingLot[eplid][nowtime][ps][0], \
                                                                  ParkingLot[eplid][nowtime][ps][1], \
                                                                  ParkingLot[eplid][nowtime][ps][2]
                                targetlongitude, targetlatitude = float(parkingrequest[i][5]), float(parkingrequest[i][6])
                                if not status:
                                    if geodesic(
                                            (targetlatitude, targetlongitude), (pslatitude, pslongitude)).km < targetdistance:
                                        targetdistance = geodesic(
                                            (targetlatitude, targetlongitude), (pslatitude, pslongitude)).km
                                        targetpsid = ps
                        StepDistance[nowtime] += targetdistance
                        for parkingminute in range(int(duration * 60)):  # Changing the status of the parking space and parking lot at the period duration
                            nowtime = NowTime(hour, minute)
                            ParkingLot[eplid][nowtime]["occupied"] += 1
                            ParkingLot[eplid][nowtime][targetpsid][2] = True
                            minute += 1
                            if minute == 60:
                                hour += 1
                                minute = 0
                            if hour == 24:
                                break
                    else:  # Non-PSV
                        selectableps = []  # The list of vacant parking spaces in the parking lot
                        for ps in ParkingLot[eplid][nowtime]:
                            if ps != "occupied":
                                pslongitude, pslatitude, status = ParkingLot[eplid][nowtime][ps][0], \
                                                                  ParkingLot[eplid][nowtime][ps][1], \
                                                                  ParkingLot[eplid][nowtime][ps][2]
                                targetlongitude, targetlatitude = float(parkingrequest[i][5]), float(parkingrequest[i][6])
                                if not status:  #
                                    distance = geodesic(
                                        (pslatitude, pslongitude), (targetlatitude, targetlongitude)).km
                                    selectableps.append([ps, distance])
                        randomindex = random.randint(0, len(selectableps) - 1)  # Randomly assign a reservation parking space
                        StepDistance[nowtime] += selectableps[randomindex][1]
                        for parkingminute in range(int(duration * 60)):  # Changing the status of the parking space and parking lot at the period duration
                            nowtime = NowTime(hour, minute)
                            ParkingLot[eplid][nowtime]["occupied"] += 1
                            ParkingLot[eplid][nowtime][selectableps[randomindex][0]][2] = True
                            minute += 1
                            if minute == 60:
                                hour += 1
                                minute = 0
                            if hour == 24:
                                break
                    count += 1
                    parkingrequest.pop(i)
                else:
                    if len(epl) == 1:  # Only one selectable parking lot, then wait one minute and to continue to search
                        minute += 1
                        if minute >= 60:
                            hour += 1
                            minute = 0
                        if hour == 24:
                            break
                        parkingrequest[i][0], parkingrequest[i][1] = (2 - len(str(hour))) * '0' + str(hour), (
                                2 - len(str(minute))) * '0' + str(minute)
                        SearchTime[nowtime] += 1
                    else:  # Arrive to the next parking lot and continue to search
                        plindex = epl.index(eplid)
                        if plindex < len(epl) - 1:
                            parkingrequest[i][2] = epl[plindex + 1]
                        else:
                            parkingrequest[i][2] = epl[0]
                        nowlongitude, nowlatitude, targetlongitude, targetlatitude = float(parkingrequest[i][3]), float(
                            parkingrequest[i][4]), float(
                            ParkingLot[eplid]["information"][1]), float(ParkingLot[eplid]["information"][2])
                        minute += 1
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

            with open("Result/WalkingDistance/" + str(dataset) + "/MixedRP_" + str(duration) + "hour_WalkingDistance.csv", 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                walkingdistance = 0
                for key in StepDistance:
                    walkingdistance += StepDistance[key]
                    print(walkingdistance)
                    writer.writerow([key, walkingdistance])
                csvfile.close()
            print("2. Mixed Reserve Parking_" + str(duration) + "hour has Finished!")
        except StopIteration:
            print("Iteration is finished.")
            break


if __name__ == '__main__':
    Generatevariables("Birmingham")
    NonPSVReserveParking("Birmingham", 0.5)
    Generatevariables("Birmingham")
    PSVReserveParking("Birmingham", 0.5)
    Generatevariables("Birmingham")
    MixedReserveParking("Birmingham", 0.5)
    for duration in range(1, 4):
        Generatevariables("Birmingham")
        NonPSVReserveParking("Birmingham", duration)
        Generatevariables("Birmingham")
        PSVReserveParking("Birmingham", duration)
        Generatevariables("Birmingham")
        MixedReserveParking("Birmingham", duration)
