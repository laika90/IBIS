def lat_lng_calibration(
    original_LAT_1DEG,
    original_LNG_1DEG,
    actual_north_m,
    actual_east_m,
    target_north_m,
    target_east_m,
):
    fixed_LAT_1DEG = original_LAT_1DEG * actual_north_m / target_north_m
    fixed_LNG_1DEG = original_LNG_1DEG * actual_east_m / target_east_m
    print("fixed LAT_1DEG:", fixed_LAT_1DEG)
    print("fixed LNG_1DEG:", fixed_LNG_1DEG)


if __name__ == "__main__":
    original_LAT_1DEG = 110940.5844  # at lat 35 deg
    original_LNG_1DEG = 91287.7885  # at lat 35 deg
    print("how long did hum-bird fly to north? e.g.) 9.8")
    actual_north_m = float(input())
    print("how long did hum-bird fly to east? e.g.) 9.8")
    actual_east_m = float(input())
    target_north_m = 10
    target_east_m = 10
    lat_lng_calibration(
        original_LAT_1DEG,
        original_LNG_1DEG,
        actual_north_m,
        actual_east_m,
        target_north_m,
        target_east_m,
    )
