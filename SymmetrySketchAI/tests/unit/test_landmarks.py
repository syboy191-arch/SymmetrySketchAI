"""Unit tests for vision.landmarks."""

from __future__ import annotations

import pytest

from vision.landmarks import (
    Finger,
    HandLandmarkIndex,
    LandmarkPoint,
    Landmarks,
    LandmarkValidationError,
)


def make_landmarks(**overrides: object) -> Landmarks:
    """Test helper: build 21 simple, deterministic landmarks."""
    points = tuple(
        LandmarkPoint(x=i / 20.0, y=1.0 - i / 20.0, z=0.0) for i in range(21)
    )
    if "points" in overrides:
        points = overrides["points"]  # type: ignore[assignment]
    return Landmarks(points=points)


class TestLandmarkPoint:
    def test_distance_to_computes_3d_euclidean_distance(self) -> None:
        a = LandmarkPoint(x=0.0, y=0.0, z=0.0)
        b = LandmarkPoint(x=3.0, y=4.0, z=0.0)
        assert a.distance_to(b) == pytest.approx(5.0)

    def test_distance_to_2d_ignores_z(self) -> None:
        a = LandmarkPoint(x=0.0, y=0.0, z=100.0)
        b = LandmarkPoint(x=3.0, y=4.0, z=-100.0)
        assert a.distance_to_2d(b) == pytest.approx(5.0)

    def test_as_tuple_returns_xyz(self) -> None:
        p = LandmarkPoint(x=1.0, y=2.0, z=3.0)
        assert p.as_tuple() == (1.0, 2.0, 3.0)

    def test_is_immutable(self) -> None:
        p = LandmarkPoint(x=0.0, y=0.0)
        with pytest.raises(Exception):
            p.x = 5.0  # type: ignore[misc]


class TestLandmarksConstruction:
    def test_construction_with_21_points_succeeds(self) -> None:
        landmarks = make_landmarks()
        assert len(landmarks) == 21

    def test_rejects_too_few_points(self) -> None:
        with pytest.raises(LandmarkValidationError):
            Landmarks(points=tuple(LandmarkPoint(0.0, 0.0) for _ in range(20)))

    def test_rejects_too_many_points(self) -> None:
        with pytest.raises(LandmarkValidationError):
            Landmarks(points=tuple(LandmarkPoint(0.0, 0.0) for _ in range(22)))

    def test_from_coordinates_builds_landmarks(self) -> None:
        coords = [(i / 20.0, i / 20.0, 0.0) for i in range(21)]
        landmarks = Landmarks.from_coordinates(coords)
        assert len(landmarks) == 21
        assert landmarks[0].as_tuple() == (0.0, 0.0, 0.0)


class TestLandmarksAccess:
    def test_by_index_matches_getitem(self) -> None:
        landmarks = make_landmarks()
        assert landmarks.by_index(HandLandmarkIndex.WRIST) == landmarks[0]
        assert (
            landmarks.by_index(HandLandmarkIndex.THUMB_TIP) == landmarks[4]
        )

    def test_named_properties_match_indices(self) -> None:
        landmarks = make_landmarks()
        assert landmarks.wrist == landmarks[HandLandmarkIndex.WRIST]
        assert landmarks.thumb_tip == landmarks[HandLandmarkIndex.THUMB_TIP]
        assert (
            landmarks.index_finger_tip
            == landmarks[HandLandmarkIndex.INDEX_FINGER_TIP]
        )
        assert (
            landmarks.middle_finger_tip
            == landmarks[HandLandmarkIndex.MIDDLE_FINGER_TIP]
        )
        assert (
            landmarks.ring_finger_tip
            == landmarks[HandLandmarkIndex.RING_FINGER_TIP]
        )
        assert landmarks.pinky_tip == landmarks[HandLandmarkIndex.PINKY_TIP]

    def test_iteration_yields_all_21_points(self) -> None:
        landmarks = make_landmarks()
        assert sum(1 for _ in landmarks) == 21


class TestLandmarksFingerLookup:
    @pytest.mark.parametrize(
        "finger,expected_tip_index",
        [
            (Finger.THUMB, HandLandmarkIndex.THUMB_TIP),
            (Finger.INDEX, HandLandmarkIndex.INDEX_FINGER_TIP),
            (Finger.MIDDLE, HandLandmarkIndex.MIDDLE_FINGER_TIP),
            (Finger.RING, HandLandmarkIndex.RING_FINGER_TIP),
            (Finger.PINKY, HandLandmarkIndex.PINKY_TIP),
        ],
    )
    def test_finger_tip_matches_expected_index(
        self, finger: Finger, expected_tip_index: HandLandmarkIndex
    ) -> None:
        landmarks = make_landmarks()
        assert landmarks.finger_tip(finger) == landmarks[expected_tip_index]

    def test_finger_landmarks_returns_four_points_base_to_tip(self) -> None:
        landmarks = make_landmarks()
        index_finger = landmarks.finger_landmarks(Finger.INDEX)
        assert len(index_finger) == 4
        assert index_finger[-1] == landmarks.index_finger_tip


class TestLandmarksGeometry:
    def test_distance_between_two_landmarks(self) -> None:
        points = [LandmarkPoint(x=0.0, y=0.0, z=0.0) for _ in range(21)]
        points[0] = LandmarkPoint(x=0.0, y=0.0, z=0.0)
        points[4] = LandmarkPoint(x=3.0, y=4.0, z=0.0)
        landmarks = Landmarks(points=tuple(points))
        distance = landmarks.distance_between(
            HandLandmarkIndex.WRIST, HandLandmarkIndex.THUMB_TIP
        )
        assert distance == pytest.approx(5.0)

    def test_bounding_box_covers_all_points(self) -> None:
        points = [LandmarkPoint(x=0.5, y=0.5, z=0.0) for _ in range(21)]
        points[0] = LandmarkPoint(x=0.1, y=0.2, z=0.0)
        points[10] = LandmarkPoint(x=0.9, y=0.8, z=0.0)
        landmarks = Landmarks(points=tuple(points))
        min_x, min_y, max_x, max_y = landmarks.bounding_box()
        assert min_x == pytest.approx(0.1)
        assert min_y == pytest.approx(0.2)
        assert max_x == pytest.approx(0.9)
        assert max_y == pytest.approx(0.8)

    def test_centroid_is_average_of_points(self) -> None:
        points = tuple(LandmarkPoint(x=1.0, y=2.0, z=3.0) for _ in range(21))
        landmarks = Landmarks(points=points)
        centroid = landmarks.centroid()
        assert centroid.x == pytest.approx(1.0)
        assert centroid.y == pytest.approx(2.0)
        assert centroid.z == pytest.approx(3.0)
