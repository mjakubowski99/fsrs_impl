from datetime import datetime, timedelta, timezone
import math
from src.rating import Rating
from src.state import State

FSRS_DEFAULT_DECAY = 0.1542
DEFAULT_PARAMETERS = (
    0.212,
    1.2931,
    2.3065,
    8.2956,
    6.4133,
    0.8334,
    3.0194,
    0.001,
    1.8722,
    0.1666,
    0.796,
    1.4835,
    0.0614,
    0.2629,
    1.6483,
    0.6014,
    1.8729,
    0.5425,
    0.0912,
    0.0658,
    FSRS_DEFAULT_DECAY,
)

STABILITY_MIN = 0.001
LOWER_BOUNDS_PARAMETERS = (
    STABILITY_MIN,
    STABILITY_MIN,
    STABILITY_MIN,
    STABILITY_MIN,
    1.0,
    0.001,
    0.001,
    0.001,
    0.0,
    0.0,
    0.001,
    0.001,
    0.001,
    0.001,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    0.1,
)

INITIAL_STABILITY_MAX = 100.0
UPPER_BOUNDS_PARAMETERS = (
    INITIAL_STABILITY_MAX,
    INITIAL_STABILITY_MAX,
    INITIAL_STABILITY_MAX,
    INITIAL_STABILITY_MAX,
    10.0,
    4.0,
    4.0,
    0.75,
    4.5,
    0.8,
    3.5,
    5.0,
    0.25,
    0.9,
    4.0,
    1.0,
    6.0,
    2.0,
    2.0,
    0.8,
    0.8,
)

MIN_DIFFICULTY = 1.0
MAX_DIFFICULTY = 10.0

FUZZ_RANGES = [
    {
        "start": 2.5,
        "end": 7.0,
        "factor": 0.15,
    },
    {
        "start": 7.0,
        "end": 20.0,
        "factor": 0.1,
    },
    {
        "start": 20.0,
        "end": math.inf,
        "factor": 0.05,
    },
]

DESIRED_RETAINABILITY = 0.9
MAXIMUM_INTERVAL = 36500

