from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from .models import Like


class LikeSerializer(serializers.ModelSerializer):
    model = None  # Simply change this model name to Your required model to inherit all of this functionality

    class Meta:
        model = Like
        fields = ["id", "object_id"]

    def save(self, **kwargs):
        if self.model is None or self.model == "":
            raise serializers.ValidationError({"error": "No model_name was specified"})

        content_type = ContentType.objects.get_for_model(self.model)
        user_id = self.context.get("user_id")

        try:
            obj = self.model.objects.get(uid=self.validated_data["object_id"])
        except self.model.DoesNotExist:
            raise serializers.ValidationError(
                {"error": f"{self.model.__name__} does not exist"}
            )

        if like := Like.objects.filter(
            user_id=user_id, object_id=obj.pk, content_type=content_type
        ):
            like.delete()
            return None
        self.instance = Like.objects.create(
            user_id=user_id,
            content_type=content_type,
            content_object=obj,
            **self.validated_data,
        )

        return self.instance
