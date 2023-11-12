
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth import authenticate
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from sms_ir import SmsIr
from random import randint
from .models import User
from .serializer import UserSerializer

class UserViewSet(viewsets.ViewSet):
    """
    A viewset for handling user-related CRUD operations and additional functionalities.
    """

    def list(self, request):
        """
        List all users in the system.
        """
        queryset = User.objects.all()
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        """
        Create a new user. Requires OTP to be verified first.
        """
        if not request.data.get('is_otp_verified', False):
            return Response({'status': 'OTP not verified'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        """
        Retrieve details of a specific user by their primary key.
        """
        queryset = User.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    def update(self, request, pk=None):
        """
        Update details of a specific user by their primary key.
        """
        queryset = User.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """
        Delete a specific user by their primary key.
        """
        queryset = User.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['POST'])
    def generate_otp(self, request):
        """
        Generate a one-time password (OTP) for phone number verification.
        """
        user_data = request.data
        phone_number = user_data.get('phone_number')
        otp = str(randint(100000, 999999))

        cache.set(f"otp_{phone_number}", otp, timeout=90)
        cache.set(f"user_data_{phone_number}", user_data, timeout=90)

        api_key = settings.SMS_API_KEY
        linenumber = settings.SMS_LINENUMBER

        sms_ir = SmsIr(api_key, linenumber)
        sms_ir.send_sms(phone_number, f'Your OTP code is {otp}', linenumber)

        return Response({'status': 'OTP sent'})

    @action(detail=False, methods=['POST'])
    def verify_otp(self, request):
        """
        Verify the OTP received from the user.
        """
        signUpData = request.data.get('signUpData')

        if signUpData is None:
            return Response({'status': 'Invalid request'}, status=status.HTTP_400_BAD_REQUEST)

        phone_number = signUpData.get('phone_number')
        otp_received = request.data.get('otp')

        otp_stored = cache.get(f"otp_{phone_number}")
        user_data = cache.get(f"user_data_{phone_number}")

        if otp_stored == otp_received:
            user_data['is_otp_verified'] = True
            serializer = UserSerializer(data=user_data)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': 'OTP verified and user created'}, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({'status': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['POST'], url_path='change-password')
    def change_password(self, request):
        """
        Change the user's password.
        """
        username = request.data.get('username')
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        confirm_new_password = request.data.get('confirm_new_password')

        user = authenticate(username=username, password=current_password)

        if user is None:
            return Response({"error": "Invalid username or current password"}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_new_password:
            return Response({"error": "New passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({"success": "Password changed successfully"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'], url_path='sign-in')
    def sign_in(self, request):
        """
        Sign in a user.
        """
        username_or_email = request.data.get('username_or_email')
        password = request.data.get('password')
        user_type = request.data.get('user_type').upper()

        user = authenticate(username=username_or_email, password=password)
        if user is None:
            try:
                user = User.objects.get(email=username_or_email)
                user = authenticate(username=user.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is None:
            return Response({"error": "Invalid username/email or password"}, status=status.HTTP_400_BAD_REQUEST)

        if user.userType != user_type:
            return Response({"error": "Invalid user type"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"success": "Signed in successfully", "user": UserSerializer(user).data}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'])
    def set_phone_number(self, request, pk=None):
        """
        Update the phone number for a specific user.
        """
        user = get_object_or_404(User, pk=pk)
        phone_number = request.data.get('phone_number')
        if phone_number is not None:
            user.phone_number = phone_number
            user.save()
            return Response({'status': 'phone number set'})
        else:
            return Response({'status': 'phone number not provided'}, status=status.HTTP_400_BAD_REQUEST)
