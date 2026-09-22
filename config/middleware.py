from django.http import HttpResponse
from django.utils import translation


class APICorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # OPTIONS را بدون authentication جواب بده
        if request.method == "OPTIONS":
            response = HttpResponse()
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            )
            response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            response["Access-Control-Max-Age"] = "86400"
            return response

        response = self.get_response(request)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = (
            "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        )
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response


class ForcePersianMiddleware:
    """کل UI (ادمین) همیشه فارسی — وابسته به زبان مرورگر نباشد."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        translation.activate("fa")
        request.LANGUAGE_CODE = "fa"
        response = self.get_response(request)
        response["Content-Language"] = "fa"
        return response
