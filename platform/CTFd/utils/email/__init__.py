from CTFd.constants.email import (
    DEFAULT_PASSWORD_CHANGE_ALERT_BODY,
    DEFAULT_PASSWORD_CHANGE_ALERT_SUBJECT,
    DEFAULT_PASSWORD_RESET_BODY,
    DEFAULT_PASSWORD_RESET_SUBJECT,
    DEFAULT_SUCCESSFUL_REGISTRATION_EMAIL_BODY,
    DEFAULT_SUCCESSFUL_REGISTRATION_EMAIL_SUBJECT,
    DEFAULT_USER_CREATION_EMAIL_BODY,
    DEFAULT_USER_CREATION_EMAIL_SUBJECT,
    DEFAULT_VERIFICATION_EMAIL_BODY,
    DEFAULT_VERIFICATION_EMAIL_SUBJECT,
)
def sendmail(addr, text, subject="Message from {ctf_name}"): return True
def password_change_alert(email): return True
def forgot_password(email): return True
def verify_email_address(addr): return True
def successful_registration_notification(addr): return True
def user_created_notification(addr, name, password): return True
def check_email_is_whitelisted(email_address): return True
def check_email_is_blacklisted(email_address): return False
