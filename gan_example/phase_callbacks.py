import copy
from typing import Dict, List  # isort:skip
from collections import OrderedDict

from catalyst.core import _State, Callback, CallbackNode, CallbackOrder
from catalyst.dl.callbacks import PhaseManagerCallback
from catalyst.dl import registry


# TODO: remove copy-paste from catalyst.dl.callback.phase
class Phase:
    """
    Class for storing information about certain phase, including
    - phase name
    - number of steps (batches) in phase before next phase is chosen
    - how many steps (batches) are done already
    """
    def __init__(self, name: str = None, steps: int = None,
                 batch_metric_key: str = None,
                 threshold: float = None,
                 greater_is_good: bool = None):
        self.steps = int(steps) if steps is not None else None
        self.curr_step = 0
        self.name = name

        self.batch_metric_key = batch_metric_key
        self.threshold = threshold
        self.greater_is_good = greater_is_good

    def step(self, state: _State):
        metric_value = state.prev_batch_metrics.get(self.batch_metric_key, None)
        if metric_value is None:
            return False
        metric_value = abs(metric_value)  # todo: remove this hack
        is_greater = metric_value > self.threshold
        do_step = (not is_greater) and (not self.greater_is_good)
        do_step = do_step or (is_greater and self.greater_is_good)
        if do_step:
            self.curr_step = (self.curr_step + 1) % self.steps
            return self.curr_step == 0
        else:
            return False


# TODO: remove copy-paste from catalyst.dl.callback.phase
class PhaseManager:
    """
    Class for storing & managing all phases in experiment configuration

    Stores separately current phases in train & validation modes

    By calling `.step(...)` method current phase is updated by step-size
    and if current phase is finished, the next phase becomes current
    """
    def __init__(self, train_phases: List[Phase], valid_phases: List[Phase]):
        self.train_phases = train_phases
        self.valid_phases = valid_phases

        self.train_index = 0
        self.valid_index = 0

    def step(self, state: _State, step_size: int = 1):
        assert step_size == 1
        if state.need_backward_pass:
            if len(self.train_phases) > 1:
                need_change_phase = self.train_phases[self.train_index].step(state)
                if need_change_phase:
                    self.train_index = \
                        (self.train_index + 1) % len(self.train_phases)
        else:
            if len(self.valid_phases) > 1:
                need_change_phase = self.valid_phases[self.valid_index].step(state)
                if need_change_phase:
                    self.valid_index = \
                        (self.valid_index + 1) % len(self.valid_phases)

    def get_phase_name(self, state: _State):
        if state.need_backward_pass:
            return self.train_phases[self.train_index].name
        return self.valid_phases[self.valid_index].name


@registry.Callback
class SmartPhaseManagerCallback(PhaseManagerCallback):

    def _get_phase_manager(
            self,
            train_phases: "OrderedDict[str, Dict]" = None,
            valid_phases: "OrderedDict[str, Dict]" = None,
            valid_mode: str = None
    ):
        assert (valid_phases is None) ^ (valid_mode is None), \
            "Exactly one of them must be specified"

        if train_phases is None:
            train_phases = [Phase(name=None, steps=None)]
        else:
            train_phases = [
                Phase(name=name, **params)
                for name, params in train_phases.items()
            ]

        if valid_phases is None:
            if valid_mode == self.VALIDATION_MODE_ALL:
                valid_phases = [Phase(name=None, steps=None)]
            elif valid_mode == self.VALIDATION_MODE_SAME:
                valid_phases = copy.deepcopy(train_phases)
            else:
                raise ValueError(
                    f"Unsupported validation_mode, should be one of "
                    f"{self.allowed_valid_modes}"
                )

        return PhaseManager(
            train_phases=train_phases, valid_phases=valid_phases
        )

    def on_batch_start(self, state: _State):
        super().on_batch_start(state)

    def on_batch_end(self, state: _State):
        super().on_batch_end(state)