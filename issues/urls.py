from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('user/', views.user_portal_view, name='user_portal'),
    path('user/track/', views.track_issue_view, name='track_issue'),
    path('developer/', views.developer_dashboard_view, name='developer_dashboard'),
    path('developer/issue/<int:id>/', views.issue_detail_view, name='issue_detail'),
    path('submit/', views.redirect_submit, name='redirect_submit'),
    path('issues/', views.redirect_issues, name='redirect_issues'),
    path('login/', views.role_login, name='login'),
    path('logout/', views.role_logout, name='logout'),
    path('signup/', views.role_signup, name='signup'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('developer/teams/', views.team_queue_view, name='team_queue'),
    path('developer/download/', views.download_issues_excel, name='download_issues_excel'),
    path('developer/download/csv/', views.download_issues_csv, name='download_issues_csv'),
    path('developer/issues/', views.all_issues_view, name='all_issues'),
    path('developer/next-issue/', views.next_issue, name='next_issue'),
    path('developer/search/', views.search_issues, name='search_issues'),
]
