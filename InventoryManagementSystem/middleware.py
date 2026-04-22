from accounts.models import User


class AccountsUserMiddleware:
    """Attach the logged-in accounts.User (if any) to each request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):                            # __call__ runs on each request
        uid = request.session.get('accounts_user_id')               # get user_if from stored in session
        request.accounts_user = (
            User.objects.filter(pk=uid).first() if uid else None            # if user_id is there fetch user from DB else None
        )
        response = self.get_response(request)               # now request goes next middleware - views - response
        return response                                 
