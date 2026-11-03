import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from src.power_analyzer import PowerAnalyzer


def make_binary(p1, p2, significance_level=0.05, target_power=0.80):
    return PowerAnalyzer(
        outcome_type="binary",
        significance_level=significance_level,
        target_power=target_power,
        p1=p1,
        p2=p2,
    )


def make_continuous(mean_control, mean_treatment, std_dev, significance_level=0.05, target_power=0.80):
    return PowerAnalyzer(
        outcome_type="continuous",
        significance_level=significance_level,
        target_power=target_power,
        mean_control=mean_control,
        mean_treatment=mean_treatment,
        std_dev=std_dev,
    )


class TestBinaryOutcome:
    def test_small_effect(self):
        # p1=0.3, p2=0.35, alpha=0.05, power=0.80 → N=1376
        analyzer = make_binary(p1=0.3, p2=0.35)
        assert analyzer.calculate_required_n() == 1376

    def test_unknown_outcome_type_raises(self):
        analyzer = PowerAnalyzer(
            outcome_type="ordinal",
            significance_level=0.05,
            target_power=0.80,
        )
        with pytest.raises(ValueError, match="Unknown outcome_type"):
            analyzer.calculate_required_n()


class TestContinuousOutcome:
    def test_small_effect(self):
        # mean_control=20, mean_treatment=25, std_dev=120 → d≈0.042
        # alpha=0.05, power=0.80 → N=9043
        analyzer = make_continuous(mean_control=20, mean_treatment=25, std_dev=120)
        assert analyzer.calculate_required_n() == 9043
