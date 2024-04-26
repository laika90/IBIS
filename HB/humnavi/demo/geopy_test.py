import geopy.distance

print("type latitude")
start_lat = float(input())
print("type longitude")
start_lng = float(input())

target_lat = (
    geopy.distance.distance(meters=10)
    .destination((start_lat, start_lng), bearing=0)
    .latitude
)
target_lng = (
    geopy.distance.distance(meters=10)
    .destination((start_lat, start_lng), bearing=90)
    .longitude
)
print(target_lat, target_lng)
