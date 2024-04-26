from geopy import distance
print("start lat")
start_lat_deg = float(input())
print("start lng")
start_lng_deg = float(input())
print("goal lat")
goal_lat_deg = float(input())
print("goal lng")
goal_lng_deg = float(input())
target = (start_lat_deg, start_lng_deg)
cur_pos = (goal_lat_deg, goal_lng_deg)
remaining_dist = distance.distance(target, cur_pos).meters
print(remaining_dist)