class FsrsParams:
    is_pending: bool
    difficulty: float|None 
    stability: float|None 
    due: datetime 
    last_review: datetime|None
    reviews_count: int
    last_rating: Rating|None
    learning_steps: list
    relearning_steps: list
    step: int|None 
    state: State

    def __init__(
        self,
        state: State = State.LEARNING,
        step: int|None = None,
        stability: float|None = None,
        difficulty: float|None = None,
        due: datetime|None = None,
        last_review: datetime|None = None,
        reviews_count: int = 0,
        parameters: list[float] = DEFAULT_PARAMETERS,
        learning_steps: tuple[timedelta, ...] | list[timedelta] = (
            timedelta(minutes=1),
            timedelta(minutes=10),
        ),
        relearning_steps: tuple[timedelta, ...] | list[timedelta] = (
            timedelta(minutes=10),
        ),
        is_pending: bool = False,
        last_rating: Rating|None = None,
    ):
        self.state = state

        if self.state == State.LEARNING and step is None:
            step = 0
        self.step = step

        self.stability = stability
        self.difficulty = difficulty
        
        if due is None:
            due = datetime.now(timezone.utc)
        self.due = due
        self.last_review = last_review
        self.parameters = parameters
        self.reviews_count = 0
        self.learning_steps = learning_steps
        self.relearning_steps = relearning_steps
        self.last_rating = None
        self.is_pending = is_pending
        self.reviews_count = reviews_count
        self.last_rating = last_rating

    def __repr__(self):
        return f"FsrsParams(stability={self.stability}, difficulty={self.difficulty}, due={self.due}, last_review={self.last_review}, reviews_count={self.reviews_count}, last_rating={self.last_rating}, learning_steps={self.learning_steps}, relearning_steps={self.relearning_steps}, step={self.step}, state={self.state}, is_pending={self.is_pending})"

    def review(self, rating: Rating, review_datetime: datetime|None = None):
        if review_datetime is None:
            review_datetime = datetime.now(timezone.utc)

        time_since_last_review = (
            review_datetime - self.last_review
        ) if self.last_review else None
        days_since_last_review = time_since_last_review.days if time_since_last_review else None

        if self.state == State.LEARNING:
            next_interval = self._handle_learning(rating, review_datetime, days_since_last_review, time_since_last_review) 
        elif self.state == State.REVIEW:
            next_interval = self._handle_review(rating, review_datetime, days_since_last_review, time_since_last_review)
        elif self.state == State.RELEARNING:
            next_interval = self._handle_relearning(rating, review_datetime, days_since_last_review, time_since_last_review)
        else:
            raise ValueError(f"Invalid state: {self.state}")

        self.due = review_datetime + next_interval
        self.last_review = review_datetime
        self.reviews_count += 1

    def _handle_learning(self, rating: Rating, review_datetime: datetime, days_since_last_review: int|None, time_since_last_review: timedelta|None):
        assert self.step is not None

        if self.stability is None or self.difficulty is None:
            self.stability = initial_stability(rating, parameters=self.parameters)
            self.difficulty = initial_difficulty(rating, True, parameters=self.parameters)
        elif self._last_review_was_today(days_since_last_review, time_since_last_review):
            self.stability = short_term_stability(
                self.stability,
                rating,
                parameters=self.parameters
            )
            self.difficulty = next_difficulty(self.difficulty, rating, self.parameters)
        else:
            retrievability = get_card_retrievability(
                self.stability, 
                self.last_review,
                review_datetime,
                parameters=self.parameters
            )
            self.stability = next_stability(
                self.difficulty, 
                self.stability, 
                retrievability,
                rating, 
                parameters=self.parameters
            )
            self.difficulty = next_difficulty(self.difficulty, rating, self.parameters)

        if len(self.learning_steps) == 0 or (
            self.step >= len(self.learning_steps)
            and rating != Rating.VERY_HARD
        ):
            self.state = State.REVIEW
            self.step = None
            next_interval = self.calculate_next_interval(self.stability)
        else:
            if rating == Rating.VERY_HARD:
                self.step = 0
                next_interval = self.learning_steps[0]
            elif rating == Rating.HARD:
                if self.step == 0 and len(self.learning_steps) == 1:
                    next_interval = self.learning_steps[0] * 1.5
                elif self.step == 0 and len(self.learning_steps) >= 2:
                    next_interval = (self.learning_steps[0] + self.learning_steps[1]) / 2
                else:
                    next_interval = self.learning_steps[self.step]
            elif rating == Rating.GOOD:
                if self.step + 1 == len(self.learning_steps):
                    self.state = State.REVIEW 
                    self.step = None
                    next_interval = self.calculate_next_interval(self.stability)
                else:
                    self.step += 1 
                    next_interval = self.learning_steps[self.step]
            elif rating == Rating.EASY:
                self.state = State.REVIEW
                self.step = None 
                next_interval = self.calculate_next_interval(self.stability)

        return next_interval


    def _handle_review(self, rating: Rating, review_datetime: datetime, days_since_last_review: int|None, time_since_last_review: timedelta|None):
        assert self.stability is not None 
        assert self.difficulty is not None

        if self._last_review_was_today(days_since_last_review, time_since_last_review):
            self.stability = short_term_stability(
                stability=self.stability,
                rating=rating,
                parameters=self.parameters
            )
            self.difficulty = next_difficulty(self.difficulty, rating, self.parameters)
        else:
            retrievability = get_card_retrievability(
                self.stability, 
                self.last_review,
                review_datetime,
                parameters=self.parameters
            )
            self.stability = next_stability(
                difficulty=self.difficulty,
                stability=self.stability,
                retrievability=retrievability,
                rating=rating,
                parameters=self.parameters
            )
            self.difficulty = next_difficulty(self.difficulty, rating, self.parameters)

        if rating == Rating.VERY_HARD:
            if len(self.relearning_steps) == 0:
                next_interval = self.calculate_next_interval(self.stability)
            else:
                self.state = State.RELEARNING
                self.step = 0 
                next_interval = self.relearning_steps[0]
        else:
            next_interval = self.calculate_next_interval(self.stability)

        return next_interval

    def _handle_relearning(self, rating: Rating, review_datetime: datetime, days_since_last_review: int|None, time_since_last_review: timedelta|None):
        assert self.stability is not None
        assert self.difficulty is not None
        assert self.step is not None

        if self._last_review_was_today(days_since_last_review, time_since_last_review):
            self.stability = short_term_stability(
                stability=self.stability,
                rating=rating,
                parameters=self.parameters
            )
            self.difficulty = next_difficulty(
                difficulty=self.difficulty, 
                rating=rating,
                parameters=self.parameters
            )
        else:
            retrievability = get_card_retrievability(
                self.stability, 
                self.last_review,
                review_datetime,
                parameters=self.parameters
            )
            self.stability = next_stability(
                difficulty=self.difficulty,
                stability=self.stability,
                retrievability=retrievability,
                rating=rating,
                parameters=self.parameters
            )
            self.difficulty = next_difficulty(self.difficulty, rating, self.parameters)

        if len(self.relearning_steps) == 0 or (
            self.step >= len(self.relearning_steps)
            and rating != Rating.VERY_HARD
        ):
            self.state = State.REVIEW
            self.step = None
            next_interval = self.calculate_next_interval(self.stability)
        else:
            if rating == Rating.VERY_HARD:
                self.step = 0 
                next_interval = self.relearning_steps[0]
            elif rating == Rating.HARD:
                if self.step == 0 and len(self.relearning_steps) == 1:
                    next_interval = self.relearning_steps[0] * 1.5
                elif self.step == 0 and len(self.relearning_steps) >= 2:
                    next_interval = (self.relearning_steps[0] + self.relearning_steps[1]) / 2
                else:
                    next_interval = self.relearning_steps[self.step]
            elif rating == Rating.GOOD:
                if self.step + 1 == len(self.relearning_steps):
                    self.state = State.REVIEW
                    self.step = None
                    next_interval = self.calculate_next_interval(self.stability)
                else:
                    self.step += 1
                    next_interval = self.relearning_steps[self.step]
            elif rating == Rating.EASY:
                self.state = State.REVIEW
                self.step = None
                next_interval = self.calculate_next_interval(self.stability)

        return next_interval

    def _last_review_was_today(self, days_since_last_review: int|None, time_since_last_review: timedelta|None) -> bool:
        if time_since_last_review is None:
            return False
        return time_since_last_review.total_seconds() > 0 and days_since_last_review is not None and days_since_last_review < 1

    def calculate_next_interval(self, stability: float|None):
        next_i = get_next_interval(stability=stability, parameters=self.parameters)
        return timedelta(days=next_i)

    def activate_from_pending(self, current_datetime: datetime|None = None) -> None:
        """
        Convert a pending card back to normal schedule.
        
        Adjusts stability and difficulty based on how long the card was pending.
        Cards that were pending for a long time have lower actual retrievability,
        so we adjust parameters to reflect this reality without breaking the schedule.
        
        Args:
            current_datetime: Current datetime (defaults to now if None)
        """
        if not self.is_pending:
            return
        
        if current_datetime is None:
            current_datetime = datetime.now(timezone.utc)
        
        if self.last_review is None or self.stability is None or self.difficulty is None:
            self.is_pending = False
            return

        elapsed_time = current_datetime - self.last_review
        elapsed_days = max(0, elapsed_time.days)
        
        if elapsed_days == 0:
            self.is_pending = False
            return
        
        actual_retrievability = get_card_retrievability(
            stability=self.stability,
            last_review_datetime=self.last_review,
            current_datetime=current_datetime,
            parameters=self.parameters
        )
        
        # If retrievability is very low (card was effectively forgotten),
        if actual_retrievability < 0.3:
            # Card was effectively forgotten, use forget stability adjustment
            self.stability = next_forget_stability(
                difficulty=self.difficulty,
                stability=self.stability,
                retrievability=actual_retrievability,
                parameters=self.parameters
            )
            # Slightly increase difficulty (forgotten cards are harder)
            difficulty_increase = min(0.5, elapsed_days * 0.01)  # Max 0.5 increase
            self.difficulty = clamp_difficulty(self.difficulty + difficulty_increase)
            
            if self.state == State.REVIEW and self.stability <= 3.0:
                if len(self.relearning_steps) > 0:
                    self.state = State.RELEARNING
                    self.step = 0
        else:
            # Card still has some retrievability, adjust stability more conservatively
            # Use a weighted adjustment: reduce stability proportionally to how much
            desired_retention = DESIRED_RETAINABILITY
            retention_loss = desired_retention - actual_retrievability
            
            if retention_loss > 0:
                stability_reduction_factor = 1.0 - (retention_loss * 0.3)  # Max 30% reduction
                self.stability = clamp_stability(self.stability * stability_reduction_factor)
                # Slightly increase difficulty (cards that weren't reviewed on time are harder)
                difficulty_increase = min(0.2, retention_loss * 0.5)
                self.difficulty = clamp_difficulty(self.difficulty + difficulty_increase)
        
        self.due = current_datetime
        self.is_pending = False


