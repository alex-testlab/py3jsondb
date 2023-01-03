class InvalidEntryID(ValueError):
    """ EntryID is invalid """


class DatabaseNotCommitted(FileNotFoundError):
    """ Database has not been saved in yet """


class SessionError(RuntimeError):
    """ Could not commit database"""


class MatchError(ValueError):
    """ could not match an item in db """

class TableNotFound(FileNotFoundError):
    """ Table has not been created yet """

class TableCanNotBeEmpty(ValueError):
    """ Table can not be empty """

class ChildNotFound(FileNotFoundError):
    """ Child has not been created yet """