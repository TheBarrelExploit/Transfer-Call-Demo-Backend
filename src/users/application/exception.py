class UserException(Exception):
    """Base class for user-related exceptions."""

    pass


class UserNotFoundException(UserException):
    pass


class InvalidPasswordException(UserException):
    pass


class EmailAlreadyExistsException(UserException):
    pass


class InvalidDataException(UserException):
    pass
