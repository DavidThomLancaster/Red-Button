# TODO - login, get_user_id_from_token, validate_token, self.compare_passwords

from Repositories.UserRepository import UserRepository
from Services.TokenService import TokenService
from Utils import AuthUtils

repo = UserRepository()

# -------------------------- THIS HAS BEEN MOVED TO UserService ------------------------- # 

class AuthService:
    @staticmethod
    def login(email, password):
        pass
        # TODO
        # # calls UserRepository.get_password_by_email(email)
        # hashed_password = repo.find_by_email(email). # TODO make sure to get the password...
        # # calls Utils.COMPARE(password, hashed_password)
        # if AuthUtils.verify_password(password, hashed_password):

        #     # if it's good calls TokenService.create_token(email)
        #     token = TokenService.create_token(x)
        #     return token
        # else:
        #     return error
        # # returns the token. 


    @staticmethod
    def get_user_id_from_token(token):
        pass
        # TODO...

    @staticmethod
    def validate_token(token):
        pass
        # TODO...

    # # TODO (?) should this be staticmethod if it's listed as .self?
    # # TODO (?) Should this actually be moved to AuthUtils???
    # @staticmethod
    # def compare_passwords(password, stored_password):
    #     pass
    #     # TODO...