from django.db import models


class Meal(models.Model):

    name = models.CharField(max_length=55)
    restaurant = models.ForeignKey("Restaurant", on_delete=models.CASCADE)

    @property
    def user_rating(self):
        return self.__user_rating

    @user_rating.setter
    def user_rating(self, value):
        self.__user_rating = value

    @property
    def avg_rating(self):
        return self.__avg_rating

    @avg_rating.setter
    def avg_rating(self, value):
        self.__avg_rating = value
