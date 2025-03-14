import csv
import random

from geopy.distance import geodesic


def Processingparkinglot():
    with open("../Data/Parking Efficiency/ParkingLot_Birmingham.csv", "r", encoding="utf-8") as csvreader:
        data = list(csv.reader(csvreader))[:]
        print(len(data))

        parkingid = set()
        parkinglot = []

        parkinglot.append([data[0][0], data[0][1], "longitude", "latitude", data[0][2]])
        for content in data[1:]:
            if content[0] not in parkingid:
                parkingid.add(content[0])
                lonitude = random.uniform(-1.8304, -1.9504)
                latitude = random.uniform(52.4262, 52.4462)
                parkinglot.append([content[0], content[1], lonitude, latitude, int(0 * float(content[1]))])
        print(len(parkinglot))
        csvreader.close()

    with open("../Data/Parking Efficiency/ParkingLot_Birmingham_Processed.csv", "w", encoding="utf-8", newline='') as csvwriter:
        data = csv.writer(csvwriter)
        for content in parkinglot:
            data.writerow(content)
        csvwriter.close()


def Generaterequest():
    parkinglot = []
    with open("Data/ParkingLot_Birmingham_Processed.csv", "r", encoding="utf-8") as csvreader:
        data = list(csv.reader(csvreader))[1:]
        for content in data:
            parkinglot.append(
                [content[0], int(content[1]), float(content[2]), float(content[3]), int(content[-1])])
        csvreader.close()

    minlongitude, maxlongitude, minlatitude, maxlatitude = parkinglot[0][2], parkinglot[0][2], parkinglot[0][3], \
                                                           parkinglot[0][3]

    for content in parkinglot:  # Calculate Boundary
        minlongitude = min(content[2], minlongitude)
        maxlongitude = max(content[2], maxlongitude)
        minlatitude = min(content[3], minlatitude)
        maxlatitude = max(content[3], maxlatitude)

    peak = 0
    parkingrequest = []
    for hour in range(8, 24):
        for minute in range(0, 60):
            if 10 <= hour <= 14 or (hour == 16 and minute >= 30) or (hour == 17 and minute <= 30):
                peak = 50
            else:
                peak = 25
            for request in range(peak):  # Parking Request
                targetlongitude = random.uniform(maxlongitude, minlongitude)
                targetlatitude = random.uniform(minlatitude, maxlatitude)
                expectedparkinglot = []
                for content in parkinglot:  # Calculate Distance
                    distance = geodesic((content[3], content[2]),
                                        (targetlatitude, targetlongitude)).km
                    if distance < 1.5:
                        expectedparkinglot.append([content[0], distance, content[2], content[3]])
                expectedparkinglot.sort(key=lambda x: x[1])

                nowlongitude = expectedparkinglot[0][2]
                nowlatitude = expectedparkinglot[0][3]

                parkingrequest.append(
                    [(2 - len(str(hour))) * '0' + str(hour), (2 - len(str(minute))) * '0' + str(minute), nowlongitude,
                     nowlatitude, targetlongitude, targetlatitude, [i[0] for i in expectedparkinglot]])

    with open("Data/ParkingRequest.csv", 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Hour", "Minute", "NowLongitude", "NowLatitude", "TarLongitude", "TarLatitude", "ExpectedParkinglot"])
        for content in parkingrequest:
            writer.writerow(content)
        csvfile.close()


def GenerateParkingSpace():
    with open("Data/ParkingLot_Birmingham_Processed.csv", "r", encoding="utf-8") as csvreader:
        partparkinglot = list(csv.reader(csvreader))[1:]
        csvreader.close()

    parkingspace = []
    count = 0
    for content in partparkinglot:
        parkinglotid, capacity, longitude, latitude = content[0], int(content[1]), float(content[2]), float(content[3])

        for top in range(capacity // 2):
            longitude = (longitude * 100000 - 1) / 100000
            latitude = (latitude * 100000 - 1) / 100000
            count += 1
            parkingspace.append([parkinglotid, count, round(longitude, 5), round(latitude, 5)])
        parkinglotid, longitude, latitude = content[0], float(content[2]), float(content[3])
        for bottom in range(capacity // 2, capacity):
            longitude = (longitude * 100000 + 1) / 100000
            latitude = (latitude * 100000 + 1) / 100000
            count += 1
            parkingspace.append([parkinglotid, count, round(longitude, 5), round(latitude, 5)])
    with open("Data/ParkingSpace_Birmingham_Processed.csv", "w", encoding="utf-8",
              newline='') as csvwriter:
        data = csv.writer(csvwriter)
        data.writerow(["PLID", "PSID", "Longitude", "Latitude"])
        for content in parkingspace:
            data.writerow(content)
        csvwriter.close()



if __name__ == '__main__':
    # Processingparkinglot() # Step 1
    # Generaterequest() # Step 2
    # GenerateParkingSpace() # Step 3
