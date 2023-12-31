from django.db import transaction
from django.http import Http404, HttpRequest
from django.http.request import HttpRequest
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from hitcount.models import HitCount
from hitcount.views import HitCountMixin
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from likes.views import LikeView
from users.models import Profile
from utils.exception_handlers import ErrorEnum, ErrorResponse
from utils.helpers import custom_cache_decorator

# from .filters import ApartmentFilter
from .models import Bookmark, Comment, Picture, Post, Video
from .pagination import PostPagination
from .serializers import (
    AddCommentSerializer,
    CommentSerializer,
    CreateBookmarkSerializer,
    CreatePostSerializer,
    LikeCommentSerializer,
    LikePostSerializer,
    PostSerializer,
)


class PostViewSet(ModelViewSet):
    queryset = Post.objects.all()
    lookup_field = "uid"
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    http_method_names = ["get", "post", "patch", "delete"]
    search_fields = ["content", "profile__user_id", "profile__username"]
    pagination_class = PostPagination

    @action(methods=["GET"], detail=False, pagination_class=PostPagination)
    @method_decorator(custom_cache_decorator)
    def mine(self, request):
        """
        Returns all the Posts owned by the currently logged in agent

        """
        profile = Profile.objects.get(user_id=request.user_id)

        posts = (
            Post.objects.filter(profile=profile)
            .prefetch_related("pictures", "videos")
            .select_related("profile")
        )

        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(posts, request)

        serializer = PostSerializer(result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    def get_queryset(self):
        return (
            Post.objects.all()
            .select_related("profile")
            .prefetch_related(
                "pictures",
                "videos",
                "comments",
                "profile__watching",
                "profile__watchers",
                "likes",
            )
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreatePostSerializer
        return PostSerializer

    @method_decorator(custom_cache_decorator) #? I need to create a new redis database instance on redis lab
    def list(self, request: HttpRequest, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def retrieve(self, request: HttpRequest, *args, **kwargs):
        # Do a hit count

        hit_count = HitCount.objects.get_for_object(self.get_object())

        HitCountMixin.hit_count(request, hit_count)

        return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        profile = get_object_or_404(Profile, user_id=request.user_id)
        serializer = CreatePostSerializer(data=request.data)

        if serializer.is_valid():
            # serializer.is_valid(raise_exception=True)
            with transaction.atomic():
                data = serializer.validated_data

                images = data.pop("pictures", [])
                videos = data.pop("videos", [])

                new_post = Post.objects.create(**data, profile=profile)

                if images:
                    pics = [Picture(image=img, post=new_post) for img in images]

                    Picture.objects.bulk_create(pics)

                if videos:
                    vids = [Video(clip=clip, post=new_post) for clip in videos]

                    Video.objects.bulk_create(vids)

                serializer = PostSerializer(new_post)

                return Response(serializer.data, status=status.HTTP_200_OK)

        return ErrorResponse(ErrorEnum.ERR_001, serializer_errors=serializer.errors)

    def destroy(self, request: HttpRequest, *args, **kwargs):
        full_path = request.get_full_path()
        post_id = full_path.split("/")[4]
        try:
            post = get_object_or_404(
                Post, uid=post_id, profile__user_id=request.user_id
            )
            post.delete()

            return Response(
                {"status": True, "message": "Post deleted"}, status=status.HTTP_200_OK
            )
        except Http404:
            return ErrorResponse(
                ErrorEnum.ERR_006,
                extra_detail="Post does not exist or you do not own this post",
            )


class LikePostView(LikeView):
    serializer_class = LikePostSerializer

    def post(self, request):
        super().post(request)

        message = "Post liked"
        if self.unlike:
            message = "Post removed like"

        product_instance = Post.objects.get(uid=request.data["post_id"])
        data = PostSerializer(product_instance).data
        return Response(
            {"status": True, "message": message, "result": data},
            status=status.HTTP_200_OK,
        )


class CommentViewSet(ModelViewSet):
    lookup_field = "uid"
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        post = get_object_or_404(Post, uid=self.kwargs["post_uid"])
        return Comment.objects.filter(post_id=post.id)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AddCommentSerializer
        return CommentSerializer

    def create(self, request, *args, **kwargs):
        serializer = AddCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = get_object_or_404(Profile, user_id=request.user_id)
        content = serializer.validated_data.get("content")
        post_uid = kwargs.get("post_uid")
        post = Post.objects.get(uid=post_uid)

        new_comment = Comment.objects.create(
            content=content, profile=profile, post=post
        )

        serializer = CommentSerializer(new_comment)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LikeCommentView(LikeView):
    serializer_class = LikeCommentSerializer

    def post(self, request):
        super().post(request)

        message = "Comment liked"
        if self.unlike:
            message = "Comment removed like"

        comment_instance = Comment.objects.get(uid=request.data["comment_id"])
        data = CommentSerializer(comment_instance).data
        return Response(
            {"status": True, "message": message, "result": data},
            status=status.HTTP_200_OK,
        )


class BookmarkView(APIView):
    serializer_class = CreateBookmarkSerializer

    def get(self, request):
        """
        Provides all the posts that have been saved by the currently logged in user
        """

        my_bookmark = Bookmark.objects.filter(user_id=request.user_id).values("post_id")

        _ids = [item["post_id"] for item in my_bookmark]

        posts = Post.objects.filter(id__in=_ids)

        serializer = PostSerializer(posts, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Add a post to bookmark or saved post
        """
        serializer = CreateBookmarkSerializer(data=request.data)

        if serializer.is_valid():
            post_id = serializer.validated_data.get("post_id")
            post = get_object_or_404(Post, id=post_id)

            Bookmark.objects.create(user_id=request.user_id, post=post)
            serializer = PostSerializer(post)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(ErrorResponse("Validation error", serializer.errors))

    def delete(self, request):
        """
        Delete selected bookmarks

        Example request body:

            {
                "post_ids" : [

                    "c0330839-f30c-4667-951c-2811e5e09bdf",

                    "d59a5194-2cab-4e1c-8642-d549f5c65b86"
                ]
            }

        """

        post_id_list = request.data["post_ids"]

        Bookmark.objects.filter(post_id__in=post_id_list).delete()

        return Response(
            {"detail": "bookmarks removed successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )
