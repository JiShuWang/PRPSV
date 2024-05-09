In this part, we will detail the code and main idea of two proposed parking algorithms (non-PSV and PSV).

## Preprocessing
Before running the parking algorithms, we first preprocess the dataset and generate many parking requests.

## Cruise Parking

## Reservation Parking
In this parking mode, we use the strategy that parking nearest at the destination. For non-PSV, the reserved parking space is randomly assigned, and for PSV, the reserved parking space can be choose manully by drivers according to their needs or assigned by the parking systems.

Therefore, for non-PSV and PSV, the difference of these two parking modes is walking distance after parking, and we main use the metric to evaluate the advantages and disvantages of these two parkings. To better verify and explain the importance and advantages of PSV, we also add a parking mode (mixed reservation parking), i.e., a half of non-PSV, and the rest of a half of PSV.
