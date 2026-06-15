from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Единый обработчик исключений DRF.
    Обеспечивает приведение всех API-ошибки к единому формату ответа.
    """
    response = exception_handler(exc, context)

    if response is None:
        return response

    code = getattr(exc, "default_code", "error")

    detail = response.data.get("detail", None)

    response.data = {
        "code": code,
        "message": str(detail) if detail is not None else str(response.data),
        "status": response.status_code,
    }

    return response