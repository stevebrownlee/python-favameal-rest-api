"""View module for handling requests about restaurants"""
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.http import HttpResponseServerError
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from favamealapi.models import Restaurant
from favamealapi.models.favoriterestaurant import FavoriteRestaurant


class RestaurantSerializer(serializers.ModelSerializer):
    """JSON serializer for restaurants"""

    class Meta:
        model = Restaurant
        fields = ('id', 'name', 'address', 'favorite',)

class FaveSerializer(serializers.ModelSerializer):
    """JSON serializer for favorites"""

    class Meta:
        model = FavoriteRestaurant
        fields = ('restaurant',)
        depth = 1


class RestaurantView(ViewSet):
    """ViewSet for handling restuarant requests"""

    def create(self, request):
        """Handle POST operations for restaurants

        Returns:
            Response -- JSON serialized event instance
        """
        rest = Restaurant()
        rest.name = request.data["name"]
        rest.address = request.data["address"]

        try:
            rest.save()
            serializer = RestaurantSerializer(
                rest, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as ex:
            return Response({"reason": ex.message}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        """Handle GET requests for single event

        Returns:
            Response -- JSON serialized game instance
        """
        try:
            rest = Restaurant.objects.get(pk=pk)
            serializer = RestaurantSerializer(
                rest, context={'request': request})
            return Response(serializer.data)
        except Exception as ex:
            return HttpResponseServerError(ex)

    def list(self, request):
        """Handle GET requests to restaurants resource

        Returns:
            Response -- JSON serialized list of restaurants
        """
        # restaurants = Restaurant.objects.all()
        restaurants = Restaurant.objects.annotate(
            is_favorite=Count(
                'userfavoriterestaurants',
                filter=Q(userfavoriterestaurants__user=request.auth.user)
            )
        )
        for rest in restaurants:
            rest.favorite = bool(rest.is_favorite)

        serializer = RestaurantSerializer(restaurants, many=True, context={'request': request})

        return Response(serializer.data)

    @action(methods=['post', 'delete'], detail=True)
    def star(self, request, pk):
        """Managing favorites for restaurants"""

        if request.method == "POST":
            restaurant = Restaurant.objects.get(pk=pk)

            try:
                FavoriteRestaurant.objects.get(
                    restaurant=restaurant, user=request.auth.user)

                return Response(
                    {'message': 'Retaurant has already been favorited.'},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY
                )
            except FavoriteRestaurant.DoesNotExist:
                fave = FavoriteRestaurant()
                fave.restaurant = restaurant
                fave.user = request.auth.user
                fave.save()

                return Response({}, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            try:
                rest = Restaurant.objects.get(pk=pk)
            except Restaurant.DoesNotExist:
                return Response(
                    {'message': 'Restaurant does not exist.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                fave = FavoriteRestaurant.objects.get(
                    restaurant=rest, user=request.auth.user)
                fave.delete()
                return Response({}, status=status.HTTP_204_NO_CONTENT)

            except FavoriteRestaurant.DoesNotExist:
                return Response(
                    {'message': 'Not currently a favorite restaurant.'},
                    status=status.HTTP_404_NOT_FOUND
                )

        return Response({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

