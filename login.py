from pytcs_tecnoalarm import TCSSession
from pytcs_tecnoalarm.exceptions import OTPException
from getpass import getpass

def get_credentials():
    email = input("Enter your email: ")
    password = getpass("Enter your password: ")
    return email, password

def main():
    email, password = get_credentials()
    session = TCSSession()

    try:
        session.login(email, password)
    except OTPException:
        print("\nOTP required for this account.")
        otp = input("Please enter your OTP (received via mail): ").strip()
        session.login(email, password, otp)

    # Print session details after successful login
    print("\nLogin successful!")
    print(f"#Token:")
    print(f"SESSION_KEY={session.token}")
    print(f"#App ID:")
    print(f"APPID{session.appid}")

    return session

if __name__ == "__main__":
    main()