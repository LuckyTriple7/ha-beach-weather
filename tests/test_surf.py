"""Tests for the Surf Score calculation (pure functions, no HA scaffolding)."""
from custom_components.beach_weather.const import DEFAULT_SURF_WEIGHTS
from custom_components.beach_weather.surf import (
    angular_diff,
    calculate_surf_score,
    score_direction_diff,
    score_wave_height,
    score_wave_period,
    score_water_temperature,
    score_wind_speed,
    surf_condition_for_score,
    surf_stars_for_score,
)


class TestAngularDiff:
    def test_simple_difference(self):
        assert angular_diff(354, 340) == 14

    def test_wraps_around_360(self):
        assert angular_diff(350, 10) == 20

    def test_max_is_180(self):
        assert angular_diff(0, 180) == 180

    def test_matches_swell_example_from_spec(self):
        # Strand 340°, Dünung 280° -> Differenz 60°
        assert angular_diff(280, 340) == 60


class TestScoreTables:
    def test_wave_period_bands(self):
        assert score_wave_period(3) == 0
        assert score_wave_period(5) == 25
        assert score_wave_period(7) == 50
        assert score_wave_period(9) == 75
        assert score_wave_period(12) == 100
        assert score_wave_period(15) == 90

    def test_wave_height_bands(self):
        assert score_wave_height(0.2) == 0
        assert score_wave_height(0.4) == 30
        assert score_wave_height(0.6) == 60
        assert score_wave_height(1.0) == 100
        assert score_wave_height(1.8) == 80
        assert score_wave_height(2.5) == 60

    def test_wind_speed_bands(self):
        assert score_wind_speed(5) == 100
        assert score_wind_speed(15) == 80
        assert score_wind_speed(25) == 50
        assert score_wind_speed(35) == 20
        assert score_wind_speed(50) == 0

    def test_direction_diff_bands(self):
        assert score_direction_diff(14) == 100  # matches spec's wind example
        assert score_direction_diff(60) == 70  # matches spec's swell example
        assert score_direction_diff(150) == 0

    def test_water_temperature_bands(self):
        assert score_water_temperature(15) == 0
        assert score_water_temperature(17) == 30
        assert score_water_temperature(19) == 60
        assert score_water_temperature(22) == 100
        assert score_water_temperature(28) == 90


class TestSurfConditionAndStars:
    def test_condition_bands(self):
        assert surf_condition_for_score(10) == "no_surf"
        assert surf_condition_for_score(35) == "poor"
        assert surf_condition_for_score(55) == "okay"
        assert surf_condition_for_score(75) == "good"
        assert surf_condition_for_score(88) == "very_good"
        assert surf_condition_for_score(95) == "perfect"

    def test_stars_bands(self):
        assert surf_stars_for_score(10) == 1
        assert surf_stars_for_score(35) == 2
        assert surf_stars_for_score(55) == 3
        assert surf_stars_for_score(75) == 4
        assert surf_stars_for_score(95) == 5


class TestCalculateSurfScore:
    def _score(self, **overrides):
        params = {
            "wave_period": 9.0,
            "wave_height": 1.0,
            "swell_direction": 340.0,
            "wind_direction": 340.0,
            "wind_speed": 10.0,
            "water_temperature": 22.0,
            "beach_orientation": 340.0,
            "weights": DEFAULT_SURF_WEIGHTS,
        }
        params.update(overrides)
        return calculate_surf_score(**params)

    def test_perfect_inputs_score_100(self):
        # All sub-scores maxed, no bonus triggers (wind not offshore since
        # wind_direction == beach_orientation here) -> should still cap at 100.
        score = self._score(wave_period=12, wave_height=1.0, water_temperature=22)
        assert score == 100

    def test_worst_inputs_score_low(self):
        score = self._score(
            wave_period=2,
            wave_height=0.1,
            wind_speed=60,
            water_temperature=10,
            swell_direction=160,  # ~180° off a 340° beach orientation
            wind_direction=160,
        )
        assert score < 20

    def test_bonuses_stack_and_cap_at_100(self):
        # Frontal swell (diff 0) + offshore wind (diff 180) + long period/big
        # waves -> both +10 bonuses apply, but total is capped at 100.
        score = self._score(
            swell_direction=340,
            wind_direction=160,
            wave_period=12,
            wave_height=1.2,
            water_temperature=22,
        )
        assert score == 100

    def test_weights_are_normalized_when_not_summing_to_100(self):
        equal_weights = {key: 1.0 for key in DEFAULT_SURF_WEIGHTS}
        score = self._score(weights=equal_weights)
        assert 0 <= score <= 100
