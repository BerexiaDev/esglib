from flask import g
from esg_lib.auth.user import User


class AuthHelper:
    @staticmethod
    def get_logged_in_user():
        user_email = g.decoded_token['preferred_username'].lower()
        if not isinstance(user_email, str):
            return {"status": "fail", "message": "No email found"}, 400
        
        user = User().db().find_one({'email': user_email})
        
        if not user:
            return {"status": "fail", "message": "No such user with the provided email"}, 404

        g.auth_user = {**user, "principal_email": user.email if user.is_principal else  user.principal_email}
        return user, 200
