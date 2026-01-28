from aiogram.fsm.state import State, StatesGroup


class KeywordStates(StatesGroup):
    add = State()
    delete = State()
    import_list = State()


class SourceStates(StatesGroup):
    add = State()
    delete = State()


class SettingStates(StatesGroup):
    custom_poll_interval = State()
    custom_min_score = State()
    custom_max_results = State()
    set_channel_id = State()


class LeadStates(StatesGroup):
    add_neg_keyword = State()