def clamp_difficulty(difficulty: float) -> float:
    return min(max(difficulty, MIN_DIFFICULTY), MAX_DIFFICULTY)

def clamp_stability(stability: float) -> float:
    return max(stability, STABILITY_MIN)

def initial_stability(rating: Rating, parameters: list[float] = DEFAULT_PARAMETERS) -> float:
    return clamp_stability(parameters[rating.value-1])

def initial_difficulty(
    rating: Rating, 
    clamp: bool, 
    parameters: list[float] = DEFAULT_PARAMETERS
) -> float:
    initial_difficulty = (
        parameters[4] - (math.e ** (parameters[5] * (rating.value-1))) + 1
    )

    return clamp_difficulty(initial_difficulty) if clamp else initial_difficulty

def get_next_interval(
    stability: float, 
    desired_retention: float = DESIRED_RETAINABILITY,
    maximum_interval: int = MAXIMUM_INTERVAL,
    parameters: list[float] = DEFAULT_PARAMETERS
) -> int:
    decay = -parameters[20]
    factor = 0.9 ** (1 / decay) - 1 

    next_interval = (stability / factor) * (
        (desired_retention ** (1 / decay)) - 1
    )

    next_interval = max(round(next_interval), 1)

    return min(next_interval, maximum_interval)

