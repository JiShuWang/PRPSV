In this part, we will detail the code and main idea of two proposed parking algorithms (non-PSV and PSV).

## Preprocessing
Before running the parking algorithms, we first preprocess the dataset and generate many parking requests.

## Cruise Parking
In this parking mode, we set two parking strategies (parking closest to the destination and parking close to the current location). For non-PSV, drivers do not have real-time information about the availability of parking spaces, which leads to blindly searching for parking spaces. For PSV, on the other hand, drivers can quickly find parking spaces and go to park based on the provided real-time parking information.
Therefore, for both non-PSV and PSV, the difference between these two parking modes is the time spent in finding a parking space, and we mainly use this metric to evaluate the advantages and disadvantages of these two parking modes. To better validate and explain the importance and advantages of PSV, we also added a parking mode (mixed cruise parking), i.e., one half for non-PSV and the other half for PSV.
## Reservation Parking
In this parking mode, we use the strategy that parking nearest to the destination. For non-PSV, the reserved parking space is randomly assigned, and for PSV, the reserved parking space can be chosen manually by drivers according to their needs or assigned by the parking systems.
Therefore, for non-PSV and PSV, the difference between these two parking modes is walking distance after parking, and we mainly use the metric to evaluate the advantages and disadvantages of these two parking. To better verify and explain the importance and advantages of PSV, we also add a parking mode (mixed reservation parking), i.e., half of non-PSV, and the rest half of PSV.
