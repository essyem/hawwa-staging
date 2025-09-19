from django.urls import path
from . import views

app_name = 'ai_buddy'

urlpatterns = [
    # Main views
    path('', views.AIBuddyHomeView.as_view(), name='home'),
    path('conversations/', views.ConversationListView.as_view(), name='conversation_list'),
    path('conversation/<uuid:conversation_id>/', views.ConversationDetailView.as_view(), name='conversation_detail'),
    path('wellness/', views.WellnessTrackingView.as_view(), name='wellness_tracking'),
    path('milestones/', views.MilestoneListView.as_view(), name='milestone_list'),
    path('recommendations/', views.CareRecommendationListView.as_view(), name='recommendation_list'),
    path('settings/', views.AIBuddyProfileView.as_view(), name='profile_settings'),
    
    # AI interaction endpoints
    path('api/start-conversation/', views.start_conversation, name='create_conversation'),
    path('api/send-message/<uuid:conversation_id>/', views.send_message, name='send_message'),
    path('api/ask-question/', views.ask_ai_question, name='ask_question'),
    path('api/get-insights/', views.get_personalized_insights, name='get_insights'),
    
    # Wellness and recommendations
    path('api/log-wellness/', views.log_wellness, name='log_wellness'),
    path('api/get-recommendations/', views.get_smart_recommendations, name='get_recommendations'),
    path('api/service-recommendations/', views.get_service_recommendations, name='service_recommendations'),
    
    # Other APIs
    path('api/conversations/', views.conversation_list_api, name='conversation_list_api'),
]