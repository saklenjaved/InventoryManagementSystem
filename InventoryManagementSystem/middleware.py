from accounts.models import User


class AccountsUserMiddleware:
    """Attach the logged-in accounts.User (if any) to each request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        uid = request.session.get('accounts_user_id')
        request.accounts_user = (
            User.objects.filter(pk=uid).first() if uid else None
        )
        response = self.get_response(request)
        return response
