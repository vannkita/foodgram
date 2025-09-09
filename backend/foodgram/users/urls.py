from django.urls import path

from .views import CustomAuthToken, UsersViewSet

urlpatterns = [
    path(
        '',
        UsersViewSet.as_view({'post': 'create'}),
        name='user-create'
    ),
    path(
        'me/',
        UsersViewSet.as_view({'get': 'me'}),
        name='user-me'
    ),
    path(
        'me/avatar/',
        UsersViewSet.as_view({'put': 'me_avatar'}),
        name='user-me-avatar'
    ),
    path(
        'auth/token/login/',
        CustomAuthToken.as_view(),
        name='token-login'
    ),
    path(
        '<int:id>/',
        UsersViewSet.as_view({'get': 'retrieve'}),
        name='user-detail'
    ),
    path(
        '<int:id>/subscribe/',
        UsersViewSet.as_view({'post': 'subscribe', 'delete': 'unsubscribe'}),
        name='user-subscribe'
    ),
    path(
        'subscriptions/',
        UsersViewSet.as_view({'get': 'subscriptions'}),
        name='user-subscriptions'
    ),
]
