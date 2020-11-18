"""View module for handling requests about meals"""
from django.core.exceptions import ValidationError
from django.http import HttpResponseServerError
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers
from favamealapi.models import Meal, MealRating, Restaurant, FavoriteMeal
from favamealapi.views.restaurant import RestaurantSerializer


class MealSerializer(serializers.ModelSerializer):
    """JSON serializer for meals"""
    restaurant = RestaurantSerializer(many=False)

    class Meta:
        model = Meal
        fields = ('id', 'name', 'restaurant')


class MealView(ViewSet):
    """ViewSet for handling meal requests"""

    def create(self, request):
        """Handle POST operations for meals

        Returns:
            Response -- JSON serialized meal instance
        """
        meal = Meal()
        meal.name = request.data["name"]
        meal.restaurant = Restaurant.objects.get(pk=request.data["restaurant_id"])


        try:
            meal.save()
            serializer = MealSerializer(
                meal, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as ex:
            return Response({"reason": ex.message}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        """Handle GET requests for single meal

        Returns:
            Response -- JSON serialized meal instance
        """
        try:
            meal = Meal.objects.get(pk=pk)
            serializer = RestaurantSerializer(
                meal, context={'request': request})
            return Response(serializer.data)
        except Exception as ex:
            return HttpResponseServerError(ex)

    def list(self, request):
        """Handle GET requests to meals resource

        Returns:
            Response -- JSON serialized list of meals
        """
        meals = Meal.objects.all()

        serializer = MealSerializer(
            meals, many=True, context={'request': request})

        return Response(serializer.data)

    @action(methods=['post', 'put'], detail=True)
    def rate(self, request, pk):
        """Managing rating for meals"""

        user = request.auth.user

        if request.method == "POST":
            meal = Meal.objects.get(pk=pk)

            try:
                MealRating.objects.get(meal=meal, user=user)

                return Response(
                    {'message': 'This meal already has a rating. Send a PUT request to modify it.'},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY
                )
            except MealRating.DoesNotExist:
                rating = MealRating()
                rating.meal = meal
                rating.user = user
                rating.rating = request.data["rating"]
                rating.save()

                return Response({}, status=status.HTTP_201_CREATED)

    @action(methods=['post', 'delete'], detail=True)
    def star(self, request, pk):
        """Managing favorites for meals"""

        user = request.auth.user

        if request.method == "POST":
            meal = Meal.objects.get(pk=pk)

            try:
                FavoriteMeal.objects.get(meal=meal, user=user)

                return Response(
                    {'message': 'This meal already a favorite.'},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY
                )
            except FavoriteMeal.DoesNotExist:
                favorite = FavoriteMeal()
                favorite.meal = meal
                favorite.user = user
                favorite.save()

                return Response({}, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            try:
                meal = Meal.objects.get(pk=pk)
            except Meal.DoesNotExist:
                return Response(
                    {'message': 'Meal does not exist.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                fave = FavoriteMeal.objects.get(
                    meal=meal, user=user)
                fave.delete()
                return Response({}, status=status.HTTP_204_NO_CONTENT)

            except FavoriteMeal.DoesNotExist:
                return Response(
                    {'message': 'Not a current favorite meal.'},
                    status=status.HTTP_404_NOT_FOUND
                )

        return Response({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
