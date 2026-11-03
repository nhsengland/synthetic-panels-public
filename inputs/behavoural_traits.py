# Some of this could be replaced with real cencus data.
#
# Each trait has an "include" default toggle and a "weights" distribution. The app
# (Study Setup page) and the CLI both read this: "include" seeds the on/off toggle,
# "weights" seeds the editable distribution.

# NOTE: If adding new dimensions, please make the description match the form:
# "You {description}," - this is how the description is injected into the prompt. 

behavioural_dimensions = {
    "health_literacy": {
        "include": True,
        "weights": {
            "are comfortable reading health information, including doses and percentages": 0.39,
            "can follow written information, but find numbers and percentages hard going": 0.18,
            "find written health information hard to follow, and usually need someone to explain it": 0.43,
        },
    },

    "trust_in_healthcare": {
        "include": True,
        "weights": {
            "trust the healthcare system completely, and assume it is acting in your interest": 0.04,
            "generally trust the healthcare system, with the odd frustration": 0.22,
            "have mixed feelings about the healthcare system, neither confident nor especially critical": 0.23,
            "are frustrated with how the healthcare system is run, though you still trust doctors and nurses themselves": 0.33,
            "distrust the healthcare system, and suspect its decisions are made to save money": 0.18,
        },
    },

    "digital_literacy": {
        "include": True,
        "weights": {
            "are rarely online, and rely on a family member to deal with anything digital": 0.10,
            "can get online, but find unfamiliar sites and sign-up forms offputting": 0.16,
            "manage most things online, and get stuck occasionally": 0.32,
            "use apps and online services confidently, without help": 0.28,
            "are very comfortable online, and often set things up for other people": 0.14,
        },
    },

    "health_engagement": {
        "include": True,
        "weights": {
            "take charge of your own health, and chase things up without being asked": 0.20,
            "manage your health reasonably well, but do not go looking for extra involvement": 0.35,
            "engage when prompted, but do not feel confident directing your own care": 0.25,
            "feel your health is largely out of your hands, and leave it to the professionals": 0.20,
        },
    },

    "response_to_authority": {
        "include": True,
        "weights": {
            "take official advice at face value, and tend to act on it": 0.10,
            "are mildly irritated by being told what to do, but go along with it": 0.22,
            "dislike being pushed, and notice when a message is trying to steer you": 0.36,
            "resent being pressured, and tend to push back against it": 0.22,
            "react strongly against anything that feels like being managed or guilt-tripped": 0.10,
        },
    },

    "prosocial_orientation": {
        "include": True,
        "weights": {
            "weigh your own needs first, and are unmoved by appeals about other people": 0.08,
            "will help others when it costs you little": 0.20,
            "are reasonably considerate of others, without going out of your way": 0.34,
            "are genuinely motivated by fairness, and by not taking more than your share": 0.26,
            "are strongly moved by the idea of helping someone else who is struggling": 0.12,
        },
    },
}


def get_behavioural_dimensions(dimensions: dict | None = None) -> dict:
    """Return {trait: weights} for every trait marked include=True.

    Args:
        dimensions: trait definitions to filter; defaults to the module-level
            ``behavioural_dimensions``.
    """
    if dimensions is None:
        dimensions = behavioural_dimensions
    return {
        name: spec["weights"]
        for name, spec in dimensions.items()
        if spec.get("include", True)
    }
