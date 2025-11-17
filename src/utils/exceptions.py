class CrudException(Exception):
    pass


class CrudIntegrityError(CrudException):
    pass


class CrudUniqueValidationError(CrudIntegrityError):
    pass
