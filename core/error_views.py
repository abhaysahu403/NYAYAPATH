from django.http import JsonResponse


def json_404(request, exception=None):
    return JsonResponse({"success": False, "error": {"code": "NOT_FOUND", "message": "The requested resource could not be found."}}, status=404)


def json_500(request):
    return JsonResponse({"success": False, "error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."}}, status=500)
