from rest_framework import generics
from .models import SportCategory, Sport, Gym, GymPrice
from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from math import radians, sin, cos, sqrt, atan2

class SportCategoryListView(generics.ListAPIView):
    queryset = SportCategory.objects.all()
    serializer_class = SportCategorySerializer


class SportListView(generics.ListAPIView):
    queryset = Sport.objects.all()
    serializer_class = SportSerializer


class GymListView(generics.ListAPIView):
    queryset = Gym.objects.all()
    serializer_class = GymSerializer


class GymPriceListView(generics.ListAPIView):
    queryset = GymPrice.objects.all()
    serializer_class = GymPriceSerializer


class TopPopularGymsAPIView(APIView):
    def get(self, request):
        gyms = Gym.objects.filter(is_popular=True).order_by("-popularity_score")[:5]
        serializer = GymSerializer(gyms, many=True)
        return Response(serializer.data)
    


def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # km

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c


class NearbyGymsAPIView(APIView):
    def get(self, request):
        user_lat = float(request.query_params.get("lat"))
        user_lon = float(request.query_params.get("lon"))

        gyms = Gym.objects.all()

        sorted_gyms = sorted(
            gyms,
            key=lambda g: calculate_distance(user_lat, user_lon, g.latitude, g.longitude)
        )

        serializer = GymSerializer(sorted_gyms[:10], many=True)

        return Response(serializer.data)