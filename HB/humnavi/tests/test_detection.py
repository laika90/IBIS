import numpy as np
import pytest

from humnavi.detection import LibcsDetection

detection = LibcsDetection()


def test_coordinate_transform():
    test_x, test_y = 0, 1
    rot_deg = 45
    transformed_x, transformed_y = detection.coordinate_transform(
        test_x, test_y, rot_deg
    )
    assert abs(transformed_x - 1 / np.sqrt(2)) < 1e-5
    assert abs(transformed_y - 1 / np.sqrt(2)) < 1e-5
    test_x, test_y = 1, 0
    rot_deg = 45
    transformed_x, transformed_y = detection.coordinate_transform(
        test_x, test_y, rot_deg
    )
    assert abs(transformed_x - 1 / np.sqrt(2)) < 1e-5
    assert abs(transformed_y + 1 / np.sqrt(2)) < 1e-5
    test_x, test_y = 1, 0
    rot_deg = 90
    transformed_x, transformed_y = detection.coordinate_transform(
        test_x, test_y, rot_deg
    )
    assert abs(transformed_x) < 1e-5
    assert abs(transformed_y + 1) < 1e-5
