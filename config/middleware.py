from django.utils import translation


class APICorsMiddleware:
    """CORS ساده برای API — اگر قبلاً وجود داشته حفظ می‌شود."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Headers"] = (
            "Authorization, Content-Type, Accept, Origin, X-Requested-With"
        )
        response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        if request.method == "OPTIONS":
            response.status_code = 200
        return response


class ForcePersianMiddleware:
    """
    کل پروژه (به‌خصوص ادمین) همیشه فارسی باشد.
    مرورگر انگلیسی نباید زبان UI را عوض کند.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        translation.activate("fa")
        request.LANGUAGE_CODE = "fa"
        response = self.get_response(request)
        response.setdefault("Content-Language", "fa")
        translation.deactivate()
        return response
