from rest_framework import serializers
from .models import Book


class BookSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(
        read_only=True)  # Show username instead of ID
    cover_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id', 'owner', 'title', 'author', 'isbn', 'description',
            'genre', 'condition', 'daily_rental_price', 'cover_image',
            'cover_image_url', 'is_available', 'location', 'created_at'
        ]
        read_only_fields = ['owner', 'created_at', 'cover_image_url']

    def get_cover_image_url(self, obj):
        if obj.cover_image:
            return obj.cover_image.url
        return None

    def validate_daily_rental_price(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Rental price cannot be negative.")
        if value > 1000:
            raise serializers.ValidationError("Rental price seems too high.")
        return value

    def create(self, validated_data):
        # Set the owner to the current user
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)
