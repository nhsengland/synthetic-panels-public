import math
from statsmodels.stats.power import NormalIndPower, TTestIndPower
from statsmodels.stats.proportion import proportion_effectsize


class PowerAnalyzer:
    """
    Calculates the required sample size to achieve a target statistical power.

    Binary outcomes: two-sample proportion z-test (Cohen's h), equivalent to
    R's pwr.2p.test. Returns N per group.

    Continuous outcomes: independent-samples t-test (Cohen's d derived from
    mean_control, mean_treatment, and std_dev). Returns N per group.
    """

    def __init__(
        self,
        outcome_type: str,
        significance_level: float,
        target_power: float,
        p1: float = None,
        p2: float = None,
        mean_control: float = None,
        mean_treatment: float = None,
        std_dev: float = None,
    ):
        """
        Args:
            outcome_type: "binary" or "continuous"
            significance_level: Alpha level (e.g. 0.05)
            target_power: Desired power (e.g. 0.80)
            p1: Baseline YES proportion (binary only)
            p2: Minimum detectable YES proportion in at least one prompt (binary only)
            mean_control: Average for control group (continuous only)
            mean_treatment: Average for treatment group (continuous only)
            std_dev: Standard deviation of control group at baseline (continuous only)
        """
        self.outcome_type = outcome_type
        self.significance_level = significance_level
        self.target_power = target_power
        self.p1 = p1
        self.p2 = p2
        self.mean_control = mean_control
        self.mean_treatment = mean_treatment
        self.std_dev = std_dev

    def calculate_required_n(self) -> int:
        """
        Returns required N per group to achieve target power.
        """
        if self.outcome_type == "binary":
            h = proportion_effectsize(self.p1, self.p2)
            n = NormalIndPower().solve_power(
                effect_size=abs(h),
                alpha=self.significance_level,
                power=self.target_power,
            )
            return math.ceil(n)

        elif self.outcome_type == "continuous":
            d = (self.mean_treatment - self.mean_control) / self.std_dev
            n = TTestIndPower().solve_power(
                effect_size=abs(d),
                alpha=self.significance_level,
                power=self.target_power,
            )
            return math.ceil(n)

        else:
            raise ValueError(
                f"Unknown outcome_type: {self.outcome_type!r}. Use 'binary' or 'continuous'."
            )
import math
from statsmodels.stats.power import NormalIndPower, TTestIndPower
from statsmodels.stats.proportion import proportion_effectsize


class PowerAnalyzer:
    """
    Calculates the required sample size to achieve a target statistical power.

    Binary outcomes: two-sample proportion z-test (Cohen's h), equivalent to
    R's pwr.2p.test. Returns N per group.

    Continuous outcomes: independent-samples t-test (Cohen's d derived from
    mean_control, mean_treatment, and std_dev). Returns N per group.
    """

    def __init__(
        self,
        outcome_type: str,
        significance_level: float,
        target_power: float,
        p1: float = None,
        p2: float = None,
        mean_control: float = None,
        mean_treatment: float = None,
        std_dev: float = None,
    ):
        """
        Args:
            outcome_type: "binary" or "continuous"
            significance_level: Alpha level (e.g. 0.05)
            target_power: Desired power (e.g. 0.80)
            p1: Baseline YES proportion (binary only)
            p2: Minimum detectable YES proportion in at least one prompt (binary only)
            mean_control: Average for control group (continuous only)
            mean_treatment: Average for treatment group (continuous only)
            std_dev: Standard deviation of control group at baseline (continuous only)
        """
        self.outcome_type = outcome_type
        self.significance_level = significance_level
        self.target_power = target_power
        self.p1 = p1
        self.p2 = p2
        self.mean_control = mean_control
        self.mean_treatment = mean_treatment
        self.std_dev = std_dev

    def calculate_required_n(self) -> int:
        """
        Returns required N per group to achieve target power.
        """
        if self.outcome_type == "binary":
            h = proportion_effectsize(self.p1, self.p2)
            n = NormalIndPower().solve_power(
                effect_size=abs(h),
                alpha=self.significance_level,
                power=self.target_power,
            )
            return math.ceil(n)

        elif self.outcome_type == "continuous":
            d = (self.mean_treatment - self.mean_control) / self.std_dev
            n = TTestIndPower().solve_power(
                effect_size=abs(d),
                alpha=self.significance_level,
                power=self.target_power,
            )
            return math.ceil(n)

        else:
            raise ValueError(
                f"Unknown outcome_type: {self.outcome_type!r}. Use 'binary' or 'continuous'."
            )