def short_term_stability(
    stability: float, 
    rating: Rating, 
    parameters: list[float] = DEFAULT_PARAMETERS
) -> float:
    short_term_stability_increase = (
        math.e ** (parameters[17] * (rating.value - 3 + parameters[18]))
    ) * (stability ** -parameters[19])

    if rating in (Rating.GOOD, Rating.EASY):
        short_term_stability_increase = max(short_term_stability_increase, 1.0)

    short_term_stability = stability * short_term_stability_increase

    return clamp_stability(stability=short_term_stability)

def next_difficulty(
    difficulty: float, 
    rating: Rating, 
    parameters: list[float] = DEFAULT_PARAMETERS
) -> float:
    def _linear_damping(*, delta_difficulty: float, difficulty: float) -> float:
        return (10.0 - difficulty) * delta_difficulty / 9.0

    def _mean_reversion(*, arg_1: float, arg_2: float) -> float:
        return parameters[7] * arg_1 + (1 - parameters[7]) * arg_2

    arg_1 = initial_difficulty(rating=Rating.EASY, clamp=False, parameters=parameters)

    delta_difficulty = -(parameters[6] * (rating.value - 3))
    arg_2 = difficulty + _linear_damping(
        delta_difficulty=delta_difficulty, difficulty=difficulty
    )

    next_difficulty = _mean_reversion(arg_1=arg_1, arg_2=arg_2)

    return clamp_difficulty(difficulty=next_difficulty)

def next_stability(
    difficulty: float,
    stability: float,
    retrievability: float,
    rating: Rating,
    parameters: list[float] = DEFAULT_PARAMETERS
) -> float:
    if rating == Rating.VERY_HARD:
        next_stability = next_forget_stability(
            difficulty=difficulty,
            stability=stability,
            retrievability=retrievability,
            parameters=parameters
        )
    else:
        next_stability = next_recall_stability(
            difficulty=difficulty,
            stability=stability,
            retrievability=retrievability,
            rating=rating,
            parameters=parameters
        )

    return clamp_stability(stability=next_stability)

def next_forget_stability(
    difficulty: float, 
    stability: float, 
    retrievability: float,
    parameters: list[float] = DEFAULT_PARAMETERS
) -> float:
    next_forget_stability_long_term_params = (
        parameters[11]
        * (difficulty ** -parameters[12])
        * (((stability + 1) ** (parameters[13])) - 1)
        * (math.e ** ((1 - retrievability) * parameters[14]))
    )

    next_forget_stability_short_term_params = stability / (
        math.e ** (parameters[17] * parameters[18])
    )

    return min(
        next_forget_stability_long_term_params,
        next_forget_stability_short_term_params,
    )

def next_recall_stability(
    difficulty: float,
    stability: float,
    retrievability: float,
    rating: Rating,
    parameters: list[float] = DEFAULT_PARAMETERS
) -> float:
    hard_penalty = parameters[15] if rating == Rating.HARD else 1
    easy_bonus = parameters[16] if rating == Rating.EASY else 1

    return stability * (
        1
        + (math.e ** (parameters[8]))
        * (11 - difficulty)
        * (stability ** -parameters[9])
        * ((math.e ** ((1 - retrievability) * parameters[10])) - 1)
        * hard_penalty
        * easy_bonus
    )

def get_card_retrievability(
    stability: float|None,
    last_review_datetime: datetime|None,
    current_datetime: datetime|None = None,
    parameters: list[float] = DEFAULT_PARAMETERS
) -> float:
    decay = -parameters[20]
    factor = 0.9 ** (1 / decay) - 1 

    if last_review_datetime is None or stability is None:
        return 0

    if current_datetime is None:
        current_datetime = datetime.now(timezone.utc)

    elapsed_days = max(0, (current_datetime - last_review_datetime).days)

    return (1 + factor * elapsed_days / stability) ** decay