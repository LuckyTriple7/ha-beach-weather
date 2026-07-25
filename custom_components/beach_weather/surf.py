from __future__ import annotations

from .const import (
    KEY_WEIGHT_SWELL_DIRECTION,
    KEY_WEIGHT_WATER_TEMPERATURE,
    KEY_WEIGHT_WAVE_HEIGHT,
    KEY_WEIGHT_WAVE_PERIOD,
    KEY_WEIGHT_WIND_DIRECTION,
    KEY_WEIGHT_WIND_SPEED,
)

# Bonus trigger thresholds — not user-configurable, part of the scoring model.
_OFFSHORE_WIND_DIFF_MIN = 120.0  # wind direction diff > this = blowing offshore
_FRONTAL_SWELL_DIFF_MAX = 15.0  # swell direction diff <= this = hits the beach head-on
_LONG_PERIOD_MIN = 10.0
_SIZABLE_HEIGHT_MIN = 0.8
_BONUS_POINTS = 10.0


def angular_diff(a: float, b: float) -> float:
    """Smallest angle (0-180°) between two compass directions."""
    d = abs(a - b) % 360
    return d if d <= 180 else 360 - d


def score_wave_period(period: float) -> float:
    if period < 4:
        return 0
    if period < 6:
        return 25
    if period < 8:
        return 50
    if period < 10:
        return 75
    if period <= 14:
        return 100
    return 90


def score_wave_height(height: float) -> float:
    if height < 0.3:
        return 0
    if height < 0.5:
        return 30
    if height < 0.8:
        return 60
    if height <= 1.5:
        return 100
    if height <= 2.0:
        return 80
    return 60


def score_wind_speed(speed_kmh: float) -> float:
    if speed_kmh <= 10:
        return 100
    if speed_kmh <= 20:
        return 80
    if speed_kmh <= 30:
        return 50
    if speed_kmh <= 40:
        return 20
    return 0


def score_direction_diff(diff: float) -> float:
    """Used for both swell and wind direction, against the beach orientation."""
    if diff <= 15:
        return 100
    if diff <= 30:
        return 90
    if diff <= 45:
        return 80
    if diff <= 60:
        return 70
    if diff <= 90:
        return 50
    if diff <= 120:
        return 30
    return 0


def score_water_temperature(temp: float) -> float:
    if temp < 16:
        return 0
    if temp < 18:
        return 30
    if temp < 20:
        return 60
    if temp <= 24:
        return 100
    return 90


def surf_condition_for_score(score: float) -> str:
    if score <= 20:
        return "no_surf"
    if score <= 40:
        return "poor"
    if score <= 60:
        return "okay"
    if score <= 80:
        return "good"
    if score <= 90:
        return "very_good"
    return "perfect"


def surf_stars_for_score(score: float) -> int:
    if score <= 20:
        return 1
    if score <= 40:
        return 2
    if score <= 60:
        return 3
    if score <= 80:
        return 4
    return 5


def calculate_surf_score(
    *,
    wave_period: float,
    wave_height: float,
    swell_direction: float,
    wind_direction: float,
    wind_speed: float,
    water_temperature: float,
    beach_orientation: float,
    weights: dict[str, float],
) -> float:
    swell_diff = angular_diff(swell_direction, beach_orientation)
    wind_diff = angular_diff(wind_direction, beach_orientation)

    scores = {
        KEY_WEIGHT_WAVE_PERIOD: score_wave_period(wave_period),
        KEY_WEIGHT_WAVE_HEIGHT: score_wave_height(wave_height),
        KEY_WEIGHT_SWELL_DIRECTION: score_direction_diff(swell_diff),
        KEY_WEIGHT_WIND_DIRECTION: score_direction_diff(wind_diff),
        KEY_WEIGHT_WIND_SPEED: score_wind_speed(wind_speed),
        KEY_WEIGHT_WATER_TEMPERATURE: score_water_temperature(water_temperature),
    }

    total_weight = sum(weights.get(key, 0) for key in scores) or 1
    weighted_avg = sum(scores[key] * weights.get(key, 0) for key in scores) / total_weight

    bonus = 0.0
    if swell_diff <= _FRONTAL_SWELL_DIFF_MAX and wind_diff > _OFFSHORE_WIND_DIFF_MIN:
        bonus += _BONUS_POINTS
    if wave_period > _LONG_PERIOD_MIN and wave_height > _SIZABLE_HEIGHT_MIN:
        bonus += _BONUS_POINTS

    return min(100.0, weighted_avg + bonus)
